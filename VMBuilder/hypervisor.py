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
#    Hypervisor super class

STORAGE_DISK_IMAGE = 0
STORAGE_FS_IMAGE = 1

class Hypervisor(object):
    STORAGE_DISK_IMAGE = STORAGE_DISK_IMAGE
    STORAGE_FS_IMAGE   = STORAGE_FS_IMAGE

    def __init__(self, vm):
        self.vm = vm
