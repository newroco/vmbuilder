#
#    Uncomplicated VM Builder
#    Copyright (C) 2007-2009 Canonical Ltd.
#    
#    See AUTHORS for list of contributors
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 3, as
#    published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import logging
import os
import socket
import types
import VMBuilder
from   VMBuilder           import register_distro, Distro
from   VMBuilder.util      import run_cmd
from   VMBuilder.exception import VMBuilderUserError, VMBuilderException

class Ubuntu(Distro):
    name = 'Ubuntu'
    arg = 'ubuntu'
    suites = ['dapper', 'gutsy', 'hardy', 'intrepid', 'jaunty']
    
    # Maps host arch to valid guest archs
    valid_archs = { 'amd64' : ['amd64', 'i386', 'lpia' ],
                    'i386' : [ 'i386', 'lpia' ],
                    'lpia' : [ 'i386', 'lpia' ] }

    xen_kernel = ''

    def register_options(self):
        group = self.vm.setting_group('Package options')
        group.add_option('--addpkg', action='append', metavar='PKG', help='Install PKG into the guest (can be specfied multiple times).')
        group.add_option('--removepkg', action='append', metavar='PKG', help='Remove PKG from the guest (can be specfied multiple times)')
        self.vm.register_setting_group(group)

        group = self.vm.setting_group('General OS options')
        self.host_arch = run_cmd('dpkg', '--print-architecture').rstrip()
        group.add_option('-a', '--arch', default=self.host_arch, help='Specify the target architecture.  Valid options: amd64 i386 lpia (defaults to host arch)')
        group.add_option('--hostname', default='ubuntu', help='Set NAME as the hostname of the guest. Default: ubuntu. Also uses this name as the VM name.')
        self.vm.register_setting_group(group)

        group = self.vm.setting_group('Installation options')
        group.add_option('--suite', default='jaunty', help='Suite to install. Valid options: %s [default: %%default]' % ' '.join(self.suites))
        group.add_option('--flavour', '--kernel-flavour', help='Kernel flavour to use. Default and valid options depend on architecture and suite')
        group.add_option('--variant', metavar='VARIANT', help='Passed to debootstrap --variant flag; use minbase, buildd, or fakechroot.')
        group.add_option('--iso', metavar='PATH', help='Use an iso image as the source for installation of file. Full path to the iso must be provided. If --mirror is also provided, it will be used in the final sources.list of the vm.  This requires suite and kernel parameter to match what is available on the iso, obviously.')
        group.add_option('--mirror', metavar='URL', help='Use Ubuntu mirror at URL instead of the default, which is http://archive.ubuntu.com/ubuntu for official arches and http://ports.ubuntu.com/ubuntu-ports otherwise')
        group.add_option('--proxy', metavar='URL', help='Use proxy at URL for cached packages')
        group.add_option('--install-mirror', metavar='URL', help='Use Ubuntu mirror at URL for the installation only. Apt\'s sources.list will still use default or URL set by --mirror')
        group.add_option('--security-mirror', metavar='URL', help='Use Ubuntu security mirror at URL instead of the default, which is http://security.ubuntu.com/ubuntu for official arches and http://ports.ubuntu.com/ubuntu-ports otherwise.')
        group.add_option('--install-security-mirror', metavar='URL', help='Use the security mirror at URL for installation only. Apt\'s sources.list will still use default or URL set by --security-mirror')
        group.add_option('--components', metavar='COMPS', help='A comma seperated list of distro components to include (e.g. main,universe).')
        group.add_option('--ppa', metavar='PPA', action='append', help='Add ppa belonging to PPA to the vm\'s sources.list.')
        group.add_option('--lang', metavar='LANG', default=self.get_locale(), help='Set the locale to LANG [default: %default]')
        group.add_option('--timezone', action='store_true', help='Set the timezone to the vm.')
        self.vm.register_setting_group(group)

        group = self.vm.setting_group('Settings for the initial user')
        group.add_option('--user', default='ubuntu', help='Username of initial user [default: %default]')
        group.add_option('--name', default='Ubuntu', help='Full name of initial user [default: %default]')
        group.add_option('--pass', default='ubuntu', help='Password of initial user [default: %default]')
        group.add_option('--rootpass', help='Initial root password (WARNING: this has strong security implications).')
        group.add_option('--uid', help='Initial UID value.')
        group.add_option('--gid', help='Initial GID value.')
        group.add_option('--lock-user', action='store_true', help='Lock the initial user [default %default]')
        self.vm.register_setting_group(group)

        group = self.vm.setting_group('Other options')
        group.add_option('--ssh-key', metavar='PATH', help='Add PATH to root\'s ~/.ssh/authorized_keys (WARNING: this has strong security implications).')
        group.add_option('--ssh-user-key', help='Add PATH to the user\'s ~/.ssh/authorized_keys.')
        self.vm.register_setting_group(group)

    def set_defaults(self):
        if not self.vm.mirror:
            if self.vm.arch == 'lpia':
                self.vm.mirror = 'http://ports.ubuntu.com/ubuntu-ports'
            else:
                self.vm.mirror = 'http://archive.ubuntu.com/ubuntu'

        if not self.vm.security_mirror:
            if self.vm.arch == 'lpia':
                self.vm.security_mirror = 'http://ports.ubuntu.com/ubuntu-ports'
            else:
                self.vm.security_mirror = 'http://security.ubuntu.com/ubuntu'

        if not self.vm.components:
            self.vm.components = ['main', 'restricted', 'universe']
        else:
            self.vm.components = self.vm.components.split(',')

    def get_locale(self):
        return os.getenv('LANG')

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
            if type(self.vm.components) is str:
                self.vm.components = self.vm.components.split(',')

        if self.vm.hypervisor.name == 'Xen':
            logging.info('Xen kernel default: linux-image-%s %s', self.suite.xen_kernel_flavour, self.xen_kernel_version())

        self.vm.virtio_net = self.use_virtio_net()

        if self.vm.lang:
            try:
                run_cmd('locale-gen', '%s' % self.vm.lang)
            except VMBuilderException, e:
                msg = "locale-gen does not recognize your locale '%s'" % self.vm.lang
                raise VMBuilderUserError(msg)

        if self.vm.ec2:
            self.get_ec2_kernel()
            self.get_ec2_ramdisk()

    def install(self, destdir):
        self.destdir = destdir
        self.suite.install(destdir)

    def install_vmbuilder_log(self, logfile, rootdir):
        self.suite.install_vmbuilder_log(logfile, rootdir)

    def post_mount(self, fs):
        self.suite.post_mount(fs)

    def use_virtio_net(self):
        return self.suite.virtio_net

    def install_bootloader(self):
        devmapfile = '%s/device.map' % self.vm.workdir
        devmap = open(devmapfile, 'w')
        for (disk, id) in zip(self.vm.disks, range(len(self.vm.disks))):
            devmap.write("(hd%d) %s\n" % (id, disk.filename))
        devmap.close()
        run_cmd('grub', '--device-map=%s' % devmapfile, '--batch',  stdin='''root (hd0,0)
setup (hd0)
EOT''')

    def xen_kernel_version(self):
        if self.suite.xen_kernel_flavour:
            if not self.xen_kernel:
                rmad = run_cmd('rmadison', 'linux-image-%s' % self.suite.xen_kernel_flavour)
                version = ['0', '0','0', '0']

                for line in rmad.splitlines():
                    sline = line.split('|')
                    
                    if sline[2].strip().startswith(self.vm.suite):
                        vt = sline[1].strip().split('.')
                        for i in range(4):
                            if int(vt[i]) > int(version[i]):
                                version = vt
                                break

                if version[0] == '0':
                    raise VMBuilderException('Something is wrong, no valid xen kernel for the suite %s found by rmadison' % self.vm.suite)
                
                self.xen_kernel = '%s.%s.%s-%s' % (version[0],version[1],version[2],version[3])
            return self.xen_kernel
        else:
            raise VMBuilderUserError('There is no valid xen kernel for the suite selected.')

    def xen_kernel_initrd_path(self, which):
        path = '/boot/%s-%s-%s' % (which, self.xen_kernel_version(), self.suite.xen_kernel_flavour)
        return path

    def xen_kernel_path(self):
        return self.xen_kernel_initrd_path('kernel')

    def xen_ramdisk_path(self):
        return self.xen_kernel_initrd_path('ramdisk')

    def get_ec2_kernel(self):
        if self.suite.ec2_kernel_info:
            return self.suite.ec2_kernel_info[self.vm.arch]
        else:
            raise VMBuilderUserError('EC2 is not supported for the suite selected')

    def get_ec2_ramdisk(self):
        if self.suite.ec2_ramdisk_info:
            return self.suite.ec2_ramdisk_info[self.vm.arch]
        else:
            raise VMBuilderUserError('EC2 is not supported for the suite selected')

    def disable_hwclock_access(self):
        return self.suite.disable_hwclock_access()

register_distro(Ubuntu)
