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
import suite
import logging
import VMBuilder.disk as disk
from   VMBuilder.util import run_cmd
from   VMBuilder.plugins.ubuntu.jaunty import Jaunty

class Karmic(Jaunty):
    def apply_ec2_settings(self):
        self.vm.addpkg += ['ec2-init',
                          'openssh-server',
                          'standard^',
                          'ec2-ami-tools',
                          'update-motd']

    def pre_install(self):
        self.vm.install_file('/etc/hosts', contents='')
