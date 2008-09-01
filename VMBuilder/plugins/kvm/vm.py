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

class KVM(Hypervisor):
    name = 'KVM'
    arg = 'kvm'
    filetype = 'qcow2'
    preferred_storage = VMBuilder.hypervisor.STORAGE_DISK_IMAGE
    needs_bootloader = True

    def finalize(self):
        self.imgs = []
        self.cmdline = ['kvm', '-m', str(self.vm.mem) ]
        for disk in self.vm.disks:
            img_path = disk.convert(self.vm.destdir, self.filetype)
            self.imgs.append(img_path)
            self.vm.result_files.append(img_path)
            self.cmdline += ['-drive', 'file=%s' % os.path.basename(img_path)]

    
        self.cmdline += ['$@']

    def deploy(self):
        script = '%s/run.sh' % self.vm.destdir
        fp = open(script, 'w')
        fp.write("#!/bin/sh\n\n%s\n" % ' '.join(self.cmdline))
        fp.close()
        os.chmod(script, stat.S_IRWXU | stat.S_IRWXU | stat.S_IROTH | stat.S_IXOTH)
        self.vm.result_files.append(script)
        diskxml = ''
        for (id, img) in enumerate(self.imgs):
            diskxml += """
    <disk type='file' device='disk'>
      <source file='%s'/>
      <target dev='hd%c'/>
    </disk>""" % (img, 'abcd'[id])

        xml = '%s/domain.xml' % self.vm.destdir
        fp = open(xml, 'w')
        fp.write("""<domain type='kvm'>
  <name>%s</name>
  <memory>%d</memory>
  <vcpu>1</vcpu>
  <os>
    <type>hvm</type>
    <boot dev='hd'/>
  </os>
  <features>
    <acpi/>
  </features>
  <clock offset='utc'/>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>destroy</on_crash>
  <devices>
    <emulator>/usr/bin/kvm</emulator>
    <interface type='network'>
      <source network='default'/>
    </interface>
    <input type='mouse' bus='ps2'/>
    <graphics type='vnc' port='-1' listen='127.0.0.1'/>
    %s
  </devices>
</domain>""" % (self.vm.hostname, self.vm.mem, diskxml))
        fp.close()

register_hypervisor(KVM)
