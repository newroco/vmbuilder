#
#    Uncomplicated VM Builder
#    Copyright (C) 2007-2008 Canonical
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
#    CLI related classes and code
import VMBuilder
import os
import textwrap
import optparse
import log
from optparse import OptionContainer
from gettext import gettext
_ = gettext

vm.register_option('--rootsize', metavar='SIZE', type='int', default=4096, help='Size (in MB) of the root filesystem [default: %default]')
vm.register_option('--optsize', metavar='SIZE', type='int', default=0, help='Size (in MB) of the /opt filesystem. If not set, no /opt filesystem will be added.')
vm.register_option('--swapsize', metavar='SIZE', type='int', default=1024, help='Size (in MB) of the swap partition [default: %default]')
