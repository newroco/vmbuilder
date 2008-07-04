#
#    Uncomplicated VM Builder
#    Copyright (C) 2007-2008 Canonical
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
#    CLI plugin
import VMBuilder
import optparse
import logging
import VMBuilder
import textwrap
from gettext import gettext
_ = gettext

class CLI(VMBuilder.Frontend):
    arg = 'cli'

    def run(self):
        vm = VMBuilder.VM()
        vm.register_setting('--rootsize', metavar='SIZE', type='int', default=4096, help='Size (in MB) of the root filesystem [default: %default]')
        vm.register_setting('--optsize', metavar='SIZE', type='int', default=0, help='Size (in MB) of the /opt filesystem. If not set, no /opt filesystem will be added.')
        vm.register_setting('--swapsize', metavar='SIZE', type='int', default=1024, help='Size (in MB) of the swap partition [default: %default]')
        vm.optparser.disable_interspersed_args()
        (foo, args) = vm.optparser.parse_args()
        if len(args) < 2:
            vm.optparser.error("You need to specify at least the hypervisor type and the distro")
        vm.set_hypervisor(args[0])
        vm.set_distro(args[1])
        vm.optparser.enable_interspersed_args()
        (settings, args) = vm.optparser.parse_args()
        for (k,v) in settings.__dict__.iteritems():
            setattr(vm, k, v)

        self.set_disk_layout(vm)

        vm.create()

    def set_disk_layout(self, vm):
        size = vm.rootsize + vm.swapsize + vm.optsize
        disk = vm.add_disk(size='%dM' % size)
        offset = 0
        disk.add_part(offset, vm.rootsize, 'ext3', '/')
        offset += vm.rootsize+1
        disk.add_part(offset, vm.swapsize, 'swap', 'swap')
        offset += vm.swapsize+1
        if vm.optsize > 0:
            disk.add_part(offset, vm.optsize, 'ext3', '/opt')

VMBuilder.register_frontend(CLI)
