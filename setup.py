#!/usr/bin/env python
from distutils.core import setup
import VMBuilder.plugins
from glob import glob
import os.path
import subprocess

if os.path.exists('.bzr'):
    try:
        o = subprocess.Popen(('bzr','version-info', '--python'), stdout=subprocess.PIPE).stdout
        f = open('VMBuilder/vcsversion.py', 'w')
        f.write(o.read())
        f.close()
        o.close()
    except Exception, e:
        print repr(e)

setup(name='VMBuilder',
      version='0.12.4',
      description='Uncomplicated VM Builder',
      author='Soren Hansen',
      author_email='soren@ubuntu.com',
      url='http://launchpad.net/vmbuilder/',
      packages=['VMBuilder', 'VMBuilder.tests', 'VMBuilder.plugins', 'VMBuilder.contrib'] + VMBuilder.plugins.find_plugins(),
      data_files=[('/etc/vmbuilder/%s' % (pkg,), glob('VMBuilder/plugins/%s/templates/*' % (pkg,))) for pkg in [p.split('.')[-1] for p in VMBuilder.plugins.find_plugins()]],
      scripts=['vmbuilder'],
      )
