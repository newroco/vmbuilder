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
from VMBuilder import register_hypervisor, Hypervisor
from VMBuilder.util import run_cmd
import VMBuilder
import logging
import os.path
import stat

class Xen(Hypervisor):
    name = 'Xen'
    arg = 'xen'
    preferred_storage = Hypervisor.STORAGE_FS_IMAGE
    needs_bootloader = False

    def finalize(self):
        for filesystem in self.vm.filesystems:
            destfile = '%s/%s' % (self.vm.destdir, os.path.basename(filesystem.filename))
            logging.info('Moving %s to %s' % (filesystem.filename, destfile))
            self.vm.result_files.append(destfile)
            run_cmd('cp', '--sparse=always', filesystem.filename, destfile)
    
        xenconf = '%s/foo.conf' % self.vm.destdir
        fp = open(xenconf, 'w')
        fp.write("This should be a config file for xen")
        fp.close()
        self.vm.result_files.append(xenconf)

register_hypervisor(Xen)
