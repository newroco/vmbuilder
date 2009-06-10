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

import os
import os.path
import stat
import VMBuilder
from   VMBuilder      import register_hypervisor, Hypervisor, VMBuilderUserError
from   VMBuilder.disk import vbox_manager_path
import VMBuilder.hypervisor

class VirtualBox(Hypervisor):
    preferred_storage = VMBuilder.hypervisor.STORAGE_DISK_IMAGE
    needs_bootloader = True
    name = 'VirtualBox'
    arg = 'vbox'

    def register_options(self):
        group = self.vm.setting_group('VirtualBox options')
        group.add_option('--vbox-disk-format', metavar='FORMAT', default='vdi', help='Desired disk format. Valid options are: vdi vmdk. [default: %default]')
        self.vm.register_setting_group(group)

    def finalize(self):
        self.imgs = []
        for disk in self.vm.disks:
            img_path = disk.convert(self.vm.destdir, self.vm.vbox_disk_format)
            self.imgs.append(img_path)
            self.vm.result_files.append(img_path)

    def deploy(self):
        vm_deploy_script = VMBuilder.util.render_template('virtualbox', self.vm, 'vm_deploy_script', { 'os_type' : self.vm.distro.__class__.__name__, 'vm_name' : self.vm.hostname, 'vm_disks' : self.imgs, 'memory' : self.vm.mem })

        script_file = '%s/deploy_%s.sh' % (self.vm.destdir, self.vm.hostname)
        fp = open(script_file, 'w')
        fp.write(vm_deploy_script)
        fp.close()
        os.chmod(script_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        self.vm.result_files.append(script_file)

register_hypervisor(VirtualBox)
