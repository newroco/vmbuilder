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
#!/usr/bin/python
import builder
import os
import logging
import optparse
import tempfile

import VMBuilder.plugins
from VMBuilder.util import run_cmd 
from VMBuilder.disk import Disk
from VMBuilder.hypervisor import Hypervisor
from VMBuilder.distro import Distro
from VMBuilder.plugins import load_plugins
from exception import VMBuilderException
   
def register_hypervisor(cls):
    hypervisors[cls.arg] = cls

def register_distro(cls):
    distros[cls.arg] = cls

def checkroot():
    if os.geteuid() != 0:
        optparser.error("This script must be run as root (e.g. via sudo)")

def run(parse_options):
    checkroot()     

    finished = False
    try:
        logging.debug('Loading plugins')
        load_plugins()
        (distro, hypervisor) = parse_options()
        builder.create_directory_structure()

        distro.set_defaults()

        create_partitions()
        mount_partitions()

        install(distro, hypervisor)
        
        umount_partitions()

        hypervisor.convert()

        finished = True
    except VMBuilderException,e:
        raise e
    finally:
        if not finished:
            logging.critical("Oh, dear, an exception occurred")
        cleanup()

def cleanup():
    logging.info("Cleaning up the mess...")
    while len(cleanup_cb) > 0:
        cleanup_cb.pop(0)()

def add_clean_cb(cb):
    cleanup_cb.insert(0, cb)

def add_clean_cmd(*argv, **kwargs):
    add_clean_cb(lambda : run_cmd(*argv, **kwargs))

def create_partitions():
    for disk in VMBuilder.disks:
        disk.create()

def get_ordered_partitions():
    parts = []
    for disk in VMBuilder.disks:
        parts += disk.partitions
    parts.sort(lambda x,y: len(x.mntpnt)-len(y.mntpnt))
    return parts

def mount_partitions():
    logging.info('Mounting target filesystem')
    parts = get_ordered_partitions()
    for part in parts:
        if part.type != part.TYPE_SWAP: 
            logging.debug('Mounting %s', part.mntpnt) 
            part.mntpath = '%s%s' % (rootmnt, part.mntpnt)
            if not os.path.exists(part.mntpath):
                os.makedirs(part.mntpath)
            run_cmd('mount', part.mapdev, part.mntpath)
            add_clean_cmd('umount', part.mntpath, ignore_fail=True)

def umount_partitions():
    logging.info('Unmounting target filesystem')
    parts = get_ordered_partitions()
    parts.reverse()
    for part in parts:
        if part.type != part.TYPE_SWAP: 
            logging.debug('Unounting %s', part.mntpath) 
            run_cmd('umount', part.mntpath)
    for disk in disks:
        disk.unmap()

def install(distro, hypervisor):
    if options.in_place:
        destdir = rootmnt
    else:
        destdir = tmproot

    logging.info("Installing guest operating system. This might take some time...")
    distro.install(destdir=destdir)

    logging.info("Copying to disk images")
    run_cmd('rsync', '-aHA', '%s/' % tmproot, rootmnt)

    logging.info("Installing bootloader")
    distro.install_bootloader()

def convert():
    for disk in VMBuilder.disks:
        disk.convert('/home/soren/disk1.qcow2', 'qcow2')

def bootpart():
    return disks[0].partitions[0]

cleanup_cb = []
distros = {}
hypervisors = {}
