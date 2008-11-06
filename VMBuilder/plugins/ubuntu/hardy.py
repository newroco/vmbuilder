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
import suite
from VMBuilder.plugins.ubuntu.gutsy import Gutsy

class Hardy(Gutsy):
    virtio_net = True

    def xen_kernel_path(self):
        return '/boot/vmlinuz-2.6.24-19-xen'

    def xen_ramdisk_path(self):
        return '/boot/initrd.img-2.6.24-19-xen'
