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
import logging
import suite
import shutil
import VMBuilder.disk as disk
from   VMBuilder.util import run_cmd
from   VMBuilder.plugins.ubuntu.dapper import Dapper

class Edgy(Dapper):
    valid_flavours = { 'i386' :  ['386', '686', '686-smp', 'generic', 'k7', 'k7-smp', 'server', 'server-bigiron'],
                       'amd64' : ['amd64-generic', 'amd64-k8', 'amd64-k8-smp', 'amd64-server', 'amd64-xeon', 'server']}
    default_flavour = { 'i386' : 'server', 'amd64' : 'server' }
    disk_prefix = 'sd'

    def mangle_grub_menu_lst(self):
        bootdev = disk.bootpart(self.vm.disks)
        run_cmd('sed', '-ie', 's/^# kopt=root=\([^ ]*\)\(.*\)/# kopt=root=UUID=%s\\2/g' % bootdev.fs.uuid, '%s/boot/grub/menu.lst' % self.destdir)
        run_cmd('sed', '-ie', 's/^# groot.*/# groot %s/g' % bootdev.get_grub_id(), '%s/boot/grub/menu.lst' % self.destdir)
        run_cmd('sed', '-ie', '/^# kopt_2_6/ d', '%s/boot/grub/menu.lst' % self.destdir)

    def fstab(self):
        retval = '''# /etc/fstab: static file system information.
#
# <file system>                                 <mount point>   <type>  <options>       <dump>  <pass>
proc                                            /proc           proc    defaults        0       0
'''
        parts = disk.get_ordered_partitions(self.vm.disks)
        for part in parts:
            retval += "UUID=%-40s %15s %7s %15s %d       %d\n" % (part.fs.uuid, part.fs.mntpnt, part.fs.fstab_fstype(), part.fs.fstab_options(), 0, 0)
        return retval

    def copy_settings(self):
        self.copy_to_target('/etc/default/locale', '/etc/default/locale')
        shutil.rmtree('%s/etc/console-setup' % self.destdir)
        self.copy_to_target('/etc/console-setup', '/etc/console-setup')
        self.copy_to_target('/etc/default/console-setup', '/etc/default/console-setup')
        self.copy_to_target('/etc/timezone', '/etc/timezone')
        self.run_in_target('dpkg-reconfigure', '-pcritical', 'tzdata')
        self.run_in_target('locale-gen', 'en_US')
        if self.vm.lang:
            self.run_in_target('locale-gen', self.vm.lang)
            self.install_from_template('/etc/default/locale', 'locale', { 'lang' : self.vm.lang })
        self.run_in_target('dpkg-reconfigure', '-pcritical', 'locales')
        self.run_in_target('dpkg-reconfigure', '-pcritical', 'console-setup')
