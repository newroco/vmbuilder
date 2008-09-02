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
import os

def load_plugins():
    for plugin in find_plugins():
        exec "import %s" % plugin

def find_plugins():
    retval = []
    for plugin_dir in __path__:
        for p in os.listdir(plugin_dir):
            path = '%s/%s' % (plugin_dir, p)
            if os.path.isdir(path) and os.path.isfile('%s/__init__.py' % path):
                retval.append("VMBuilder.plugins.%s" % p)
    return retval

class Plugin(object):
    def __init__(self, vm):
        self.vm = vm
        self.register_options()

    def register_options(self):
        pass

    def preflight_check(self):
        """Override this method with checks for anything that might cause the VM creation to fail
        
        raise an exception if you can see already that this won't work
        """
        pass

    def deploy(self):
        return False
