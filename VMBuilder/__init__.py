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
from opts import create_optparser
from VMBuilder.plugins import load_plugins
from exception import VMBuilderException
   
def register_hypervisor(cls):
    hypervisors[cls.arg] = cls

def register_distro(cls):
    distros[cls.arg] = cls

# This is waaay to simple. All it does is to apply the sizes of root, swap and opt
# and put them all on a single disk (in separate partitions, of course)
def disk_layout():
    size = options.rootsize + options.swapsize + options.optsize
    disk = Disk(dir=workdir, size='%dM' % size)
    offset = 0
    disk.add_part(offset, options.rootsize, 'ext3', '/')
    offset += options.rootsize+1
    disk.add_part(offset, options.swapsize, 'swap', 'swap')
    offset += options.swapsize+1
    if options.optsize > 0:
        disk.add_part(offset, options.optsize, 'ext3', '/opt')
    return [disk]

def checkroot():
    if os.geteuid() != 0:
        optparser.error("This script must be run as root (e.g. via sudo)")

def parse_options():
    global options
    global optparser
    optparser.disable_interspersed_args()
    (options, args) = optparser.parse_args()
    if len(args) < 2:
        optparser.error("You need to specify at least the hypervisor type and the distro")

    if not args[0] in hypervisors.keys():
        optparser.error("Invalid hypervisor. Valid hypervisors: %s" % " ".join(hypervisors.keys()))
    else:
        hypervisor = hypervisors[args[0]]()
        if getattr(hypervisor, 'extend_optparse', None):
            optparser = hypervisor.extend_optparse(optparser)

    if not args[1] in distros.keys():
        optparser.error("Invalid distro. Valid distros: %s" % " ".join(distros.keys()))
    else:
        distro = distros[args[1]]()
        if getattr(distro, 'extend_optparse', None):
            optparser = distro.extend_optparse(optparser)

    optparser.set_defaults(destdir='%s-%s' % (args[0], args[1]))
    optparser.enable_interspersed_args()
    (options, args) = optparser.parse_args()
    return (distro, hypervisor)

def run():
    checkroot()     

    finished = False
    try:
        logging.debug('Loading plugins')
        load_plugins()
        (distro, hypervisor) = parse_options()
        create_directory_structure()

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
optparser = create_optparser()
distros = {}
hypervisors = {}
