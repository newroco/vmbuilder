#    Uncomplicated VM Builder
#    Copyright (C) 2007-2009 Canonical Ltd.
#    
#    See AUTHORS for list of contributors
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 3, as
#    published by the Free Software Foundation.
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
import os
import pwd
import sys
import textwrap
import VMBuilder
import VMBuilder.util as util
from VMBuilder.disk import parse_size
import VMBuilder.hypervisor
_ = gettext


class CLI(VMBuilder.Frontend):
    arg = 'cli'
       
    def run(self):

        if len(sys.argv) < 3:
            print 'Usage: %s hypervisor distro [options]' % sys.argv[0]
            sys.exit(1)

        group = self.setting_group(' ')
        group.add_setting('config', extra_args=['-c'], type='str', help='Configuration file')
        group.add_setting('destdir', extra_args=['-d'], type='str', help='Destination directory')

        group = self.setting_group('Disk')
        group.add_setting('rootsize', metavar='SIZE', default=4096, help='Size (in MB) of the root filesystem [default: %default]')
        group.add_setting('optsize', metavar='SIZE', default=0, help='Size (in MB) of the /opt filesystem. If not set, no /opt filesystem will be added.')
        group.add_setting('swapsize', metavar='SIZE', default=1024, help='Size (in MB) of the swap partition [default: %default]')
        group.add_setting('raw', metavar='PATH', type='str', help="Specify a file (or block device) to as first disk image.")
        group.add_setting('part', metavar='PATH', type='str', help="Allows to specify a partition table in PATH each line of partfile should specify (root first): \n    mountpoint size \none per line, separated by space, where size is in megabytes. You can have up to 4 virtual disks, a new disk starts on a line containing only '---'. ie: \n    root 2000 \n    /boot 512 \n    swap 1000 \n    --- \n    /var 8000 \n    /var/log 2000")
        
        optparser = optparse.OptionParser()
        optparser.add_option('--version', action='callback', callback=self.versioninfo, help='Show version information')
        distro_name = sys.argv[2]
        distro_class = VMBuilder.get_distro(distro_name)
        distro = distro_class()
        distro.plugins.append(self)
        self.add_settings_from_context(optparser, distro)

        hypervisor_name = sys.argv[1]
        hypervisor_class = VMBuilder.get_hypervisor(hypervisor_name)
        hypervisor = hypervisor_class(distro)
        hypervisor.plugins.append(self)
        self.add_settings_from_context(optparser, hypervisor)

        self.set_setting_default('destdir', '%s-%s' % (distro_name, hypervisor_name))

        (options, args) = optparser.parse_args(sys.argv[2:])
        for option in dir(options):
            if option.startswith('_') or option in ['ensure_value', 'read_module', 'read_file']:
                continue
            val = getattr(options, option)
            if val:
                if distro.has_setting(option):
                    distro.set_setting(option, val)
                else:
                    hypervisor.set_setting(option, val)
        
        chroot_dir = util.tmpdir()

        distro.set_chroot_dir(chroot_dir)
        distro.build_chroot()

        self.set_disk_layout(hypervisor)
        hypervisor.install_os()

        destdir = self.get_setting('destdir')
        os.mkdir(destdir)
        self.fix_ownership(destdir)
        hypervisor.finalise(destdir)

        sys.exit(1)

    def fix_ownership(self, filename):
        """
        Change ownership of file to $SUDO_USER.

        @type  path: string
        @param path: file or directory to give to $SUDO_USER
        """

        if 'SUDO_USER' in os.environ:
            logging.debug('Changing ownership of %s to %s' % (filename, os.environ['SUDO_USER']))
            (uid, gid) = pwd.getpwnam(os.environ['SUDO_USER'])[2:4]
            os.chown(filename, uid, gid)

    def add_settings_from_context(self, optparser, context):
        setting_groups = set([setting.setting_group for setting in context._config.values()])
        for setting_group in setting_groups:
            optgroup = optparse.OptionGroup(optparser, setting_group.name)
            for setting in setting_group._settings:
                args = ['--%s' % setting.name]
                args += setting.extra_args
                kwargs = {}
                if setting.help:
                    kwargs['help'] = setting.help
                    if len(setting.extra_args) > 0:
                        setting.help += " Config option: %s" % setting.name
                if setting.metavar:
                    kwargs['metavar'] = setting.metavar
                if setting.get_default():
                    kwargs['default'] = setting.get_default()
                if type(setting) == VMBuilder.plugins.Plugin.BooleanSetting:
                    kwargs['action'] = 'store_true'
                if type(setting) == VMBuilder.plugins.Plugin.ListSetting:
                    kwargs['action'] = 'append'
                optgroup.add_option(*args, **kwargs)
            optparser.add_option_group(optgroup)

    def versioninfo(self, option, opt, value, parser):
        print '%(major)d.%(minor)d.%(micro)s.r%(revno)d' % VMBuilder.get_version_info()
        sys.exit(0)

    def set_usage(self, optparser):
        optparser.set_usage('%prog hypervisor distro [options]')
        optparser.arg_help = (('hypervisor', vm.hypervisor_help), ('distro', vm.distro_help))

    def handle_args(self, vm, args):
        if len(args) < 2:
            vm.optparser.error("You need to specify at least the hypervisor type and the distro")
        self.hypervisor = vm.get_hypervisor(args[0])
        self.distro = distro.vm.get_distro(args[1])

    def set_disk_layout(self, hypervisor):
        if not self.get_setting('part'):
            rootsize = parse_size(self.get_setting('rootsize'))
            swapsize = parse_size(self.get_setting('swapsize'))
            optsize = parse_size(self.get_setting('optsize'))
            if hypervisor.preferred_storage == VMBuilder.hypervisor.STORAGE_FS_IMAGE:
                hypervisor.add_filesystem(size='%dM' % rootsize, type='ext3', mntpnt='/')
                hypervisor.add_filesystem(size='%dM' % swapsize, type='swap', mntpnt=None)
                if optsize > 0:
                    hypervisor.add_filesystem(size='%dM' % optsize, type='ext3', mntpnt='/opt')
            else:
                raw = self.get_setting('raw')
                if raw:
                    disk = hypervisor.add_disk(filename=raw, preallocated=True)
                else:
                    size = rootsize + swapsize + optsize
                    tmpfile = util.tmpfile(keep=False)
                    disk = hypervisor.add_disk(tmpfile, size='%dM' % size)
                offset = 0
                disk.add_part(offset, rootsize, 'ext3', '/')
                offset += rootsize
                disk.add_part(offset, swapsize, 'swap', 'swap')
                offset += swapsize
                if optsize > 0:
                    disk.add_part(offset, optsize, 'ext3', '/opt')
        else:
            # We need to parse the file specified
            part = self.get_setting('part')
            if vm.hypervisor.preferred_storage == VMBuilder.hypervisor.STORAGE_FS_IMAGE:
                try:
                    for line in file(part):
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
                    for line in file(part):
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
        optparser.set_usage('%prog hypervisor suite [options]')
        optparser.arg_help = (('hypervisor', vm.hypervisor_help), ('suite', self.suite_help))

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
