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

import os
import logging

class firstscripts(Plugin):
    """
    Plugin to provide --firstboot and --firstlogin scripts capabilities
    """
    name = 'First-Scripts plugin'

    def register_options(self):
        group = self.vm.setting_group('Scripts')
        group.add_option('--firstboot', metavar='PATH', default='', help='Specify a script that will be copied into the guest and executed the first time the machine boots.  This script must not be interactive.')
        group.add_option('--firstlogin', metavar='PATH', default='', help='Specify a script that will be copied into the guest and will be executed the first time the user logs in. This script can be interactive.')
        self.vm.register_setting_group(group)

    def preflight_check(self):
        logging.debug("check script")
        
        if (self.vm.firstboot != ''):
            if not(os.path.isfile(self.vm.firstboot)):
                raise VMBuilderUserError('The path to the first-boot script is invalid: %s. Make sure you are providing a full path.' % self.vm.firstboot)
                
        if (self.vm.firstlogin != ''):
            if not(os.path.isfile(self.vm.firstlogin)):
                raise VMBuilderUserError('The path to the first-login script is invalid: %s.  Make sure you are providing a full path.' % self.vm.firstlogin)
        

    def install(self):
        '''This is the install event for plugins
        '''

        logging.debug("Installing scripts")
        if (self.vm.firstboot != ""):
            fd = open(self.vm.firstboot, 'r')
            content = fd.read()
            fd.close()
            self.install_file('/root/firstboot.sh', content)
            os.chmod('%s/root/firstboot.sh' % self.vm.installdir, 700)
            os.rename('%s/etc/rc.local' % self.vm.installdir, '%s/etc/rc.local.orig' % self.vm.installdir)
            self.install_from_template('/etc/rc.local', 'firstbootrc')
            os.chmod('%s/etc/rc.local' % self.vm.installdir, 755)

        if (self.vm.firstlogin != ""):
            fd = open(self.vm.firstlogin,'r')
            content = fd.read()
            fd.close()
            self.install_file('/root/firstlogin.sh', content)
            os.chmod('%s/root/firstlogin.sh' % self.vm.installdir, 755)
            os.rename('%s/etc/bash.bashrc' % self.vm.installdir, '%s/etc/bash.bashrc.orig' % self.vm.installdir)
            self.install_from_template('/etc/bash.bashrc', 'firstloginrc')


        return True

    def deploy(self):
        '''This is the deploy even for plugins
        We do not use this event here
        '''
        return True

    def install_file(self, path, contents):
        fullpath = '%s%s' % (self.vm.installdir, path)
        fp = open(fullpath, 'w')
        fp.write(contents)
        fp.close()
        return fullpath

    def install_from_template(self, path, tmplname, context=None):
        return self.install_file(path, VMBuilder.util.render_template('ubuntu', self.vm, tmplname, context))

register_plugin(firstscripts)
