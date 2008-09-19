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
import glob
import logging
import os
import suite
import shutil
import socket
import VMBuilder
import VMBuilder.disk as disk
from   VMBuilder.util import run_cmd

class Dapper(suite.Suite):
    updategrub = "/sbin/update-grub"
    grubroot = "/lib/grub"
    valid_flavours = { 'i386' :  ['386', '686', '686-smp', 'k7', 'k7-smp', 'server', 'server-bigiron'],
                       'amd64' : ['amd64-generic', 'amd64-k8', 'amd64-k8-smp', 'amd64-server', 'amd64-xeon']}
    default_flavour = { 'i386' : 'server', 'amd64' : 'amd64-server' }
    disk_prefix = 'hd'

    def check_kernel_flavour(self, arch, flavour):
        return flavour in self.valid_flavours[arch]

    def check_arch_validity(self, arch):
        return arch in self.valid_flavours.keys()
        
    def install(self, destdir):
        self.destdir = destdir

        logging.debug("debootstrapping")
        self.debootstrap()

        logging.debug("Setting up sources.list")
        self.install_sources_list()

        logging.debug("Installing fstab")
        self.install_fstab()

        logging.debug("Creating devices")
        self.create_devices()
    
        if self.vm.hypervisor.needs_bootloader:
            logging.debug("Installing grub")
            self.install_grub()
        
        logging.debug("Configuring guest networking")
        self.config_network()

        logging.debug("Preventing daemons from starting")
        self.prevent_daemons_starting()

        if self.vm.hypervisor.needs_bootloader:
            logging.debug("Installing menu.list")
            self.install_menu_lst()

            logging.debug("Installing kernel")
            self.install_kernel()

            logging.debug("Creating device.map")
            self.install_device_map()

        logging.debug("Installing extra packages")
        self.install_extras()

        
        logging.debug("Creating initial user")
        self.create_initial_user()

        self.install_authorized_keys()

        logging.debug("Unmounting volatile lrm filesystems")
        self.unmount_volatile()

        logging.debug("Unpreventing daemons from starting")
        self.unprevent_daemons_starting()

    def install_authorized_keys(self):
        if self.vm.ssh_key:
            os.mkdir('%s/root/.ssh' % self.destdir, 0700)
            shutil.copy(self.vm.ssh_key, '%s/root/.ssh/authorized_keys' % self.destdir)
            os.chmod('%s/root/.ssh/authorized_keys' % self.destdir, 0644)
        if self.vm.ssh_user_key:
            os.mkdir('%s/home/%s/.ssh' % (self.destdir, self.vm.user), 0700)
            shutil.copy(self.vm.ssh_user_key, '%s/home/%s/.ssh/authorized_keys' % (self.destdir, self.vm.user))
            os.chmod('%s/home/%s/.ssh/authorized_keys' % (self.destdir, self.vm.user), 0644)

    def create_initial_user(self):
        self.run_in_target('adduser', '--disabled-password', '--gecos', self.vm.name, self.vm.user)
        self.run_in_target('chpasswd', stdin=('%s:%s\n' % (self.vm.user, getattr(self.vm, 'pass'))))
        self.run_in_target('addgroup', '--system', 'admin')
        self.run_in_target('adduser', self.vm.user, 'admin')

        self.install_from_template('/etc/sudoers', 'sudoers')
        for group in ['adm', 'audio', 'cdrom', 'dialout', 'floppy', 'video', 'plugdev', 'dip', 'netdev', 'powerdev', 'lpadmin', 'scanner']:
            self.run_in_target('adduser', self.vm.user, group, ignore_fail=True)

        # Lock root account
        self.run_in_target('chpasswd', stdin='root:!\n')

    def kernel_name(self):
        return 'linux-image-%s' % (self.vm.flavour or self.default_flavour[self.vm.arch],)

    def config_network(self):
        self.install_file('/etc/hostname', self.vm.hostname)
        self.install_from_template('/etc/hosts', 'etc_hosts', { 'hostname' : self.vm.hostname, 'domain' : self.vm.domain }) 
        self.install_from_template('/etc/network/interfaces', 'interfaces')

    def unprevent_daemons_starting(self):
        os.unlink('%s/usr/sbin/policy-rc.d' % self.destdir)

    def prevent_daemons_starting(self):
        os.chmod(self.install_from_template('/usr/sbin/policy-rc.d', 'nostart-policy-rc.d'), 0755)

    def install_extras(self):
        if not self.vm.addpkg and not self.vm.removepkg:
            return
        cmd = ['apt-get', 'install', '-y', '--force-yes']
        cmd += self.vm.addpkg or []
        cmd += ['%s-' % pkg for pkg in self.vm.removepkg or []]
        self.run_in_target(*cmd)
        
    def unmount_volatile(self):
        for mntpnt in glob.glob('%s/lib/modules/*/volatile' % self.destdir):
            logging.debug("Unmounting %s" % mntpnt)
            run_cmd('umount', mntpnt)

    def install_menu_lst(self):
        run_cmd('mount', '--bind', '/dev', '%s/dev' % self.destdir)
        self.vm.add_clean_cmd('umount', '%s/dev' % self.destdir, ignore_fail=True)

        self.run_in_target('mount', '-t', 'proc', 'proc', '/proc')
        self.vm.add_clean_cmd('umount', '%s/proc' % self.destdir, ignore_fail=True)

        self.run_in_target(self.updategrub, '-y')
        self.mangle_grub_menu_lst()
        self.run_in_target(self.updategrub)
        self.run_in_target('grub-set-default', '0')

        run_cmd('umount', '%s/dev' % self.destdir)
        run_cmd('umount', '%s/proc' % self.destdir)

    def mangle_grub_menu_lst(self):
        bootdev = disk.bootpart(self.vm.disks)
        run_cmd('sed', '-ie', 's/^# kopt=root=\([^ ]*\)\(.*\)/# kopt=root=\/dev\/hd%s%d\\2/g' % (bootdev.disk.devletters, bootdev.get_index()+1), '%s/boot/grub/menu.lst' % self.destdir)
        run_cmd('sed', '-ie', 's/^# groot.*/# groot %s/g' % bootdev.get_grub_id(), '%s/boot/grub/menu.lst' % self.destdir)
        run_cmd('sed', '-ie', '/^# kopt_2_6/ d', '%s/boot/grub/menu.lst' % self.destdir)

    def install_sources_list(self):
        self.install_from_template('/etc/apt/sources.list', 'sources.list')
        self.run_in_target('apt-get', 'update')

    def install_fstab(self):
        self.install_from_template('/etc/fstab', 'dapper_fstab', { 'parts' : disk.get_ordered_partitions(self.vm.disks), 'prefix' : self.disk_prefix })

    def install_device_map(self):
        self.install_from_template('/boot/grub/device.map', 'devicemap', { 'prefix' : self.disk_prefix })

    def debootstrap(self):
        cmd = ['/usr/sbin/debootstrap', '--arch=%s' % self.vm.arch, self.vm.suite, self.destdir ]
        if self.vm.mirror:
            cmd += [self.vm.mirror]
        run_cmd(*cmd)

    def install_kernel(self):
        self.install_from_template('/etc/kernel-img.conf', 'kernelimg', { 'updategrub' : self.updategrub }) 
        run_cmd('chroot', self.destdir, 'apt-get', '--force-yes', '-y', 'install', self.kernel_name(), 'grub')

    def install_grub(self):
        self.run_in_target('apt-get', '--force-yes', '-y', 'install', 'grub')
        run_cmd('cp', '-a', '%s%s/%s/' % (self.destdir, self.grubroot, self.vm.arch == 'amd64' and 'x86_64-pc' or 'i386-pc'), '%s/boot/grub' % self.destdir) 

    def create_devices(self):
        import VMBuilder.plugins.xen

        if isinstance(self.vm.hypervisor, VMBuilder.plugins.xen.Xen):
            self.run_in_target('mknod', '/dev/xvda', 'b', '202', '0')
            self.run_in_target('mknod', '/dev/xvda1', 'b', '202', '1')
            self.run_in_target('mknod', '/dev/xvda2', 'b', '202', '2')
            self.run_in_target('mknod', '/dev/xvda3', 'b', '202', '3')
            self.run_in_target('mknod', '/dev/xvc0', 'c', '204', '191')

    def install_from_template(self, path, tmplname, context=None):
        return self.install_file(path, VMBuilder.util.render_template('ubuntu', self.vm, tmplname, context))
        
    def install_file(self, path, contents):
        fullpath = '%s%s' % (self.destdir, path)
        fp = open(fullpath, 'w')
        fp.write(contents)
        fp.close()
        return fullpath


    def run_in_target(self, *args, **kwargs):
        return run_cmd('chroot', self.destdir, *args, **kwargs)

