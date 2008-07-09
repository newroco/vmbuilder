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
from VMBuilder import register_distro, Distro
from VMBuilder.util import run_cmd
import VMBuilder
from optparse import OptionGroup
import os
import socket

class Ubuntu(Distro):
    name = 'Ubuntu'
    arg = 'ubuntu'
    suites = ['dapper', 'feisty', 'gutsy', 'hardy', 'intrepid']

    def __init__(self, vm):
        self.vm = vm
        self.register_settings()

    def register_settings(self):
        group = self.vm.setting_group('Package options')
        group.add_option('--addpkg', action='append', metavar='PKG', help='Install PKG into the guest (can be specfied multiple times).')
        group.add_option('--removepkg', action='append', metavar='PKG', help='Remove PKG from the guest (can be specfied multiple times)')
        self.vm.register_setting_group(group)

        domainname = '.'.join(socket.gethostbyname_ex(socket.gethostname())[0].split('.')[1:])

        group = self.vm.setting_group('General OS options')
        arch = run_cmd('dpkg-architecture', '-qDEB_HOST_ARCH').rstrip()
        group.add_option('-a', '--arch', default=arch, help='Specify the target architecture.  Valid options: amd64 i386 lpia (defaults to host arch)')
        group.add_option('--domain', default=domainname, help='Set DOMAIN as the domain name of the guest. Default: The domain of the machine running this script.')
        group.add_option('--hostname', default='ubuntu', help='Set NAME as the hostname of the guest. Default: ubuntu. Also uses this name as the VM name.')
        self.vm.register_setting_group(group)

        group = self.vm.setting_group('Installation options')
        group.add_option('--suite', default='hardy', help='Suite to install. Valid options: %s [default: %%default]' % ' '.join(self.suites))
        group.add_option('--flavour', help='Kernel flavour to use. Default and valid options depend on architecture and suite')
        group.add_option('--iso', metavar='PATH', help='Use an iso image as the source for installation of file. Full path to the iso must be provided. If --mirror is also provided, it will be used in the final sources.list of the vm.  This requires suite and kernel parameter to match what is available on the iso, obviously.')
        group.add_option('--mirror', metavar='URL', help='Use Ubuntu mirror at URL instead of the default, which is http://archive.ubuntu.com/ubuntu for official arches and http://ports.ubuntu.com/ubuntu-ports otherwise')
        self.vm.register_setting_group(group)

        group = self.vm.setting_group('Settings for the initial user')
        group.add_option('--user', default='ubuntu', help='Username of initial user [default: %default]')
        group.add_option('--name', default='Ubuntu', help='Full name of initial user [default: %default]')
        group.add_option('--pass', default='ubuntu', help='Password of initial user [default: %default]')
        self.vm.register_setting_group(group)

    def set_defaults(self):
        if not self.vm.mirror:
            if self.vm.arch == 'lpia':
                self.vm.mirror = 'http://ports.ubuntu.com/ubuntu-ports'
            else:
                self.vm.mirror = 'http://archive.ubuntu.com/ubuntu'
        
    def install(self, destdir):
        self.destdir = destdir
        if not self.vm.suite in self.suites:
            raise VMBuilderException('Invalid suite. Valid suites are: %s' % ' '.join(self.suites))
        
        suite = self.vm.suite
        mod = 'VMBuilder.plugins.ubuntu.%s' % (suite, )
        exec "import %s" % (mod,)
        exec "self.suite = %s.%s(self.vm)" % (mod, suite.capitalize())

        self.suite.install(destdir)


    def fstab(self):
        return
        self.suite.fstab()
        retval = '''# /etc/fstab: static file system information.
#
# <file system>                                 <mount point>   <type>  <options>       <dump>  <pass>
proc                                            /proc           proc    defaults        0       0
'''
        parts = VMBuilder.get_ordered_partitions()
        for part in parts:
            retval += "UUID=%42s %15s %7s %15s %d       %d" % (part.uuid, part.mntpnt, part.fstab_fstype(), part.fstab_options(), 0, 0)

    def install_bootloader(self):
        devmapfile = '%s/device.map' % self.vm.workdir
        devmap = open(devmapfile, 'w')
        for (disk, id) in zip(self.vm.disks, range(len(self.vm.disks))):
            devmap.write("(hd%d) %s\n" % (id, disk.filename))
        devmap.close()
        run_cmd('grub', '--device-map=%s' % devmapfile, '--batch',  stdin='''root (hd0,0)
setup (hd0)
EOT''')

register_distro(Ubuntu)
