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
#    CLI plugin
from gettext import gettext
import logging
import optparse
import sys
import textwrap
import VMBuilder
import VMBuilder.hypervisor
_ = gettext


class CLI(VMBuilder.Frontend):
    arg = 'cli'
       
    def run(self):
        try:
            next = False
            conf = None
            for val in sys.argv:
                if (val == '-c') | (val == '--config'):
                    next = True
                elif next:
                    conf = val
                    break

            vm = VMBuilder.VM(conf)
            vm.register_setting('--rootsize', metavar='SIZE', type='int', default=4096, help='Size (in MB) of the root filesystem [default: %default]')
            vm.register_setting('--optsize', metavar='SIZE', type='int', default=0, help='Size (in MB) of the /opt filesystem. If not set, no /opt filesystem will be added.')
            vm.register_setting('--swapsize', metavar='SIZE', type='int', default=1024, help='Size (in MB) of the swap partition [default: %default]')
            vm.register_setting('--raw', metavar='PATH', type='string', help="Specify a file (or block device) to as first disk image.")
            vm.register_setting('--part', metavar='PATH', type='string', help="Allows to specify a partition table in PATH each line of partfile should specify (root first): \n    mountpoint size \none per line, separated by space, where size is in megabytes. You can have up to 4 virtual disks, a new disk starts on a line containing only '---'. ie: \n    root 2000 \n    /boot 512 \n    swap 1000 \n    --- \n    /var 8000 \n    /var/log 2000")
            self.set_usage(vm)

            vm.optparser.disable_interspersed_args()
            (foo, args) = vm.optparser.parse_args()
            self.handle_args(vm, args)
            vm.optparser.enable_interspersed_args()

            for opt in vm.optparser.option_list + sum([grp.option_list for grp in vm.optparser.option_groups], []):
                if len(opt._long_opts) > 1 or (opt.action == 'store' and opt._long_opts[0][2:] != opt.dest):
                    opt.help += " Config option: %s" % opt.dest

            (settings, args) = vm.optparser.parse_args(values=optparse.Values())
            for (k,v) in settings.__dict__.iteritems():
                setattr(vm, k, v)

            self.set_disk_layout(vm)

            vm.create()
        except VMBuilder.VMBuilderUserError, e:
            print >> sys.stderr, e

    def set_usage(self, vm):
        vm.optparser.set_usage('%prog hypervisor distro [options]')
        vm.optparser.arg_help = (('hypervisor', vm.hypervisor_help), ('distro', vm.distro_help))

    def handle_args(self, vm, args):
        if len(args) < 2:
            vm.optparser.error("You need to specify at least the hypervisor type and the distro")
        vm.set_hypervisor(args[0])
        vm.set_distro(args[1])

    def set_disk_layout(self, vm):
        if not vm.part:
            if vm.hypervisor.preferred_storage == VMBuilder.hypervisor.STORAGE_FS_IMAGE:
                vm.add_filesystem(size='%dM' % vm.rootsize, type='ext3', mntpnt='/')
                vm.add_filesystem(size='%dM' % vm.swapsize, type='swap', mntpnt=None)
                if vm.optsize > 0:
                    vm.add_filesystem(size='%dM' % optsize, type='ext3', mntpnt='/opt')
            else:
                if vm.raw:
                    disk = vm.add_disk(filename=vm.raw, preallocated=True)
                else:
                    size = vm.rootsize + vm.swapsize + vm.optsize
                    disk = vm.add_disk(size='%dM' % size)
                offset = 0
                disk.add_part(offset, vm.rootsize, 'ext3', '/')
                offset += vm.rootsize
                disk.add_part(offset, vm.swapsize, 'swap', 'swap')
                offset += vm.swapsize
                if vm.optsize > 0:
                    disk.add_part(offset, vm.optsize, 'ext3', '/opt')
        else:
            # We need to parse the file specified
            if vm.hypervisor.preferred_storage == VMBuilder.hypervisor.STORAGE_FS_IMAGE:
                try:
                    for line in file(vm.part):
                        elements = line.strip().split(' ')
                        if elements[0] == 'root':
                            vm.add_filesystem(elements[1], type='ext3', mntpnt='/')
                        elif elements[0] == 'swap':
                            vm.add_filesystem(elements[1], type='swap', mntpnt=None)
                        elif elements[0] == '---':
                            # We just ignore the user's attempt to specify multiple disks
                            pass
                        elif len(elements) == 3:
                            vm.add_filesystem(elements[1], type='ext3', mntpnt=elements[0], devletter='', device=elements[2], dummy=(int(elements[1]) == 0))
                        else:
                            vm.add_filesystem(elements[1], type='ext3', mntpnt=elements[0])

                except IOError, (errno, strerror):
                    vm.optparser.error("%s parsing --part option: %s" % (errno, strerror))
            else:
                try:
                    curdisk = list()
                    size = 0
                    for line in file(vm.part):
                        pair = line.strip().split(' ',1) 
                        if pair[0] == '---':
                            self.do_disk(vm, curdisk, size)
                            curdisk = list()
                            size = 0
                        elif pair[0] != '':
                            logging.debug("part: %s, size: %d" % (pair[0], int(pair[1])))
                            curdisk.append((pair[0], pair[1]))
                            size += int(pair[1])

                    self.do_disk(vm, curdisk, size)

                except IOError, (errno, strerror):
                    vm.optparser.error("%s parsing --part option: %s" % (errno, strerror))
    
    def do_disk(self, vm, curdisk, size):
        disk = vm.add_disk(size+1)
        logging.debug("do_disk - size: %d" % size)
        offset = 0
        for pair in curdisk:
            logging.debug("do_disk - part: %s, size: %s, offset: %d" % (pair[0], pair[1], offset))
            if pair[0] == 'root':
                disk.add_part(offset, int(pair[1]), 'ext3', '/')
            elif pair[0] == 'swap':
                disk.add_part(offset, int(pair[1]), pair[0], pair[0])
            else:
                disk.add_part(offset, int(pair[1]), 'ext3', pair[0])
            offset += int(pair[1])

class UVB(CLI):
    arg = 'ubuntu-vm-builder'

    def set_usage(self, vm):
        vm.optparser.set_usage('%prog hypervisor suite [options]')
        vm.optparser.arg_help = (('hypervisor', vm.hypervisor_help), ('suite', self.suite_help))

    def suite_help(self):
        return 'Suite. Valid options: %s' % " ".join(VMBuilder.plugins.ubuntu.distro.Ubuntu.suites)

    def handle_args(self, vm, args):
        if len(args) < 2:
            vm.optparser.error("You need to specify at least the hypervisor type and the suite")
        vm.set_hypervisor(args[0])
        vm.set_distro('ubuntu')
        vm.suite = args[1]
 
VMBuilder.register_frontend(CLI)
VMBuilder.register_frontend(UVB)
