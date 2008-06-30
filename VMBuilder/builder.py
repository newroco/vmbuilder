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
import VMBuilder
import util
import tempfile
import logging
import os
from VMBuilder.disk import Disk

def create_directory_structure():
    VMBuilder.workdir = create_workdir()
    VMBuilder.add_clean_cmd('rm', '-rf', VMBuilder.workdir)

    logging.debug('Temporary directory: %s', VMBuilder.workdir)

    # rootmnt is where the disk images will be mounted
    VMBuilder.rootmnt = '%s/target' % VMBuilder.workdir
    logging.debug('Creating the root mount directory: %s', VMBuilder.rootmnt)
    os.mkdir(VMBuilder.rootmnt)

    # tmproot it where we build up the guest filesystem
    VMBuilder.tmproot = '%s/root' % VMBuilder.workdir
    logging.debug('Creating temporary root: %s', VMBuilder.tmproot)
    os.mkdir(VMBuilder.tmproot)

    logging.debug('Creating destination directory: %s', VMBuilder.options.destdir)
    os.mkdir(VMBuilder.options.destdir)
    util.give_to_caller(VMBuilder.options.destdir)

    VMBuilder.disks = disk_layout()

def create_workdir():
    if VMBuilder.options.tmp is not None:
        workdir = tempfile.mkdtemp('', 'vmbuilder', VMBuilder.options.tmp)
    else:
        workdir = tempfile.mkdtemp('', 'vmbuilder')

    return workdir

# This is waaay to simple. All it does is to apply the sizes of root, swap and opt
# and put them all on a single disk (in separate partitions, of course)
def disk_layout():
    size = VMBuilder.options.rootsize + VMBuilder.options.swapsize + VMBuilder.options.optsize
    disk = Disk(dir=VMBuilder.workdir, size='%dM' % size)
    offset = 0
    disk.add_part(offset, VMBuilder.options.rootsize, 'ext3', '/')
    offset += VMBuilder.options.rootsize+1
    disk.add_part(offset, VMBuilder.options.swapsize, 'swap', 'swap')
    offset += VMBuilder.options.swapsize+1
    if VMBuilder.options.optsize > 0:
        disk.add_part(offset, VMBuilder.options.optsize, 'ext3', '/opt')
    return [disk]


