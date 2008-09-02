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
from   VMBuilder import register_plugin, Plugin, VMBuilderUserError
import libvirt

class Libvirt(Plugin):
    name = 'libvirt integration'

    def register_options(self):
        group = self.vm.setting_group('libvirt integation')
        group.add_option('--libvirt', metavar='URI', help='Add VM to given URI')
        self.vm.register_setting_group(group)

    def all_domains(self):
        return self.conn.listDefinedDomains() + [self.conn.lookupById(id).name for id in self.conn.listDomainsID()]

    def preflight_check(self):
        print repr(self.vm.libvirt)
        if not self.vm.libvirt:
            return True

        self.conn = libvirt.open(self.vm.libvirt)
        if self.vm.hostname in self.all_domains():
            raise VMBuilderUserError('Domain %s already exists at %s' % (self.vm.hostname, self.vm.libvirt))

    def deploy(self):
        if not self.vm.libvirt:
            # Not for us
            return False

        diskxml = ''
        for (id, disk) in enumerate(self.vm.disks):
            diskxml += """
    <disk type='file' device='disk'>
      <source file='%s'/>
      <target dev='hd%c'/>
    </disk>""" % (disk.filename, disk.devletters())
        vmxml = """<domain type='kvm'>
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
</domain>""" % (self.vm.hostname, self.vm.mem, diskxml)
        if self.vm.hostname in self.all_domains():
            raise VMBuilderUserError('Domain %s already exists at %s' % (self.vm.hostname, self.vm.libvirt))
        else:
            self.conn.defineXML(vmxml)

        return True

register_plugin(Libvirt)
