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
import suite
from VMBuilder.plugins.ubuntu.gutsy import Gutsy

class Hardy(Gutsy):
    virtio_net = True
    ec2_kernel_info = { 'i386' : 'aki-6e709707', 'amd64' : 'aki-6f709706' }
    ec2_ramdisk_info = { 'i386' : 'ari-6c709705', 'amd64' : 'ari-61709708' }

    def install_ec2(self):
        if not self.vm.ec:
            return False

        if self.vm.addpkg:
            self.vm.addpkg = []

        self.vm.addpkg += ['libc6-xen', 'ibc6-i686-']
        self.install_from_template('/etc/event.d/xvc0', 'upstart', { 'console' : 'xvc0' })
        self.install_from_template('/etc/ld.so.conf.d/libc6-xen.conf', 'xen-ld-so-conf')
        self.run_in_target('update-rc.d', '-f', 'hwclockfirst.sh', 'remove')

    def xen_kernel_path(self):
        return '/boot/vmlinuz-2.6.24-19-xen'

    def xen_ramdisk_path(self):
        return '/boot/initrd.img-2.6.24-19-xen'
