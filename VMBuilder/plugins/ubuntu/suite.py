from VMBuilder.util import run_cmd
import VMBuilder
import logging
import glob

class Suite(object):
    def __init__(self, builder):
        self.builder = builder

    def install(self, destdir):
        self.destdir = destdir

        logging.debug("debootstrapping")
        self.debootstrap()

        logging.debug("Installing fstab")
        self.install_fstab()
    
        logging.debug("Installing kernel")
        self.install_kernel()

        logging.debug("Installing grub")
        self.install_grub()

        logging.debug("Creating device.map")
        self.install_device_map()

        logging.debug("Installing menu.list")
        self.install_menu_lst()

        logging.debug("Unmounting volatile lrm filesystems")
        self.unmount_volatile()

    def unmount_volatile(self):
        for mntpnt in glob.glob('%s/lib/modules/*/volatile' % self.destdir):
            logging.debug("Unmounting %s" % mntpnt)
            run_cmd('umount', mntpnt)

    def install_menu_lst(self):
        run_cmd('chroot', self.destdir, 'update-grub', '-y')
        self.mangle_grub_menu_lst()
        run_cmd('chroot', self.destdir, 'update-grub')

    def mangle_grub_menu_lst(self):
        bootdev = 'UUID=%s' % (VMBuilder.bootpart().uuid, )
        run_cmd('sed', '-ie', 's/\/dev\/hda1/%s/g' % bootdev, '%s/boot/grub/menu.lst' % self.destdir)

    def install_fstab(self):
        fp = open('%s/etc/fstab' % self.destdir, 'w')
        fp.write(self.fstab())
        fp.close()

    def install_device_map(self):
        fp = open('%s/boot/grub/device.map' % self.destdir, 'a')
        fp.write(self.device_map())
        fp.close()

    def device_map(self):
        raise NotImplemented('Suite needs to implement device_map method')

    def debootstrap(self):
        cmd = ['debootstrap', self.builder.options.suite, self.destdir]
        if hasattr(self.builder.options, 'mirror'):
            cmd += [self.builder.options.mirror]
        run_cmd(*cmd)

    def install_kernel(self):
        kernel_name = self.kernel_name()
        run_cmd('chroot', self.destdir, 'apt-get', '--force-yes', '-y', 'install', kernel_name, 'grub')

    def install_grub(self):
        run_cmd('chroot', self.destdir, 'apt-get', '--force-yes', '-y', 'install', 'grub')
        run_cmd('cp', '-a', '%s%s' % (self.destdir, self.grubdir()), '%s/boot/grub' % self.destdir) 

    def grubdir(self):
        if self.builder.options.arch == 'amd64':
            return '/usr/lib/grub/x86_64-pc'
        else:
            return '/usr/lib/grub/i386-pc'

    def kernel_name(self):
        raise NotImplemented('Suite needs to implement kernel_name method')

    def fstab(self):
        retval = '''# /etc/fstab: static file system information.
#
# <file system>                                 <mount point>   <type>  <options>       <dump>  <pass>
proc                                            /proc           proc    defaults        0       0
'''
        parts = self.builder.get_ordered_partitions()
        for part in parts:
            retval += "UUID=%-40s %15s %7s %15s %d       %d\n" % (part.uuid, part.mntpnt, part.fstab_fstype(), part.fstab_options(), 0, 0)
        return retval


