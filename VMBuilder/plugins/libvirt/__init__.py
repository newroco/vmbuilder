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
import VMBuilder.util

class Libvirt(Plugin):
    name = 'libvirt integration'

    def register_options(self):
        group = self.vm.setting_group('libvirt integration')
        group.add_option('--libvirt', metavar='URI', help='Add VM to given URI')
        self.vm.register_setting_group(group)

    def all_domains(self):
        return self.conn.listDefinedDomains() + [self.conn.lookupById(id).name for id in self.conn.listDomainsID()]

    def preflight_check(self):
        if not self.vm.libvirt:
            return True

        import libvirt

        self.conn = libvirt.open(self.vm.libvirt)
        if self.vm.hostname in self.all_domains() and not self.vm.overwrite:
            raise VMBuilderUserError('Domain %s already exists at %s' % (self.vm.hostname, self.vm.libvirt))

    def deploy(self):
        if not self.vm.libvirt:
            # Not for us
            return False

        vmxml = VMBuilder.util.render_template('libvirt', self.vm, 'libvirtxml')

        if self.vm.hostname in self.all_domains() and not self.vm.overwrite:
            raise VMBuilderUserError('Domain %s already exists at %s' % (self.vm.hostname, self.vm.libvirt))
        else:
            self.conn.defineXML(vmxml)

        return True

register_plugin(Libvirt)
