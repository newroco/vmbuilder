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
from VMBuilder import register_plugin, Plugin, VMBuilderUserError
from VMBuilder.util import run_cmd

import logging
import os
import shutil
import VMBuilder
import VMBuilder.util as util

class postinst(Plugin):
    """
    Plugin to provide --exec and --copy post install capabilities
    """
    name ='Post install plugin'

    def register_options(self):
        group = self.vm.setting_group('Post install actions')
        group.add_option('--copy', metavar='FILE', help="Read 'source dest' lines from FILE, copying source files from host to dest in the guest's file system.")
        group.add_option('--execscript', '--exec', metavar='SCRIPT', help="Run SCRIPT after distro installation finishes. Script will be called with the guest's chroot as first argument, so you can use 'chroot $1 <cmd>' to run code in the virtual machine.")
        self.vm.register_setting_group(group)

    def preflight_check(self):
        if self.vm.copy:
            logging.debug("Checking if --copy PATH exists: %s" % self.vm.copy)
            if not(os.path.isfile(self.vm.copy)):
                raise VMBuilderUserError('The path to the --copy directives is invalid: %s. Make sure you are providing a full path.' % self.vm.copy)
                
        if self.vm.execscript:
            logging.debug("Checking if --exec PATH exists: %s" % self.vm.execscript)
            if not(os.path.isfile(self.vm.execscript)):
                raise VMBuilderUserError('The path to the --execscript file is invalid: %s. Make sure you are providing a full path.' % self.vm.execscript) 

    def post_install(self):
        if self.vm.copy:
            logging.info("Copying files specified by --copy in: %s" % self.vm.copy)
            try:
                for line in file(self.vm.copy):
                    pair = line.strip().split(' ')
                    util.run_cmd('cp', '-LpR', pair[0], '%s%s' % (self.vm.installdir, pair[1]))

            except IOError, (errno, strerror):
                raise VMBuilderUserError("%s executing --copy directives: %s" % (errno, strerror))

        if self.vm.execscript:
            logging.info("Executing script: %s" % self.vm.execscript)
            util.run_cmd(self.vm.execscript, self.vm.installdir)

        return True

register_plugin(postinst)
