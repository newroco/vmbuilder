#
#    Uncomplicated VM Builder
#    Copyright (C) 2010 Canonical Ltd.
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
import os
from   VMBuilder.util import run_cmd
from   VMBuilder.plugins.ubuntu.karmic import Karmic

class Lucid(Karmic):
    valid_flavours = { 'i386' :  ['386', 'generic', 'generic-pae', 'virtual'],
                       'amd64' : ['generic', 'preempt', 'server', 'virtual'] }

    def divert_file(self, path, add):
        if add: action = "--add"
        else: action = "--remove"
        if not add:
            os.remove('%s/%s' % (self.context.chroot_dir, path))
        run_cmd('chroot', self.context.chroot_dir, 'dpkg-divert', '--local', '--rename', action, path)
