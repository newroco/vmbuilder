from VMBuilder.util import run_cmd 
import VMBuilder
import logging
import string

class Disk(object):
    index = 1

    def __init__(self, size='5G', preallocated=False, filename=None, dir=None):
        self.size = self.parse_size(size)
        self.preallocated = preallocated
        if filename:
            self.filename = filename
        else:
            self.filename = 'disk%d.img' % Disk.index
        # This will only work for up to 26 disks. If you *actually* 
        # need more than that, just shout, but right now, I can't 
        # be bothered to fix it. - Soren
        self.devname = '/dev/sd%s' % string.ascii_lowercase[Disk.index]
        if dir:
            self.filename = '%s/%s' % (dir, self.filename)
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

    def create(self):
        if not self.preallocated:
            logging.info('Creating disk image: %s' % self.filename)
            run_cmd('qemu-img', 'create', '-f', 'raw', self.filename, '%dM' % self.size)

        logging.info('Adding partition table to disk image: %s' % self.filename)
        run_cmd('parted', '--script', self.filename, 'mklabel', 'msdos')

        for part in self.partitions:
            part.create(self)

        logging.info('Creating loop devices corresponding to the created partitions')
        kpartx_output = run_cmd('kpartx', '-av', self.filename)
        VMBuilder.add_clean_cb(lambda : self.unmap(ignore_fail=True))
        parts = kpartx_output.split('\n')[2:-1]
        mapdevs = []
        for line in parts:
            mapdevs.append(line.split(' ')[2])
        for (part, mapdev) in zip(self.partitions, mapdevs):
            part.mapdev = '/dev/mapper/%s' % mapdev

        logging.info("Creating file systems")
        for part in self.partitions:
            part.mkfs()

    def unmap(self, ignore_fail=False):
        run_cmd('kpartx', '-d', self.filename, ignore_fail=ignore_fail)

    def add_part(self, begin, length, type, mntpnt):
        end = begin+length-1
        for part in self.partitions:
            if (begin >= part.begin and begin <= part.end) or \
                (end >= part.begin and end <= part.end):
                raise Exception('Partitions are overlapping')
            if begin > end:
                raise Exception('Partition\'s last block is before its first')
            if begin < 0 or end > self.size:
                raise Exception('Partition is out of bounds. start=%d, end=%d, disksize=%d' % (begin,end,self.size))
        part = self.Partition(begin=begin, end=end, type=self.Partition.str_to_type(type), mntpnt=mntpnt)
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

        def __init__(self, begin, end, type, mntpnt):
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


