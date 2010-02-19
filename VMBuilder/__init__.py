#!/usr/bin/python
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
#    The publically exposed bits of VMBuilder
#
import logging
import VMBuilder.plugins
from   VMBuilder.distro     import Distro
from   VMBuilder.hypervisor import Hypervisor
from   VMBuilder.plugins    import Plugin
from   VMBuilder.vm         import VM
from   VMBuilder.exception  import VMBuilderException, VMBuilderUserError

# Internal bookkeeping
distros = {}
hypervisors = {}
_distro_plugins = []
_hypervisor_plugins = []

# This is meant to be populated by plugins. It should contain a list of the files that we give back to the user.

def register_hypervisor(cls):
    """Register a hypervisor plugin with VMBuilder"""
    hypervisors[cls.arg] = cls

def get_hypervisor(name):
    if name in hypervisors:
        return hypervisors[name]
    else:
        raise VMBuilderUserError('No such hypervisor. Available hypervisors: %s' % (' '.join(hypervisors.keys())))

def register_distro(cls):
    """Register a distro plugin with VMBuilder"""
    distros[cls.arg] = cls

def get_distro(name):
    if name in distros:
        return distros[name]
    else:
        raise VMBuilderUserError('No such distro. Available distros: %s' % (' '.join(distros.keys())))

def register_distro_plugin(cls):
    """Register a plugin with VMBuilder"""
    _distro_plugins.append(cls)
    _distro_plugins.sort(key=lambda x: x.priority)

def register_hypervisor_plugin(cls):
    """Register a plugin with VMBuilder"""
    _hypervisor_plugins.append(cls)
    _hypervisor_plugins.sort(key=lambda x: x.priority)

def get_version_info():
    import vcsversion
    info = vcsversion.version_info
    info['major'] = 0
    info['minor'] = 11
    info['micro'] = 3
    return info
 
logging.debug('Loading plugins')
VMBuilder.plugins.load_plugins()
