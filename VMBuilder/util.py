import os
import subprocess
import sys
import logging
from exception import VMBuilderException

def run_cmd(*argv, **kwargs):
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
        raise VMBuilderException, "Process returned %d. stdout: %s, stderr: %s" % (status, stdout, stderr)
    return stdout

def give_to_caller(path):
    if 'SUDO_USER' in os.environ:
        logging.debug('Changing ownership of %s to %s' % (path, os.environ['SUDO_USER']))
        (uid, gid) = pwd.getpwnam(os.environ['SUDO_USER'])
        os.chown(path, uid, gid)
        
