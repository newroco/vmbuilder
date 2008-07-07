#
#    Uncomplicated VM Builder
#    Copyright (C) 2007-2008 Canonical
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
from VMBuilder.util import run_cmd 
import VMBuilder
import logging
import string

class Disk(object):
    index = 1

    def __init__(self, vm, size='5G', preallocated=False, filename=None):
        """size is by default given in MB, but 'G', 'k', 'M' suffixes are allowed, too
           preallocated means that the disk already exists and we shouldn't create it (useful for raw devices)
           filename can be given to force a certain filename or to give the name of the preallocated disk image"""
        self.size = self.parse_size(size)
        self.vm = vm

        self.preallocated = preallocated
        if filename:
            self.filename = filename
        else:
            self.filename = 'disk%d.img' % Disk.index
        self.index = Disk.index
        self.devletters = index_to_devname(self.index)
        Disk.index += 1    
        self.partitions = []

    def parse_size(self, size_str):
        """Takes a size like qemu-img would accept it and returns the size in MB"""
        try:
            return int(size_str)
        except ValueError, e:
            pass

        try:
            num = int(size_str[:-1])
        except ValueError, e:
            raise ValueError("Invalid size: %s" % size_str)

        if size_str[-1:] == 'g' or size_str[-1:] == 'G':
            return num * 1024
        if size_str[-1:] == 'm' or size_str[-1:] == 'M':
            return num
        if size_str[-1:] == 'k' or size_str[-1:] == 'K':
            return num / 1024

    def create(self, directory):
        """Create the disk image and partition mapping devices, and mkfs's the partitions"""
        if not self.preallocated:
            if directory:
                self.filename = '%s/%s' % (directory, self.filename)
            logging.info('Creating disk image: %s' % self.filename)
            run_cmd('qemu-img', 'create', '-f', 'raw', self.filename, '%dM' % self.size)

        logging.info('Adding partition table to disk image: %s' % self.filename)
        run_cmd('parted', '--script', self.filename, 'mklabel', 'msdos')

        for part in self.partitions:
            part.create(self)

        logging.info('Creating loop devices corresponding to the created partitions')
        kpartx_output = run_cmd('kpartx', '-av', self.filename)
        self.vm.add_clean_cb(lambda : self.unmap(ignore_fail=True))

        parts = kpartx_output.split('\n')[2:-1]
        mapdevs = []
        for line in parts:
            mapdevs.append(line.split(' ')[2])
        for (part, mapdev) in zip(self.partitions, mapdevs):
            part.mapdev = '/dev/mapper/%s' % mapdev

        logging.info("Creating file systems")
        for part in self.partitions:
            part.mkfs()

    def get_grub_id(self):
        return '(hd%d)' % self.get_index()

    def get_index(self):
        return self.vm.disks.index(self)

    def unmap(self, ignore_fail=False):
        run_cmd('kpartx', '-d', self.filename, ignore_fail=ignore_fail)

    def add_part(self, begin, length, type, mntpnt):
        """Add a partition to the disk. Sizes are given in megabytes"""
        end = begin+length-1
        for part in self.partitions:
            if (begin >= part.begin and begin <= part.end) or \
                (end >= part.begin and end <= part.end):
                raise Exception('Partitions are overlapping')
            if begin > end:
                raise Exception('Partition\'s last block is before its first')
            if begin < 0 or end > self.size:
                raise Exception('Partition is out of bounds. start=%d, end=%d, disksize=%d' % (begin,end,self.size))
        part = self.Partition(disk=self, begin=begin, end=end, type=self.Partition.str_to_type(type), mntpnt=mntpnt)
        self.partitions.append(part)
        self.partitions.sort(cmp=lambda x,y: x.begin - y.begin)

    def convert(self, destination, format):
        logging.info('Converting %s to %s, format %s' % (self.filename, format, destination))
        run_cmd('qemu-img', 'convert', '-O', format, self.filename, destination)

    class Partition(object):
        TYPE_EXT2 = 0
        TYPE_EXT3 = 1
        TYPE_XFS = 2
        TYPE_SWAP = 3

        def __init__(self, disk, begin, end, type, mntpnt):
            self.disk = disk
            self.begin = begin
            self.end = end
            self.type = type
            self.mntpnt = mntpnt
            self.mapdev = None

        def parted_fstype(self):
            return { self.TYPE_EXT2: 'ext2', self.TYPE_EXT3: 'ext2', self.TYPE_XFS: 'ext2', self.TYPE_SWAP: 'linux-swap' }[self.type]

        def mkfs_fstype(self):
            return { self.TYPE_EXT2: 'mkfs.ext2', self.TYPE_EXT3: 'mkfs.ext3', self.TYPE_XFS: 'mkfs.xfs', self.TYPE_SWAP: 'mkswap' }[self.type]

        def fstab_fstype(self):
            return { self.TYPE_EXT2: 'ext2', self.TYPE_EXT3: 'ext3', self.TYPE_XFS: 'xfs', self.TYPE_SWAP: 'swap' }[self.type]

        def fstab_options(self):
            return 'defaults'

        def create(self, disk):
            logging.info('Adding type %d partition to disk image: %s' % (self.type, disk.filename))
            run_cmd('parted', '--script', '--', disk.filename, 'mkpart', 'primary', self.parted_fstype(), self.begin, self.end)

        def mkfs(self):
            if not self.mapdev:
                raise Exception('We can\'t mkfs before we have a mapper device')
            run_cmd(self.mkfs_fstype(), self.mapdev)
            self.uuid = run_cmd('vol_id', '--uuid', self.mapdev).rstrip()

        def get_grub_id(self):
            return '(hd%d,%d)' % (self.disk.get_index(), self.get_index())

        def get_index(self):
            return self.disk.partitions.index(self)

        @classmethod
        def str_to_type(cls, type):
            try:
                return { 'ext2': cls.TYPE_EXT2,
                         'ext3': cls.TYPE_EXT3,
                         'xfs': cls.TYPE_XFS,
                         'swap': cls.TYPE_SWAP,
                         'linux-swap': cls.TYPE_SWAP }[type]
            except KeyError, e:
                raise Exception('Unknown partition type')


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

def create_partitions(vm):
    for disk in vm.disks:
        disk.create(vm.workdir)

def get_ordered_partitions(disks):
    """Returns partitions from disks array in an order suitable for mounting them"""
    parts = []
    for disk in disks:
        parts += disk.partitions
    parts.sort(lambda x,y: len(x.mntpnt)-len(y.mntpnt))
    return parts

def devname_to_index(devname):
    index = 0
    while True:
        index += string.ascii_lowercase.index(devname[0])
        devname = devname[1:]
        if not devname:
            break
        index = (index + 1) * 26
    return index

def index_to_devname(index):
    retval = ''
    while index >= 0:
        retval = string.ascii_lowercase[index % 26] + retval
        index = index / 26 - 1
    return retval
