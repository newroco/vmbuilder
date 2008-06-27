import os
import sys
import tempfile
import logging
import optparse
from VMBuilder.util import run_cmd 

class VMBuilder(object):
    def __init__(self):
        # Set some reasonable defaults
        self.tmpdir = '/dev/shm'
        # Ok, this might not be reasonable, but it's handy while we're working it all out.
        logging.basicConfig(level=logging.INFO)

        self.cleanup_cb = []
        self.workdir = self.get_workdir()
        self.disks = self.default_disk_layout()
        logging.debug('Temporary directory: %s', self.workdir)
        self.add_clean_cmd('rm', '-rf', self.workdir)
        self.rootmnt = '%s/target' % self.workdir
        self.tmproot = '%s/root' % self.workdir
        os.mkdir(self.tmproot)
        self.distro = Ubuntu(self)
        self.in_place = False
        (self.options, self.args) = self.parser.parse_args()

    def default_disk_layout(self):
        disk = Disk(self, dir=self.workdir)
        disk.add_part(0, 4096, 'ext3', '/')
        disk.add_part(4097, 5120, 'swap', 'swap')
        return [disk]

    def get_workdir(self):
        if self.tmpdir is not None:
            return tempfile.mkdtemp('', 'vmbuilder', self.tmpdir)
        else:
            return tempfile.mkdtemp('', 'vmbuilder')

    def cleanup(self):
        logging.info("Cleaning up the mess...")
        while len(self.cleanup_cb) > 0:
            self.cleanup_cb.pop(0)()

    def add_clean_cb(self, cb):
        self.cleanup_cb.insert(0, cb)

    def add_clean_cmd(self, *argv):
        self.add_clean_cb(lambda : run_cmd(*argv))

    def create_partitions(self):
        for disk in self.disks:
            disk.create()
    
    def get_ordered_partitions(self):
        parts = []
        for disk in self.disks:
            parts += disk.partitions
        parts.sort(lambda x,y: len(x.mntpnt)-len(y.mntpnt))
        return parts
        
    def mount_partitions(self):
        logging.info('Mounting target filesystem')
        parts = self.get_ordered_partitions()
        for part in parts:
            if part.type != part.TYPE_SWAP: 
                logging.debug('Mounting %s', part.mntpnt) 
                mntpath = '%s%s' % (self.rootmnt, part.mntpnt)
                if not os.path.exists(mntpath):
                    os.makedirs(mntpath)
                run_cmd('mount', part.mapdev, mntpath)
                self.add_clean_cmd('umount', mntpath)

    def install(self):
        if self.in_place:
            destdir = self.rootmnt
        else:
            destdir = self.tmproot

        logging.info("Installing guest operating system. This might take some time...")
        self.distro.install(destdir=destdir)

        logging.info("Copying to disk images")
        run_cmd('rsync', '-aHA', '%s/' % self.tmproot, self.rootmnt)

        logging.info("Installing bootloader")
        self.distro.install_bootloader()

    def convert(self):
        for disk in self.disks:
            disk.convert('/home/soren/disk1.qcow2', 'qcow2')

    def run(self):
        self.create_partitions()
        self.mount_partitions()
        self.install()
        self.convert()
#        self.cleanup()

class Distro(object):
    def install(self):
        pass


if __name__ == "__main__":
    builder = VMBuilder()
#    try:
    builder.run()
