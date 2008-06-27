from VMBuilder import register_hypervisor, Hypervisor
import VMBuilder
import os.path

class KVM(Hypervisor):
    name = 'KVM'
    arg = 'kvm'
    filetype = 'qcow2'

    def convert(self):
        for disk in VMBuilder.disks:
            disk.convert('%s/%s.%s' % (VMBuilder.options.destdir, '.'.join(os.path.basename(disk.filename).split('.')[:-1]), self.filetype), self.filetype)
    
register_hypervisor(KVM)
