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
#    The VM class
import VMBuilder
import VMBuilder.util      as util
import VMBuilder.log       as log
import VMBuilder.disk      as disk
from   VMBuilder.disk      import Disk, Filesystem
from   VMBuilder.exception import VMBuilderException, VMBuilderUserError
from   gettext import gettext
import logging
import os
import optparse
import shutil
import tempfile
import textwrap
_ = gettext

class VM(object):
    """The VM object has the following attributes of relevance to plugins:

    distro: A distro object, representing the distro running in the vm

    disks: The disk images for the vm.
    filesystems: The filesystem images for the vm.

    result_files: A list of the files that make up the entire vm.
                  The ownership of these files will be fixed up.

    optparser: Will be of interest mostly to frontends. Any sort of option
               a plugin accepts will be represented in the optparser.
    

    """
    def __init__(self):
        self.hypervisor = None #: hypervisor object, representing the hypervisor the vm is destined for
        self.distro = None

        self.disks = []
        self.filesystems = []

        self.result_files = []
        self.plugins  = []
        self._cleanup_cbs = []

        #: final destination for the disk images
        self.destdir = None
        #: tempdir where we do all the work
        self.workdir = None
        #: mount point where the disk images will be mounted
        self.rootmnt = None
        #: directory where we build up the guest filesystem
        self.tmproot = None

        self.optparser = _MyOptParser(epilog="ubuntu-vm-builder is Copyright (C) 2007-2008 Canonical Ltd. and written by Soren Hansen <soren@canonical.com>.", usage='%prog hypervisor distro [options]')
        self.optparser.arg_help = (('hypervisor', self.hypervisor_help), ('distro', self.distro_help))
        self._register_base_settings()

    def cleanup(self):
        logging.info("Cleaning up")
        while len(self._cleanup_cbs) > 0:
            self._cleanup_cbs.pop(0)()

    def add_clean_cb(self, cb):
        self._cleanup_cbs.insert(0, cb)

    def add_clean_cmd(self, *argv, **kwargs):
        cb = lambda : util.run_cmd(*argv, **kwargs)
        self.add_clean_cb(cb)
        return cb

    def cancel_cleanup(self, cb):
        try:
            self._cleanup_cbs.remove(cb)
        except ValueError, e:
            # Wasn't in there. No worries.
            pass

    def distro_help(self):
        return 'Distro. Valid options: %s' % " ".join(VMBuilder.distros.keys())

    def hypervisor_help(self):
        return 'Hypervisor. Valid options: %s' % " ".join(VMBuilder.hypervisors.keys())

    def register_setting(self, *args, **kwargs):
        return self.optparser.add_option(*args, **kwargs)

    def register_setting_group(self, group):
        return self.optparser.add_option_group(group)

    def setting_group(self, *args, **kwargs):
        return optparse.OptionGroup(self.optparser, *args, **kwargs)

    def _register_base_settings(self):
        self.register_setting('-c', dest='altconfig', default='~/.ubuntu-vm-builder', help='Specify a optional configuration file [default: %default]')
        self.register_setting('-d', '--dest', help='Specify the destination directory. [default: <hypervisor>-<distro>]')
        self.register_setting('--debug', action='callback', callback=log.set_verbosity, help='Show debug information')
        self.register_setting('-v', '--verbose', action='callback', callback=log.set_verbosity, help='Show progress information')
        self.register_setting('-q', '--quiet', action='callback', callback=log.set_verbosity, help='Silent operation')
        self.register_setting('-t', '--tmp', default=os.environ.get('TMPDIR', '/tmp'), help='Use TMP as temporary working space for image generation. Defaults to $TMPDIR if it is defined or /tmp otherwise. [default: %default]')
        self.register_setting('-o', '--overwrite', action='store_true', default=False, help='Force overwrite of destination directory if it already exist. [default: %default]')
        self.register_setting('--in-place', action='store_true', default=False, help='Install directly into the filesystem images. This is needed if your \$TMPDIR is nodev and/or nosuid, but will result in slightly larger file system images.')
        self.register_setting('--tmpfs', metavar="OPTS", help='Use a tmpfs as the working directory, specifying its size or "-" to use tmpfs default (suid,dev,size=1G).')
        self.register_setting('-m', '--mem', type='int', default=128, help='Assign MEM megabytes of memory to the guest vm. [default: %default]')

    def add_disk(self, *args, **kwargs):
        """Adds a disk image to the virtual machine"""
        disk = Disk(self, *args, **kwargs)
        self.disks.append(disk)
        return disk

    def add_filesystem(self, *args, **kwargs):
        """Adds a filesystem to the virtual machine"""
        fs = Filesystem(self, *args, **kwargs)
        self.filesystems.append(fs)
        return fs

    def call_hooks(self, func):
        for plugin in self.plugins:
            getattr(plugin, func)()
        getattr(self.hypervisor, func)()
        getattr(self.distro, func)()
        
    def set_distro(self, arg):
        if arg in VMBuilder.distros.keys():
            self.distro = VMBuilder.distros[arg](self)
            self.set_defaults()
        else:
            raise VMBuilderUserError("Invalid distro. Valid distros: %s" % " ".join(VMBuilder.distros.keys()))

    def set_hypervisor(self, arg):
        if arg in VMBuilder.hypervisors.keys():
            self.hypervisor = VMBuilder.hypervisors[arg](self)
            self.set_defaults()
        else:
            raise VMBuilderUserError("Invalid hypervisor. Valid hypervisors: %s" % " ".join(VMBuilder.hypervisors.keys()))

    def set_defaults(self):
        for plugin in VMBuilder._plugins:
            self.plugins.append(plugin(self))

        if self.distro and self.hypervisor:
            self.optparser.set_defaults(destdir='%s-%s' % (self.distro.arg, self.hypervisor.arg))

            (settings, dummy) = self.optparser.parse_args([])
            for (k,v) in settings.__dict__.iteritems():
                setattr(self, k, v)

    def create_directory_structure(self):
        """Creates the directory structure where we'll be doing all the work

        When create_directory_structure returns, the following attributes will be set:

         - L{VM.destdir}: The final destination for the disk images
         - L{VM.workdir}: The temporary directory where' we'll too all the work
         - L{VM.rootmnt}: The root mount point where all the target filesystems will be mounted
         - L{VM.tmproot}: The directory where we build up the guest filesystem

        ..and the corresponding directories are created.

        Additionally, L{VM.destdir} is created, which is where the files (disk images, filesystem
        images, run scripts, etc.) will eventually be placed.
        """

        self.workdir = self.create_workdir()
        self.add_clean_cmd('rm', '-rf', self.workdir)

        logging.debug('Temporary directory: %s', self.workdir)

        self.rootmnt = '%s/target' % self.workdir
        logging.debug('Creating the root mount directory: %s', self.rootmnt)
        os.mkdir(self.rootmnt)

        self.tmproot = '%s/root' % self.workdir
        logging.debug('Creating temporary root: %s', self.tmproot)
        os.mkdir(self.tmproot)

        # destdir is where the user's files will land when they're done
        if os.path.exists(self.destdir):
            if self.overwrite:
                logging.info('%s exists, and --overwrite specified. Removing..' % (self.destdir, ))
                shutil.rmtree(self.destdir)
            else:
                raise VMBuilderUserError('%s already exists' % (self.destdir,))

        logging.debug('Creating destination directory: %s', self.destdir)
        os.mkdir(self.destdir)
        self.add_clean_cmd('rmdir', self.destdir, ignore_fail=True)

        self.result_files.append(self.destdir)

    def create_workdir(self):
        """Creates the working directory for this vm and returns its path"""
        return tempfile.mkdtemp('', 'vmbuilder', self.tmp)

    def mount_partitions(self):
        """Mounts all the vm's partitions and filesystems below .rootmnt"""
        logging.info('Mounting target filesystems')
        fss = disk.get_ordered_filesystems(self)
        for fs in fss:
            fs.mount()

    def umount_partitions(self):
        """Unmounts all the vm's partitions and filesystems"""
        logging.info('Unmounting target filesystem')
        fss = VMBuilder.disk.get_ordered_filesystems(self)
        fss.reverse()
        for fs in fss:
            fs.umount()
        for disk in self.disks:
            disk.unmap()

    def install(self):
        if self.in_place:
            self.installdir = self.rootmnt
        else:
            self.installdir = self.tmproot

        logging.info("Installing guest operating system. This might take some time...")
        self.distro.install(self.installdir)
    
        if not self.in_place:
            logging.info("Copying to disk images")
            util.run_cmd('rsync', '-aHA', '%s/' % self.tmproot, self.rootmnt)

        if self.hypervisor.needs_bootloader:
            logging.info("Installing bootloader")
            self.distro.install_bootloader()

    def create(self):
        """
        The core vm creation method
        
        The VM creation happens in the following steps:

        A series of preliminary checks are performed:
         - We check if we're being run as root, since 
           the filesystem handling requires root priv's
         - Each plugin's prefligh_check method is called.
           See L{VMBuilder.plugins.Plugin} documentation for details
         - L{create_directory_structure} is called
         - VMBuilder.disk.create_partitions is called
         - VMBuilder.disk.create_filesystems is called
         - .mount_partitions is called
         - .install is called

        """
        util.checkroot()
        
        self.call_hooks('preflight_check')

        finished = False
        try:
            self.create_directory_structure()

            disk.create_partitions(self)
            disk.create_filesystems(self)

            self.mount_partitions()

            self.install()

            self.umount_partitions()

            self.hypervisor.finalize()

            util.fix_ownership(self.result_files)

            finished = True
        except VMBuilderException,e:
            raise e
        finally:
            if not finished:
                logging.critical("Oh, dear, an exception occurred")
            self.cleanup()

class _MyOptParser(optparse.OptionParser):
    def format_arg_help(self, formatter):
        result = []
        for arg in self.arg_help:
            result.append(self.format_arg(formatter, arg))
        return "".join(result)

    def format_arg(self, formatter, arg):
        result = []
        arghelp = arg[1]()
        arg = arg[0]
        width = formatter.help_position - formatter.current_indent - 2
        if len(arg) > width:
            arg = "%*s%s\n" % (self.current_indent, "", arg)
            indent_first = formatter.help_position
        else:                       # start help on same line as opts
            arg = "%*s%-*s  " % (formatter.current_indent, "", width, arg)
            indent_first = 0
        result.append(arg)
        help_lines = textwrap.wrap(arghelp, formatter.help_width)
        result.append("%*s%s\n" % (indent_first, "", help_lines[0]))
        result.extend(["%*s%s\n" % (formatter.help_position, "", line)
                           for line in help_lines[1:]])
        return "".join(result)

    def format_option_help(self, formatter=None):
        if formatter is None:
            formatter = self.formatter
        formatter.store_option_strings(self)
        result = []
        if self.arg_help:
            result.append(formatter.format_heading(_("Arguments")))
            formatter.indent()
            result.append(self.format_arg_help(formatter))
            result.append("\n")
            formatter.dedent()
        result.append(formatter.format_heading(_("Options")))
        formatter.indent()
        if self.option_list:
            result.append(optparse.OptionContainer.format_option_help(self, formatter))
            result.append("\n")
        for group in self.option_groups:
            result.append(group.format_help(formatter))
            result.append("\n")
        formatter.dedent()
        # Drop the last "\n", or the header if no options or option groups:
        return "".join(result[:-1])


