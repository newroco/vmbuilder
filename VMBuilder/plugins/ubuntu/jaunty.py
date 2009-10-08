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
import logging
import VMBuilder.disk as disk
from   VMBuilder.util import run_cmd
from   VMBuilder.plugins.ubuntu.intrepid import Intrepid

class Jaunty(Intrepid):
    xen_kernel_flavour = 'server'
    ec2_kernel_info = { 'i386' : 'aki-c553b4ac', 'amd64' : 'aki-d653b4bf' }
    ec2_ramdisk_info = { 'i386' : 'ari-c253b4ab', 'amd64' : 'ari-d753b4be' }
    chpasswd_cmd= [ 'chpasswd' ]

    def install_ec2(self):
        self.run_in_target('apt-get', '--force-yes', '-y', 'install', 'server^')
        self.install_from_template('/etc/update-motd.d/51_update-motd', '51_update-motd')
        self.install_from_template('/etc/ec2-init/is-compat-env', 'is-compat-env')
        self.run_in_target('chmod', '755', '/etc/update-motd.d/51_update-motd')

    def mangle_grub_menu_lst(self):
        bootdev = disk.bootpart(self.vm.disks)
        run_cmd('sed', '-ie', 's/^# kopt=root=\([^ ]*\)\(.*\)/# kopt=root=UUID=%s\\2/g' % bootdev.fs.uuid, '%s/boot/grub/menu.lst' % self.destdir)
        run_cmd('sed', '-ie', 's/^# groot.*/# groot=%s/g' % bootdev.fs.uuid, '%s/boot/grub/menu.lst' % self.destdir)
        run_cmd('sed', '-ie', '/^# kopt_2_6/ d', '%s/boot/grub/menu.lst' % self.destdir)

