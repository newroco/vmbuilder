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
from   VMBuilder import register_hypervisor, Hypervisor
import VMBuilder
import VMBuilder.hypervisor
import os
import os.path
import stat
from shutil import move
from math import floor

class VMWare(Hypervisor):
    filetype = 'vmdk'
    preferred_storage = VMBuilder.hypervisor.STORAGE_DISK_IMAGE
    needs_bootloader = True
    vmxtemplate = 'vmware'

    def finalize(self):
        self.imgs = []
        for disk in self.context.disks:
            img_path = disk.convert(self.context.destdir, self.filetype)
            self.imgs.append(img_path)
            self.context.result_files.append(img_path)

    def disks(self):
        return self.context.disks

    def deploy(self):
        vmdesc = VMBuilder.util.render_template('vmware', self.context, self.vmxtemplate, { 'disks' : self.disks(), 'vmhwversion' : self.vmhwversion, 'mem' : self.context.mem, 'hostname' : self.context.hostname, 'arch' : self.context.arch, 'guestos' : (self.context.arch == 'amd64' and 'ubuntu-64' or 'ubuntu') })

        vmx = '%s/%s.vmx' % (self.context.destdir, self.context.hostname)
        fp = open(vmx, 'w')
        fp.write(vmdesc)
        fp.close()
        os.chmod(vmx, stat.S_IRWXU | stat.S_IRWXU | stat.S_IROTH | stat.S_IXOTH)
        self.context.result_files.append(vmx)

class VMWareWorkstation6(VMWare):
    name = 'VMWare Workstation 6'
    arg = 'vmw6'
    vmhwversion = 6

class VMWareServer(VMWare):
    name = 'VMWare Server'
    arg = 'vmserver'
    vmhwversion = 4

class VMWareEsxi(VMWare):
    name = 'VMWare ESXi'
    arg = 'esxi'
    vmhwversion = 4
    adaptertype = 'lsilogic' # lsilogic | buslogic, ide is not supported by ESXi
    vmxtemplate = 'esxi.vmx'

    vmdks = [] # vmdk filenames used when deploying vmx file

    def finalize(self):
        self.imgs = []
        for disk in self.context.disks:

            # Move raw image to <imagename>-flat.vmdk
            diskfilename = os.path.basename(disk.filename)
            if '.' in diskfilename:
                diskfilename = diskfilename[:diskfilename.rindex('.')]

            flat = '%s/%s-flat.vmdk' % (self.context.destdir, diskfilename)
            self.vmdks.append(diskfilename)
            
            move(disk.filename, flat)
            
            self.context.result_files.append(flat)
            
            # Create disk descriptor file            
            sectorTotal = disk.size * 2048
            sector = int(floor(sectorTotal / 16065)) # pseudo geometry
            
            diskdescriptor = VMBuilder.util.render_template('vmware', self.context, 'flat.vmdk',  { 'adaptertype' : self.adaptertype, 'sectors' : sector, 'diskname' : os.path.basename(flat), 'disksize' : sectorTotal })
            vmdk = '%s/%s.vmdk' % (self.context.destdir, diskfilename)
            
            fp = open(vmdk, 'w')
            fp.write(diskdescriptor)
            fp.close()
            os.chmod(vmdk, stat.S_IRWXU | stat.S_IRWXU | stat.S_IROTH | stat.S_IXOTH)
            
            self.context.result_files.append(vmdk)            

    def disks(self):
        return self.vmdks

register_hypervisor(VMWareServer)
register_hypervisor(VMWareWorkstation6)
register_hypervisor(VMWareEsxi)
