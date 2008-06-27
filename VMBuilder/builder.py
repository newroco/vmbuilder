import VMBuilder
import util

rootmnt = None
tmproot = None

def create_directory_structure():
    VMBuilder.workdir = create_workdir()
    add_clean_cmd('rm', '-rf', workdir)

    logging.debug('Temporary directory: %s', workdir)

    # rootmnt is where the disk images will be mounted
    rootmnt = '%s/target' % workdir
    logging.debug('Creating the root mount directory: %s', rootmnt)
    os.mkdir(rootmnt)

    # tmproot it where we build up the guest filesystem
    tmproot = '%s/root' % workdir
    logging.debug('Creating temporary root: %s', tmproot)
    os.mkdir(tmproot)

    logging.debug('Creating destination directory: %s', options.destdir)
    os.mkdir(options.destdir)
    util.give_to_caller(options.destdir)

    disks = disk_layout()

def create_workdir():
    if options.tmp is not None:
        workdir = tempfile.mkdtemp('', 'vmbuilder', options.tmp)
    else:
        workdir = tempfile.mkdtemp('', 'vmbuilder')

    return workdir


