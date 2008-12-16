#
#    Uncomplicated VM Builder
#    Copyright (C) 2007-2008 Canonical Ltd.
#    
#    See AUTHORS for list of contributors
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Virtual disk management

import logging
import os.path
import re
import string
import tempfile
import VMBuilder
from   VMBuilder.util      import run_cmd 
from   VMBuilder.exception import VMBuilderUserError, VMBuilderException

TYPE_EXT2 = 0
TYPE_EXT3 = 1
TYPE_XFS = 2
TYPE_SWAP = 3

class Disk(object):
    def __init__(self, vm, size='5G', preallocated=False, filename=None):
        """
        @type  size: string or number
        @param size: The size of the disk image (passed to L{parse_size})

        @type  preallocated: boolean
        @param preallocated: if True, the disk image already exists and will not be created (useful for raw devices)

        @type  filename: string
        @param filename: force a certain filename or to give the name of the preallocated disk image
        """

        # We need this for "introspection"
        self.vm = vm

        # Perhaps this should be the frontend's responsibility?
        self.size = parse_size(size)

        self.preallocated = preallocated

        # If filename isn't given, make one up
        if filename:
            self.filename = filename
        else:
            if self.preallocated:
                raise VMBuilderException('Preallocated was set, but no filename given')
            self.filename = 'disk%d.img' % len(self.vm.disks)

        self.partitions = []

    def devletters(self):
        """
        @rtype: string
        @return: the series of letters that ought to correspond to the device inside
                 the VM. E.g. the first disk of a VM would return 'a', while the 702nd would return 'zz'
        """

        return index_to_devname(self.vm.disks.index(self))

    def create(self, directory):
        """
        Creates the disk image (unless preallocated), partitions it, creates the partition mapping devices and mkfs's the partitions

        @type  directory: string
        @param directory: If set, the disk image is created in this directory
        """

        if not self.preallocated:
            if directory:
                self.filename = '%s/%s' % (directory, self.filename)
            logging.info('Creating disk image: %s' % self.filename)
            run_cmd(qemu_img_path(), 'create', '-f', 'raw', self.filename, '%dM' % self.size)

        # From here, we assume that self.filename refers to whatever holds the disk image,
        # be it a file, a partition, logical volume, actual disk..

        logging.info('Adding partition table to disk image: %s' % self.filename)
        run_cmd('parted', '--script', self.filename, 'mklabel', 'msdos')

        # Partition the disk 
        for part in self.partitions:
            part.create(self)

        logging.info('Creating loop devices corresponding to the created partitions')
        self.vm.add_clean_cb(lambda : self.unmap(ignore_fail=True))
        kpartx_output = run_cmd('kpartx', '-av', self.filename)
        parts = []
        for line in kpartx_output.split('\n'):
            if line == "" or line.startswith("gpt:") or line.startswith("dos:"):
                continue
            if line.startswith("add"):
                parts.append(line)
                continue
            logging.error('Skipping unknown line in kpartx output (%s)' % line)
        mapdevs = []
        for line in parts:
            mapdevs.append(line.split(' ')[2])
        for (part, mapdev) in zip(self.partitions, mapdevs):
            part.mapdev = '/dev/mapper/%s' % mapdev

        # At this point, all partitions are created and their mapping device has been
        # created and set as .mapdev

        # Adds a filesystem to the partition
        logging.info("Creating file systems")
        for part in self.partitions:
            part.mkfs()

    def get_grub_id(self):
        """
        @rtype:  string
        @return: name of the disk as known by grub
        """
        return '(hd%d)' % self.get_index()

    def get_index(self):
        """
        @rtype:  number
        @return: index of the disk (starting from 0)
        """
        return self.vm.disks.index(self)

    def unmap(self, ignore_fail=False):
        """
        Destroy all mapping devices
        """
        run_cmd('kpartx', '-d', self.filename, ignore_fail=ignore_fail)
        for part in self.partitions:
            self.mapdev = None

    def add_part(self, begin, length, type, mntpnt):
        """
        Add a partition to the disk

        @type  begin: number
        @param begin: Start offset of the new partition (in megabytes)
        @type  length: 
        @param length: Size of the new partition (in megabytes)
        @type  type: string
        @param type: Type of the new partition. Valid options are: ext2 ext3 xfs swap linux-swap
        @type  mntpnt: string
        @param mntpnt: Intended mountpoint inside the guest of the new partition
        """
        end = begin+length-1
        logging.debug("add_part - begin %d, length %d, end %d" % (begin, length, end))
        for part in self.partitions:
            if (begin >= part.begin and begin <= part.end) or \
                (end >= part.begin and end <= part.end):
                raise Exception('Partitions are overlapping')
            if begin > end:
                raise Exception('Partition\'s last block is before its first')
            if begin < 0 or end > self.size:
                raise Exception('Partition is out of bounds. start=%d, end=%d, disksize=%d' % (begin,end,self.size))
        part = self.Partition(disk=self, begin=begin, end=end, type=str_to_type(type), mntpnt=mntpnt)
        self.partitions.append(part)

        # We always keep the partitions in order, so that the output from kpartx matches our understanding
        self.partitions.sort(cmp=lambda x,y: x.begin - y.begin)

    def convert(self, destdir, format):
        """
        Convert the disk image
        
        @type  destdir: string
        @param destdir: Target location of converted disk image
        @type  format: string
        @param format: The target format (as understood by qemu-img)
        @rtype:  string
        @return: the name of the converted image
        """
        if self.preallocated:
            # We don't convert preallocated disk images. That would be silly.
            return self.filename

        filename = os.path.basename(self.filename)
        if '.' in filename:
            filename = filename[:filename.rindex('.')]
        destfile = '%s/%s.%s' % (destdir, filename, format)

        logging.info('Converting %s to %s, format %s' % (self.filename, format, destfile))
        run_cmd(qemu_img_path(), 'convert', '-O', format, self.filename, destfile)
        os.unlink(self.filename)
        self.filename = os.path.abspath(destfile)
        return destfile

    class Partition(object):
        def __init__(self, disk, begin, end, type, mntpnt):
            self.disk = disk
            self.begin = begin
            self.end = end
            self.type = type
            self.mntpnt = mntpnt
            self.mapdev = None

        def parted_fstype(self):
            """
            @rtype: string
            @return: the filesystem type of the partition suitable for passing to parted
            """
            return { TYPE_EXT2: 'ext2', TYPE_EXT3: 'ext2', TYPE_XFS: 'ext2', TYPE_SWAP: 'linux-swap' }[self.type]

        def create(self, disk):
            """Adds partition to the disk image (does not mkfs or anything like that)"""
            logging.info('Adding type %d partition to disk image: %s' % (self.type, disk.filename))
            run_cmd('parted', '--script', '--', disk.filename, 'mkpart', 'primary', self.parted_fstype(), self.begin, self.end)

        def mkfs(self):
            """Adds Filesystem object"""
            if not self.mapdev:
                raise Exception('We can\'t mkfs before we have a mapper device')
            self.fs = Filesystem(self.disk.vm, preallocated=True, filename=self.mapdev, type=self.type, mntpnt=self.mntpnt)
            self.fs.mkfs()

        def get_grub_id(self):
            """The name of the partition as known by grub"""
            return '(hd%d,%d)' % (self.disk.get_index(), self.get_index())

        def get_suffix(self):
            """Returns 'a4' for a device that would be called /dev/sda4 in the guest. 
               This allows other parts of VMBuilder to set the prefix to something suitable."""
            return '%s%d' % (self.disk.devletters(), self.get_index() + 1)

        def get_index(self):
            """Index of the disk (starting from 0)"""
            return self.disk.partitions.index(self)

class Filesystem(object):
    def __init__(self, vm, size=0, preallocated=False, type=None, mntpnt=None, filename=None, devletter='a', device='', dummy=False):
        self.vm = vm
        self.filename = filename
        self.size = parse_size(size)
        self.preallocated = preallocated
        self.devletter = devletter
        self.device = device
        self.dummy = dummy
           
        try:
            if int(type) == type:
                self.type = type
            else:
                self.type = str_to_type(type)
        except ValueError, e:
            self.type = str_to_type(type)

        self.mntpnt = mntpnt

    def create(self):
        logging.info('Creating filesystem: %s, size: %d, dummy: %s' % (self.mntpnt, self.size, repr(self.dummy)))
        if not self.preallocated:
            logging.info('Not preallocated, so we create it.')
            if not self.filename:
                if self.mntpnt:
                    self.filename = re.sub('[^\w\s/]', '', self.mntpnt).strip().lower()
                    self.filename = re.sub('[\w/]', '_', self.filename)
                    if self.filename == '_':
                        self.filename = 'root'
                elif self.type == TYPE_SWAP:
                    self.filename = 'swap'
                else:
                    raise VMBuilderException('mntpnt not set')

                self.filename = '%s/%s' % (self.vm.workdir, self.filename)
                while os.path.exists('%s.img' % self.filename):
                    self.filename += '_'
                self.filename += '.img'
                logging.info('A name wasn\'t specified either, so we make one up: %s' % self.filename)
            run_cmd(qemu_img_path(), 'create', '-f', 'raw', self.filename, '%dM' % self.size)
        self.mkfs()

    def mkfs(self):
        if not self.dummy:
            cmd = self.mkfs_fstype() + [self.filename]
            run_cmd(*cmd)
            self.uuid = run_cmd('vol_id', '--uuid', self.filename).rstrip()

    def mkfs_fstype(self):
        if self.vm.suite in ['dapper', 'edgy', 'feisty', 'gutsy']:
            logging.debug('%s: 128 bit inode' % self.vm.suite)
            return { TYPE_EXT2: ['mkfs.ext2', '-F'], TYPE_EXT3: ['mkfs.ext3', '-I 128', '-F'], TYPE_XFS: ['mkfs.xfs'], TYPE_SWAP: ['mkswap'] }[self.type]
        else:
            logging.debug('%s: 256 bit inode' % self.vm.suite)
            return { TYPE_EXT2: ['mkfs.ext2', '-F'], TYPE_EXT3: ['mkfs.ext3', '-F'], TYPE_XFS: ['mkfs.xfs'], TYPE_SWAP: ['mkswap'] }[self.type]

    def fstab_fstype(self):
        return { TYPE_EXT2: 'ext2', TYPE_EXT3: 'ext3', TYPE_XFS: 'xfs', TYPE_SWAP: 'swap' }[self.type]

    def fstab_options(self):
        return 'defaults'

    def mount(self):
        if (self.type != TYPE_SWAP) and not self.dummy:
            logging.debug('Mounting %s', self.mntpnt) 
            self.mntpath = '%s%s' % (self.vm.rootmnt, self.mntpnt)
            if not os.path.exists(self.mntpath):
                os.makedirs(self.mntpath)
            run_cmd('mount', '-o', 'loop', self.filename, self.mntpath)
            self.vm.add_clean_cb(self.umount)

    def umount(self):
        self.vm.cancel_cleanup(self.umount)
        if (self.type != TYPE_SWAP) and not self.dummy:
            logging.debug('Unmounting %s', self.mntpath) 
            run_cmd('umount', self.mntpath)

    def get_suffix(self):
        """Returns 'a4' for a device that would be called /dev/sda4 in the guest..
           This allows other parts of VMBuilder to set the prefix to something suitable."""
        if self.device:
            return self.device
        else:
            return '%s%d' % (self.devletters(), self.get_index() + 1)

    def devletters(self):
        """
        @rtype: string
        @return: the series of letters that ought to correspond to the device inside
                 the VM. E.g. the first filesystem of a VM would return 'a', while the 702nd would return 'zz'
        """
        return self.devletter
        
    def get_index(self):
        """Index of the disk (starting from 0)"""
        return self.vm.filesystems.index(self)
                
def parse_size(size_str):
    """Takes a size like qemu-img would accept it and returns the size in MB"""
    try:
        return int(size_str)
    except ValueError, e:
        pass

    try:
        num = int(size_str[:-1])
    except ValueError, e:
        raise VMBuilderUserError("Invalid size: %s" % size_str)

    if size_str[-1:] == 'g' or size_str[-1:] == 'G':
        return num * 1024
    if size_str[-1:] == 'm' or size_str[-1:] == 'M':
        return num
    if size_str[-1:] == 'k' or size_str[-1:] == 'K':
        return num / 1024

str_to_type_map = { 'ext2': TYPE_EXT2,
                 'ext3': TYPE_EXT3,
                 'xfs': TYPE_XFS,
                 'swap': TYPE_SWAP,
                 'linux-swap': TYPE_SWAP }

def str_to_type(type):
    try:
        return str_to_type_map[type]
    except KeyError, e:
        raise Exception('Unknown partition type: %s' % type)
        
def bootpart(disks):
    """Returns the partition which contains /boot"""
    return path_to_partition(disks, '/boot/foo')

def path_to_partition(disks, path):
    parts = get_ordered_partitions(disks)
    parts.reverse()
    for part in parts:
        if path.startswith(part.mntpnt):
            return part
    raise VMBuilderException("Couldn't find partition path %s belongs to" % path)

def create_filesystems(vm):
    for filesystem in vm.filesystems:
        filesystem.create()

def create_partitions(vm):
    for disk in vm.disks:
        disk.create(vm.workdir)

def get_ordered_filesystems(vm):
    """Returns filesystems (self hosted as well as contained in partitions
    in an order suitable for mounting them"""
    fss = list(vm.filesystems)
    for disk in vm.disks:
        fss += [part.fs for part in disk.partitions]
    fss.sort(lambda x,y: len(x.mntpnt or '')-len(y.mntpnt or ''))
    return fss

def get_ordered_partitions(disks):
    """Returns partitions from disks in an order suitable for mounting them"""
    parts = []
    for disk in disks:
        parts += disk.partitions
    parts.sort(lambda x,y: len(x.mntpnt or '')-len(y.mntpnt or ''))
    return parts

def devname_to_index(devname):
    return devname_to_index_rec(devname) - 1

def devname_to_index_rec(devname):
    if not devname:
        return 0
    return 26 * devname_to_index_rec(devname[:-1]) + (string.ascii_lowercase.index(devname[-1]) + 1) 

def index_to_devname(index, suffix=''):
    if index < 0:
        return suffix
    return suffix + index_to_devname(index / 26 -1, string.ascii_lowercase[index % 26])

def qemu_img_path():
    exes = ['kvm-img', 'qemu-img']
    for dir in os.environ['PATH'].split(os.path.pathsep):
        for exe in exes:
            path = '%s%s%s' % (dir, os.path.sep, exe)
            if os.access(path, os.X_OK):
                return path
