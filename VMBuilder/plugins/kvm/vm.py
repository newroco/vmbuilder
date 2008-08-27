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
import VMBuilder
import os
import os.path
import stat

class KVM(Hypervisor):
    name = 'KVM'
    arg = 'kvm'
    filetype = 'qcow2'
    preferred_storage = Hypervisor.STORAGE_DISK_IMAGE
    needs_bootloader = True

    def finalize(self):
        cmdline = ['kvm', '-m', str(self.vm.mem) ]
        for disk in self.vm.disks:
            img_path = disk.convert(self.vm.destdir, self.filetype)
            cmdline += ['-drive', 'file=%s' % os.path.basename(img_path)]
    
        cmdline += ['$@']
        script = '%s/run.sh' % self.vm.destdir
        fp = open(script, 'w')
        fp.write("#!/bin/sh\n\n%s\n" % ' '.join(cmdline))
        fp.close()
        os.chmod(script, stat.S_IRWXU | stat.S_IRWXU | stat.S_IROTH | stat.S_IXOTH)
        self.vm.result_files.append(script)

register_hypervisor(KVM)
