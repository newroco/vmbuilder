from VMBuilder import register_distro, Distro
from VMBuilder.util import run_cmd
import VMBuilder
from optparse import OptionGroup
import os

class Ubuntu(Distro):
    name = 'Ubuntu'
    arg = 'ubuntu'
    suites = ['dapper', 'feisty', 'gutsy', 'hardy', 'intrepid']

    def __init__(self):
        pass

    @classmethod
    def extend_optparse(cls, optParser):
        group = OptionGroup(optParser, 'Package options')
        group.add_option('--addpkg', action='append', metavar='PKG', help='Install named package into the guest (can be specfied multiple times).')
        group.add_option('--removepkg', action='append', metavar='PKG', help='Remove PKG from the guest (can be specfied multiple times)')
        optParser.add_option_group(group)

        group = OptionGroup(optParser, 'General OS options')
        arch = run_cmd('dpkg-architecture', '-qDEB_HOST_ARCH').rstrip()
        group.add_option('-a', '--arch', default=arch, help='Specify the target architecture.  Valid options: amd64 i386 lpia (defaults to host arch)')
        group.add_option('--domain', help='Set DOMAIN as the domain name of the guest. Default: The domain of the machine running this script.')
        group.add_option('--hostname', help='Set NAME as the hostname of the guest. Default: ubuntu. Also uses this name as the VM name.')
        optParser.add_option_group(group)

        group = OptionGroup(optParser, 'Installation options')
        group.add_option('--suite', default='hardy', help='Suite to install. Valid options: %s [default: %%default]' % ' '.join(cls.suites))
        group.add_option('--iso', metavar='PATH', help='Use an iso image as the source for installation of file. Full path to the iso must be provided. If --mirror is also provided, it will be used in the final sources.list of the vm.  This requires suite and kernel parameter to match what is available on the iso, obviously.')
        group.add_option('--mirror', dest='mirror', metavar='URL', help='Use Ubuntu mirror at URL instead of the default, which is http://archive.ubuntu.com/ubuntu for official arches and http://ports.ubuntu.com/ubuntu-ports otherwise')
        optParser.add_option_group(group)

        group = OptionGroup(optParser, 'Settings for the initial user')
        group.add_option('--user', default='ubuntu', help='Username of initial user [default: %default]')
        group.add_option('--name', default='Ubuntu', help='Full name of initial user [default: %default]')
        group.add_option('--pass', default='ubuntu', help='Password of initial user [default: %default]')
        optParser.add_option_group(group)
        return optParser

    def set_defaults(self):
        if not VMBuilder.options.mirror:
            if VMBuilder.options.arch == 'lpia':
                VMBuilder.options.mirror = 'http://ports.ubuntu.com/ubuntu-ports'
            else:
                VMBuilder.options.mirror = 'http://archive.ubuntu.com/ubuntu'
        
    def install(self, destdir):
        self.destdir = destdir
        if not VMBuilder.options.suite in self.suites:
            VMBuilder.optparser.error('Invalid suite. Valid suites are: %s' % ' '.join(self.suites))
        
        suite = VMBuilder.options.suite
        mod = 'VMBuilder.plugins.ubuntu.%s' % (suite, )
        exec "import %s" % (mod,)
        exec "self.suite = %s.%s(VMBuilder)" % (mod, suite.capitalize())

        self.suite.install(destdir)


    def fstab(self):
        retval = '''# /etc/fstab: static file system information.
#
# <file system>                                 <mount point>   <type>  <options>       <dump>  <pass>
proc                                            /proc           proc    defaults        0       0
'''
        parts = VMBuilder.get_ordered_partitions()
        for part in parts:
            retval += "UUID=%42s %15s %7s %15s %d       %d" % (part.uuid, part.mntpnt, part.fstab_fstype(), part.fstab_options(), 0, 0)

    def install_bootloader(self):
        devmapfile = '%s/device.map' % VMBuilder.workdir
        devmap = open(devmapfile, 'w')
        for (disk, id) in zip(VMBuilder.disks, range(len(VMBuilder.disks))):
            devmap.write("(hd%d) %s\n" % (id, disk.filename))
        devmap.close()
        run_cmd('grub', '--device-map=%s' % devmapfile, '--batch',  stdin='''root (hd0,0)
setup (hd0)
EOT''')

register_distro(Ubuntu)
