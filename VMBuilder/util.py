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
#    Various utility functions
import os
import subprocess
import sys
import logging
import pwd
from exception import VMBuilderException

def run_cmd(*argv, **kwargs):
    """Runs a command.
    Locale is reset to C to make parsing error messages possible.

    stdin: a string that will be piped to the command's stdin
    ignore_fail: If True, a non-zero exit code from the command will not 
                 cause an exception to be raised.

    return value is a string containing the stdout of the command"""

    stdin= kwargs.get('stdin', None)
    ignore_fail = kwargs.get('ignore_fail', False)
    stdout = stderr = ''
    args = [str(arg) for arg in argv]
    logging.debug(args.__repr__())
    if stdin is not None:
        stdin_arg = subprocess.PIPE
    else:
        stdin_arg = sys.stdin
    env = os.environ
    env['LANG'] = 'C'
    env['LC_ALL'] = 'C'
    proc = subprocess.Popen(args, True, stdin=stdin_arg, stderr=subprocess.PIPE, stdout=subprocess.PIPE, env=env)
    if stdin is not None:
        proc.stdin.write(stdin)
        proc.stdin.close()
    for buf in proc.stderr:
        if ignore_fail:
            logging.debug(buf.rstrip())
        else:
            logging.info(buf.rstrip())
        stderr += buf
    for buf in proc.stdout:
        logging.debug(buf.rstrip())
        stdout += buf
    status = proc.wait()
    if not ignore_fail and status != 0:
        raise VMBuilderException, "Process (%s) returned %d. stdout: %s, stderr: %s" % (args.__repr__(), status, stdout, stderr)
    return stdout

def give_to_caller(path):
    """Change ownership of path to belong to $SUDO_USER if set"""
    if 'SUDO_USER' in os.environ:
        logging.debug('Changing ownership of %s to %s' % (path, os.environ['SUDO_USER']))
        (uid, gid) = pwd.getpwnam(os.environ['SUDO_USER'])[2:4]
        os.chown(path, uid, gid)

def checkroot():
    """Check if we're running as root, and bail out if we're not."""

    if os.geteuid() != 0:
        raise VMBuilderUserError("This script must be run as root (e.g. via sudo)")

def fix_ownership(files):
    """Goes through files and fixes their ownership of them. Currently, this just 
       means changing their ownership to $SUDO_USER"""
    for file in files:
        give_to_caller(file)

