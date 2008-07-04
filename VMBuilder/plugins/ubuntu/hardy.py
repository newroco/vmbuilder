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
import suite
from VMBuilder.plugins.ubuntu.dapper import Dapper

class Hardy(Dapper):
    def device_map(self):
        return '\n'.join(['(%s) %s' % (disk.get_grub_id(), disk.devname) for disk in self.vm.disks])

    def kernel_name(self):
        return 'linux-image-server'

    def fstab(self):
        retval = '''# /etc/fstab: static file system information.
#
# <file system>                                 <mount point>   <type>  <options>       <dump>  <pass>
proc                                            /proc           proc    defaults        0       0
'''
        parts = disk.get_ordered_partitions(self.vm.disks)
        for part in parts:
            retval += "UUID=%-40s %15s %7s %15s %d       %d\n" % (part.uuid, part.mntpnt, part.fstab_fstype(), part.fstab_options(), 0, 0)
        return retval


