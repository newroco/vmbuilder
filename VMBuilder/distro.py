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
#    Distro super class
from   VMBuilder.util    import run_cmd
import VMBuilder.plugins

class Distro(VMBuilder.plugins.Plugin):
    def has_xen_support(self):
        """Install the distro into destdir"""
        raise NotImplemented('Distro subclasses need to implement the has_xen_support method')
    
    def install(self, destdir):
        """Install the distro into destdir"""
        raise NotImplemented('Distro subclasses need to implement the install method')

    def post_mount(self, fs):
        """Called each time a filesystem is mounted to let the distro add things to the filesystem"""
