from distutils.core import setup
import VMBuilder.plugins
from glob import glob

setup(name='VMBuilder',
      version='0.9',
      description='Uncomplicated VM Builder',
      author='Soren Hansen',
      author_email='soren@canonical.com',
      url='http://launchpad.net/vmbuilder/',
      packages=['VMBuilder', 'VMBuilder.plugins'] + VMBuilder.plugins.find_plugins(),
      data_files=[('/etc/vmbuilder/%s' % (pkg,), glob('VMBuilder/plugins/%s/templates/*' % (pkg,))) for pkg in [p.split('.')[-1] for p in VMBuilder.plugins.find_plugins()]],
      scripts=['vmbuilder'], 
      )
