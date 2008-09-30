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
#    Various utility functions
import logging
import os
import os.path
import pwd
import subprocess
import sys
from   exception        import VMBuilderException, VMBuilderUserError

def run_cmd(*argv, **kwargs):
    """
    Runs a command.

    Locale is reset to C to make parsing error messages possible.

    @type  stdin: string
    @param stdin: input to provide to the process on stdin. If None, process'
                  stdin will be attached to /dev/null
    @type  ignore_fail: boolean
    @param ignore_fail: If True, a non-zero exit code from the command will not 
                        cause an exception to be raised.
    @type  env: dict
    @param env: Dictionary of extra environment variables to set in the new process

    @rtype:  string
    @return: string containing the stdout of the process
    """

    env = kwargs.get('env', {})
    stdin = kwargs.get('stdin', None)
    ignore_fail = kwargs.get('ignore_fail', False)
    stdout = stderr = ''
    args = [str(arg) for arg in argv]
    logging.debug(args.__repr__())
    if stdin:
        logging.debug('stdin was set and it was a string: %s' % (stdin,))
        stdin_arg = subprocess.PIPE
    else:
        stdin_arg = file('/dev/null', 'w')
    proc_env = os.environ
    proc_env['LANG'] = 'C'
    proc_env['LC_ALL'] = 'C'
    proc_env.update(env)
    proc = subprocess.Popen(args, True, stdin=stdin_arg, stderr=subprocess.PIPE, stdout=subprocess.PIPE, env=proc_env)
    if stdin:
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
    """
    Change ownership of file to $SUDO_USER.

    @type  path: string
    @param path: file or directory to give to $SUDO_USER
    """

    if 'SUDO_USER' in os.environ:
        logging.debug('Changing ownership of %s to %s' % (path, os.environ['SUDO_USER']))
        (uid, gid) = pwd.getpwnam(os.environ['SUDO_USER'])[2:4]
        os.chown(path, uid, gid)

def checkroot():
    """
    Check if we're running as root, and bail out if we're not.
    """

    if os.geteuid() != 0:
        raise VMBuilderUserError("This script must be run as root (e.g. via sudo)")

def fix_ownership(files):
    """
    Goes through files and fixes their ownership of them. 
    
    @type  files: list
    @param files: files whose ownership should be fixed up (currently 
                  simply calls L{give_to_caller})

    """
    for file in files:
        give_to_caller(file)

def render_template(plugin, vm, tmplname, context=None):
    # Import here to avoid having to build-dep on python-cheetah
    from   Cheetah.Template import Template
    searchList = []
    if context:
        searchList.append(context)
    searchList.append(vm)

    if os.path.exists('VMBuilder') and os.path.isdir('VMBuilder'):
        template_dir = 'VMBuilder/plugins/%s/templates' % plugin
    else:
        template_dir = '/etc/vmbuilder/%s' % plugin
    tmplfile = '%s/%s.tmpl' % (template_dir, tmplname)
    t = Template(file=tmplfile, searchList=searchList)
    output = t.respond()
    logging.debug('Output from template \'%s\': %s' % (tmplfile, output))
    return output
 
