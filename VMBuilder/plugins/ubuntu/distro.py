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
import VMBuilder
from   VMBuilder           import register_distro, Distro
from   VMBuilder.util      import run_cmd
from   VMBuilder.exception import VMBuilderUserError
import socket
import logging
import types

class Ubuntu(Distro):
    name = 'Ubuntu'
    arg = 'ubuntu'
    suites = ['dapper', 'feisty', 'gutsy', 'hardy', 'intrepid']
    
    # Maps host arch to valid guest archs
    valid_archs = { 'amd64' : ['amd64', 'i386', 'lpia' ],
                    'i386' : [ 'i386', 'lpia' ],
                    'lpia' : [ 'i386', 'lpia' ] }


    def __init__(self, vm):
        self.vm = vm
        self.register_settings()

    def register_settings(self):
        group = self.vm.setting_group('Package options')
        group.add_option('--addpkg', action='append', metavar='PKG', help='Install PKG into the guest (can be specfied multiple times).')
        group.add_option('--removepkg', action='append', metavar='PKG', help='Remove PKG from the guest (can be specfied multiple times)')
        self.vm.register_setting_group(group)

        group = self.vm.setting_group('General OS options')
        self.host_arch = run_cmd('dpkg-architecture', '-qDEB_HOST_ARCH').rstrip()
        group.add_option('-a', '--arch', default=self.host_arch, help='Specify the target architecture.  Valid options: amd64 i386 lpia (defaults to host arch)')
        group.add_option('--hostname', default='ubuntu', help='Set NAME as the hostname of the guest. Default: ubuntu. Also uses this name as the VM name.')
        self.vm.register_setting_group(group)

        group = self.vm.setting_group('Installation options')
        group.add_option('--suite', default='intrepid', help='Suite to install. Valid options: %s [default: %%default]' % ' '.join(self.suites))
        group.add_option('--flavour', '--kernel-flavour', help='Kernel flavour to use. Default and valid options depend on architecture and suite')
        group.add_option('--iso', metavar='PATH', help='Use an iso image as the source for installation of file. Full path to the iso must be provided. If --mirror is also provided, it will be used in the final sources.list of the vm.  This requires suite and kernel parameter to match what is available on the iso, obviously.')
        group.add_option('--mirror', metavar='URL', help='Use Ubuntu mirror at URL instead of the default, which is http://archive.ubuntu.com/ubuntu for official arches and http://ports.ubuntu.com/ubuntu-ports otherwise')
        group.add_option('--components', metavar='COMPS', help='A comma seperated list of distro components to include (e.g. main,universe).')
        group.add_option('--ppa', metavar='PPA', action='append', help='Add ppa belonging to PPA to the vm\'s sources.list.')
        self.vm.register_setting_group(group)

        group = self.vm.setting_group('Settings for the initial user')
        group.add_option('--user', default='ubuntu', help='Username of initial user [default: %default]')
        group.add_option('--name', default='Ubuntu', help='Full name of initial user [default: %default]')
        group.add_option('--pass', default='ubuntu', help='Password of initial user [default: %default]')
        self.vm.register_setting_group(group)

        group = self.vm.setting_group('Other options')
        group.add_option('--ssh-key', metavar='PATH', help='Add PATH to root\'s ~/.ssh/authorized_keys (WARNING: this has strong security implications). Conf name: ssh_key')
        group.add_option('--ssh-user-key', help='Add PATH to the user\'s ~/.ssh/authorized_keys. Conf name: ssh_user_key')
        self.vm.register_setting_group(group)

    def set_defaults(self):
        if not self.vm.mirror:
            if self.vm.arch == 'lpia':
                self.vm.mirror = 'http://ports.ubuntu.com/ubuntu-ports'
            else:
                self.vm.mirror = 'http://archive.ubuntu.com/ubuntu'

        if not self.vm.components:
            self.vm.components = ['main', 'restricted', 'universe']
        else:
            self.vm.components = self.vm.components.split(',')
        
    def preflight_check(self):
        """While not all of these are strictly checks, their failure would inevitably
        lead to failure, and since we can check them before we start setting up disk
        and whatnot, we might as well go ahead an do this now."""

        if not self.vm.suite in self.suites:
            raise VMBuilderUserError('Invalid suite. Valid suites are: %s' % ' '.join(self.suites))
        
        modname = 'VMBuilder.plugins.ubuntu.%s' % (self.vm.suite, )
        mod = __import__(modname, fromlist=[self.vm.suite])
        self.suite = getattr(mod, self.vm.suite.capitalize())(self.vm)

        if self.vm.arch not in self.valid_archs[self.host_arch] or  \
            not self.suite.check_arch_validity(self.vm.arch):
            raise VMBuilderUserError('%s is not a valid architecture. Valid architectures are: %s' % (self.vm.arch, 
                                                                                                      ' '.join(self.valid_archs[self.host_arch])))

        if not self.vm.components:
            self.vm.components = ['main', 'restricted', 'universe']
        else:
            if isinstance(self.vm.components, types.StringType):
                self.vm.components = self.vm.components.split(',')

    def install(self, destdir):
        self.destdir = destdir

        self.xen_kernel_path = getattr(self.suite, 'xen_kernel_path', lambda : None)
        self.xen_ramdisk_path = getattr(self.suite, 'xen_ramdisk_path', lambda: None)

        self.suite.install(destdir)

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
