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

class VMWare(Hypervisor):
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
        vmx = '%s/%s.vmx' % (self.vm.destdir, self.vm.hostname)
        fp = open(vmx, 'w')
        fp.write("""config.version = "8"
virtualHW.version = "%(vmhwversion)s"
scsi0.present = "FALSE"
scsi0.virtualDev = "lsilogic"
memsize = "%(mem)d"
Ethernet0.virtualDev = "vlance"
Ethernet0.present = "TRUE"
Ethernet0.connectionType = "bridged"
displayName = "%(hostname)s %(arch)s"
guestOS = "%(guestos)s"
priority.grabbed = "normal"
priority.ungrabbed = "normal"
powerType.powerOff = "hard"
powerType.powerOn = "hard"
powerType.suspend = "hard"
powerType.reset = "hard"
floppy0.present = "FALSE"
""" % { 'vmhwversion' : self.vmhwversion, 'mem' : self.vm.mem, 'hostname' : self.vm.hostname, 'arch' : self.vm.arch, 'guestos' : (self.vm.arch == 'amd64' and 'ubuntu-64' or 'ubuntu') })
        fp.close()
        os.chmod(vmx, stat.S_IRWXU | stat.S_IRWXU | stat.S_IROTH | stat.S_IXOTH)
        self.vm.result_files.append(vmx)

class VMWareWorkstation6(VMWare):
    name = 'VMWare Workstation 6'
    arg = 'vmw6'
    vmhwversion = 6

class VMWareServer(VMWare):
    name = 'VMWare Server'
    arg = 'vmserver'
    vmhwversion = 4

register_hypervisor(VMWareServer)
register_hypervisor(VMWareWorkstation6)
