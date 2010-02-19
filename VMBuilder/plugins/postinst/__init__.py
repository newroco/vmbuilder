#
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
from VMBuilder import register_distro_plugin, Plugin, VMBuilderUserError
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
        group = self.context.setting_group('Post install actions')
        group.add_option('--copy', metavar='FILE', help="Read 'source dest' lines from FILE, copying source files from host to dest in the guest's file system.")
        group.add_option('--execscript', '--exec', metavar='SCRIPT', help="Run SCRIPT after distro installation finishes. Script will be called with the guest's chroot as first argument, so you can use 'chroot $1 <cmd>' to run code in the virtual machine.")
        self.context.register_setting_group(group)

    def preflight_check(self):
        if self.context.copy:
            logging.debug("Checking if --copy PATH exists: %s" % self.context.copy)
            if not(os.path.isfile(self.context.copy)):
                raise VMBuilderUserError('The path to the --copy directives is invalid: %s. Make sure you are providing a full path.' % self.context.copy)
                
        if self.context.execscript:
            logging.debug("Checking if --exec PATH exists: %s" % self.context.execscript)
            if not(os.path.isfile(self.context.execscript)):
                raise VMBuilderUserError('The path to the --execscript file is invalid: %s. Make sure you are providing a full path.' % self.context.execscript) 

            logging.debug("Checking permissions of --exec PATH: %s" % self.context.execscript)
            if not os.access(self.context.execscript, os.X_OK|os.R_OK):
                raise VMBuilderUserError('The path to the --execscript file has invalid permissions: %s. Make sure the path is readable and executable.' % self.context.execscript)

    def post_install(self):
        if self.context.copy:
            logging.info("Copying files specified by --copy in: %s" % self.context.copy)
            try:
                for line in file(self.context.copy):
                    pair = line.strip().split(' ')
                    if len(pair) < 2: # skip blank and incomplete lines
                        continue
                    util.run_cmd('cp', '-LpR', pair[0], '%s%s' % (self.context.installdir, pair[1]))

            except IOError, (errno, strerror):
                raise VMBuilderUserError("%s executing --copy directives: %s" % (errno, strerror))

        if self.context.execscript:
            logging.info("Executing script: %s" % self.context.execscript)
            util.run_cmd(self.context.execscript, self.vm.installdir)

        return True

#register_plugin(postinst)
