import suite

class Hardy(suite.Suite):
    def device_map(self):
        return '\n'.join(['(hd%d) %s' % (idx, disk.devname) for (idx, disk) in zip(range(len(self.builder.disks)), self.builder.disks)])

    def kernel_name(self):
        return 'linux-image-server'
