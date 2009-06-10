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
import suite
from VMBuilder.plugins.ubuntu.gutsy import Gutsy

class Hardy(Gutsy):
    virtio_net = True
    ec2_kernel_info = { 'i386' : 'aki-6e709707', 'amd64' : 'aki-6f709706' }
    ec2_ramdisk_info = { 'i386' : 'ari-6c709705', 'amd64' : 'ari-61709708' }

    def install_ec2(self):
        self.run_in_target('apt-get' ,'--force-yes', '-y', 'install', 'libc6-xen')
        self.run_in_target('apt-get','--purge','--force-yes', '-y', 'remove', 'libc6-i686')
        self.install_from_template('/etc/event.d/xvc0', 'upstart', { 'console' : 'xvc0' })
        self.install_from_template('/etc/ld.so.conf.d/libc6-xen.conf', 'xen-ld-so-conf')
        self.run_in_target('update-rc.d', '-f', 'hwclockfirst.sh', 'remove')
        self.install_from_template('/etc/update-motd.d/51_update-motd', '51_update-motd-hardy')
        self.run_in_target('chmod', '755', '/etc/update-motd.d/51_update-motd')

    def xen_kernel_path(self):
        return '/boot/vmlinuz-2.6.24-19-xen'

    def xen_ramdisk_path(self):
        return '/boot/initrd.img-2.6.24-19-xen'
