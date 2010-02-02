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
#    Virtual network management

import logging
import re
import struct
import socket

from   VMBuilder           import register_plugin
from   VMBuilder.plugins   import Plugin
from   VMBuilder.exception import VMBuilderUserError

def validate_mac(mac):
    valid_mac_address = re.compile("^([0-9a-f]{2}:){5}([0-9a-f]{2})$", re.IGNORECASE)
    if not valid_mac_address.match(mac):
        return False
    else:
        return True

def numeric_to_dotted_ip(numeric_ip):
    return socket.inet_ntoa(struct.pack('I', numeric_ip))

def dotted_to_numeric_ip(dotted_ip):
    try:
        return struct.unpack('I', socket.inet_aton(dotted_ip))[0] 
    except socket.error:
        raise VMBuilderUserError('%s is not a valid ip address' % dotted_ip)

def guess_mask_from_ip(numip):
    first_octet = numip & 0xFF

    if (first_octet > 0) and (first_octet <= 127):
        return 0xFF
    elif (first_octet > 128) and (first_octet < 192):
        return 0xFFFF
    elif (first_octet < 224):
        return 0xFFFFFF
    else:
        raise VMBuilderUserError('Could not guess network class of: %s' % numeric_to_dotted_ip(numip))

def calculate_net_address_from_ip_and_netmask(ip, netmask):
    return ip & netmask

def calculate_broadcast_address_from_ip_and_netmask(net, mask):
    return net + (mask ^ 0xFFFFFFFF)

def guess_gw_from_ip(ip):
    return ip + 0x01000000

class NetworkPlugin(Plugin):
    def preflight_check(self):
        """
        Validate the ip configuration given and set defaults
        """

        logging.debug("ip: %s" % self.vm.ip)
        
        if self.vm.mac:
            if not validate_mac(mac):
                raise VMBuilderUserError("Malformed MAC address entered: %s" % mac)

        if self.vm.ip != 'dhcp':
            if self.vm.domain == '':
                raise VMBuilderUserError('Domain is undefined and host has no domain set.')

            # num* are numeric representations
            numip = dotted_to_numeric_ip(self.vm.ip)
            
            if not self.vm.mask:
                nummask = guess_mask_from_ip(numip)
            else:
                nummask = dotted_to_numeric_ip(self.vm.mask)

            numnet = calculate_net_address_from_ip_and_netmask(numip, nummask)

            if not self.vm.net:
                self.vm.net = numeric_to_dotted_ip(numnet)

            if not self.vm.bcast:
                numbcast = calculate_broadcast_address_from_ip_and_netmask(numnet, nummask)
                self.vm.bcast = numeric_to_dotted_ip(numbcast)

            if not self.vm.gw:
                numgw = guess_gw_from_ip(numip)
                self.vm.gw = numeric_to_dotted_ip(numgw)

            if not self.vm.dns:
                self.vm.dns = self.vm.gw

            self.vm.mask = numeric_to_dotted_ip(nummask)

            logging.debug("net: %s" % self.vm.net)
            logging.debug("netmask: %s" % self.vm.mask)
            logging.debug("broadcast: %s" % self.vm.bcast)
            logging.debug("gateway: %s" % self.vm.gw)
            logging.debug("dns: %s" % self.vm.dns)

register_plugin(NetworkPlugin)
