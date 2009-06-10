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
from   VMBuilder      import register_hypervisor, Hypervisor
from   VMBuilder.util import run_cmd
import VMBuilder
import VMBuilder.hypervisor
import logging
import os.path
import stat

class Xen(Hypervisor):
    name = 'Xen'
    arg = 'xen'
    preferred_storage = VMBuilder.hypervisor.STORAGE_FS_IMAGE
    needs_bootloader = False

    def register_options(self):
        group = self.vm.setting_group('Xen option')
        group.add_option('--xen-kernel', metavar='PATH', help='Path to the kernel to use (e.g.: /boot/vmlinux-2.6.27-7-server). Default depends on distribution and suite')
        group.add_option('--xen-ramdisk', metavar='PATH', help='Path to the ramdisk to use (e.g.: /boot/initrd.img-2.6.27-7-server). Default depends on distribution and suite.')
        self.vm.register_setting_group(group)

    def finalize(self):
        destimages = []
        for filesystem in self.vm.filesystems:
            if not filesystem.preallocated:
                destfile = '%s/%s' % (self.vm.destdir, os.path.basename(filesystem.filename))
                logging.info('Moving %s to %s' % (filesystem.filename, destfile))
                self.vm.result_files.append(destfile)
                run_cmd('cp', '--sparse=always', filesystem.filename, destfile)
                os.unlink(filesystem.filename)
                filesystem.filename = os.path.abspath(destfile)
                destimages.append(destfile)
    
        if not self.vm.xen_kernel:
            self.vm.xen_kernel = self.vm.distro.xen_kernel_path()
        if not self.vm.xen_ramdisk:
            self.vm.xen_ramdisk = self.vm.distro.xen_ramdisk_path()

        xenconf = '%s/xen.conf' % self.vm.destdir
        fp = open(xenconf, 'w')
        fp.write("""
# Configuration file for the Xen instance %s, created
# by VMBuilder
kernel = '%s'
ramdisk = '%s'
memory = %d

root = '/dev/xvda1 ro'
disk = [
%s
]

name = '%s'

dhcp    = 'dhcp'
vif = ['']

on_poweroff = 'destroy'
on_reboot   = 'restart'
on_crash    = 'restart'

extra = 'xencons=tty console=tty1 console=hvc0'

"""  %   (self.vm.name,
          self.vm.xen_kernel,
          self.vm.xen_ramdisk,
          self.vm.mem,
          ',\n'.join(["'tap:aio:%s,xvda%d,w'" % (os.path.abspath(img), id+1) for (img, id) in zip(destimages, range(len(destimages)))]),
          self.vm.name))
        fp.close()
        self.vm.result_files.append(xenconf)

register_hypervisor(Xen)
