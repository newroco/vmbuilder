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
#    Logging

import logging

FORMAT='%(asctime)s %(levelname)-8s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

def set_verbosity(option, opt_str, value, parser):
    if opt_str == '--debug':
        logging.getLogger().setLevel(logging.DEBUG)
    elif opt_str == '--verbose':
        logging.getLogger().setLevel(logging.INFO)
    elif opt_str == '--quiet':
        logging.getLogger().setLevel(logging.CRITICAL)
