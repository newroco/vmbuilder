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
import logging
import VMBuilder.disk as disk
from   VMBuilder.util import run_cmd
from   VMBuilder.plugins.ubuntu.hardy import Hardy

class Intrepid(Hardy):
    def xen_kernel_path(self):
        def isvmlinuz(x): return (string.find(x, 'vmlinuz') == 0)

        list = sorted(filter(isvmlinuz, os.listdir('/boot')))
        if len(list) > 0:
            vmlinuz = '/boot/%s' % list[len(list)-1]
        else:
            vmlinuz = ''
        logging.debug('vmlinuz: %s' % self.vm.vmlinuz)
        return vmlinuz

    def xen_ramdisk_path(self):
        def isinitrd(x): return (string.find(x, 'initrd.img') == 0)

        list = sorted(filter(isinitrd, os.listdir('/boot')))
        if len(list) > 0:
            initrd =  '/boot/%s' % list[len(list)-1]
        else:
            initrd = ''
        logging.debug('initrd: %s' % self.vm.initrd)
        return initrd

    def mangle_grub_menu_lst(self):
        bootdev = disk.bootpart(self.vm.disks)
        run_cmd('sed', '-ie', 's/^# kopt=root=\([^ ]*\)\(.*\)/# kopt=root=UUID=%s\\2/g' % bootdev.fs.uuid, '%s/boot/grub/menu.lst' % self.destdir)
        run_cmd('sed', '-ie', 's/^# groot.*/# groot=%s/g' % bootdev.fs.uuid, '%s/boot/grub/menu.lst' % self.destdir)
        run_cmd('sed', '-ie', '/^# kopt_2_6/ d', '%s/boot/grub/menu.lst' % self.destdir)

