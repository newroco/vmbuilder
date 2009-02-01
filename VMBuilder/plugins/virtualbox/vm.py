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

from   VMBuilder import register_hypervisor, Hypervisor
import VMBuilder
import VMBuilder.hypervisor
import os
import os.path
import stat

class VirtualBox(Hypervisor):
    pass

class VirtualBox_vmdk(VirtualBox):
    name = 'VirtualBox with vmdk'
    arg = 'virtualbox-vmdk'
    vmhwversion = 4
    filetype = 'vmdk'
    preferred_storage = VMBuilder.hypervisor.STORAGE_DISK_IMAGE
    needs_bootloader = True

    def finalize(self):
        self.imgs = []
        for disk in self.vm.disks:
            img_path = disk.convert(self.vm.destdir, self.filetype)
            self.imgs.append(img_path)
            self.vm.result_files.append(img_path)

    def deploy(self):
        vmdesc = VMBuilder.util.render_template('vmware', self.vm, 'vmware',  { 'vmhwversion' : self.vmhwversion, 'mem' : self.vm.mem, 'hostname' : self.vm.hostname, 'arch' : self.vm.arch, 'guestos' : (self.vm.arch == 'amd64' and 'ubuntu-64' or 'ubuntu') })

        vmx = '%s/%s.vmx' % (self.vm.destdir, self.vm.hostname)
        fp = open(vmx, 'w')
        fp.write(vmdesc)
        fp.close()
        self.vm.result_files.append(vmx)

register_hypervisor(VirtualBox_vmdk)

