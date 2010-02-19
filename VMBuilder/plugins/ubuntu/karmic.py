#
#    Uncomplicated VM Builder
#    Copyright (C) 2007-2010 Canonical Ltd.
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
    preferred_filesystem = 'ext4'

    def apply_ec2_settings(self):
        self.context.addpkg += ['standard^',
                          'uec^']

    def pre_install(self):
        self.context.install_file('/etc/hosts', contents='')
