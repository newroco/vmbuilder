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

from   VMBuilder import register_hypervisor, Hypervisor, VMBuilderUserError
import VMBuilder
import VMBuilder.hypervisor
import os
import os.path
import stat

class VirtualBox(Hypervisor):
    preferred_storage = VMBuilder.hypervisor.STORAGE_DISK_IMAGE
    needs_bootloader = True
    pass

class VirtualBox_vmdk(VirtualBox):
    name = 'VirtualBox with vmdk'
    arg = 'vbox-vmdk'
    vmhwversion = 4
    filetype = 'vmdk'

    def finalize(self):
        self.imgs = []
        for disk in self.vm.disks:
            img_path = disk.convert(self.vm.destdir, self.filetype)
            self.imgs.append(img_path)
            self.vm.result_files.append(img_path)

class VirtualBox_vdi(VirtualBox):
    name = 'VirtualBox with vdi'
    arg = 'vbox-vdi'

    def preflight_check(self):
        raise VMBuilderUserError('Sorry, support for vdi container isn\'t yet implemented.')

    def finalize(self):
        pass

    def deploy(self):
        pass

register_hypervisor(VirtualBox_vmdk)
register_hypervisor(VirtualBox_vdi)

