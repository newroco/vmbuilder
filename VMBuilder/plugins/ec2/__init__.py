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
from VMBuilder import register_plugin, Plugin, VMBuilderUserError
from VMBuilder.util import run_cmd
import logging
import os

class EC2(Plugin):
    name = 'EC2 integration'

    def register_options(self):
        group = self.vm.setting_group('EC2 integation')
        group.add_option('--ec2', action='store_true', help='Build for EC2')
        group.add_option('--ec2-name','--ec2-prefix', metavar='EC2_NAME', help='Name for the EC2 image.')
        group.add_option('--ec2-cert', metavar='CERTFILE', help='PEM encoded public certificate for EC2.')
        group.add_option('--ec2-key', metavar='KEYFILE', help='PEM encoded private key for EC2.')
        group.add_option('--ec2-user', metavar='AWS_ACCOUNT', help='EC2 user ID (a.k.a. AWS account number, not AWS access key ID).')
        group.add_option('--ec2-bucket', metavar='BUCKET', help='S3 bucket to hold the AMI.')
        group.add_option('--ec2-access-key', metavar='ACCESS_ID', help='AWS access key ID.')
        group.add_option('--ec2-secret-key', metavar='SECRET_ID', help='AWS secret access key.')
        group.add_option('--ec2-kernel','--ec2-aki', metavar='AKI', help='EC2 AKI (kernel) to use.')
        group.add_option('--ec2-ramdisk','--ec2-ari', metavar='ARI', help='EC2 ARI (ramdisk) to use.')
        self.vm.register_setting_group(group)

    def preflight_check(self):
        if not self.vm.ec2:
            return True

        if not self.vm.hypervisor.name == 'Xen':
            raise VMBuilderUserError('When building for EC2 you must use the xen hypervisor.')

        if not self.vm.ec2_name:
            raise VMBuilderUserError('When building for EC2 you must supply the name for the image.')

        if not self.vm.ec2_cert:
            if "EC2_CERT" in os.environ:
                self.vm.ec2_cert = os.environ["EC2_CERT"]
            else:
                raise VMBuilderUserError('When building for EC2 you must provide your PEM encoded public key certificate')

        if not self.vm.ec2_key:
            if "EC2_PRIVATE_KEY" in os.environ:
                self.vm.ec2_key = os.environ["EC2_PRIVATE_KEY"]
            else:
                raise VMBuilderUserError('When building for EC2 you must provide your PEM encoded private key file')

        if not self.vm.ec2_user:
            raise VMBuilderUserError('When building for EC2 you must provide your EC2 user ID (your AWS account number, not your AWS access key ID)')

        if not self.vm.ec2_kernel:
            logging.debug('No ec2-aki choosen setting to default. Use --ec2-kernel to change this')
            if self.vm.arch == 'amd64':
                self.vm.ec2_kernel = 'aki-d314f0ba'
            else:
                self.vm.ec2_kernel = 'aki-af14f0c6'

        if not self.vm.ec2_ramdisk:
            logging.debug('No ec2-ari choosen setting to default. Use --ec2-ramdisk to change this.')
            if self.vm.arch == 'amd64':
                self.vm.ec2_ramdisk = 'ari-d014f0b9'
            else:
                self.vm.ec2_ramdisk = 'ari-ac14f0c5'

        if not self.vm.ec2_bucket:
            raise VMBuilderUserError('When building for EC2 you must provide an S3 bucket to hold the AMI')

        if not self.vm.ec2_access_key:
            raise VMBuilderUserError('When building for EC2 you must provide your AWS access key ID.')

        if not self.vm.ec2_secret_key:
            raise VMBuilderUserError('When building for EC2 you must provide your AWS secret access key.')


        if not self.vm.addpkg:
             self.vm.addpkg = []

        self.vm.addpkg += ['openssh-server']
        self.vm.addpkg += ['ec2-init']
        self.vm.addpkg += ['openssh-server']
        self.vm.addpkg += ['ec2-modules']
        self.vm.addpkg += ['server^']
        self.vm.addpkg += ['standard^']

        if not self.vm.ppa:
            self.vm.ppa = []

        self.vm.ppa += ['ubuntu-ec2']

    def post_install(self):
        if not self.vm.ec2:
            return

        logging.info("Running ec2 postinstall")
        self.install_from_template('/etc/event.d/xvc0', 'upstart')
        self.run_in_target('passwd', '-l', self.vm.user)

    def deploy(self):
        if not self.vm.ec2:
            return False

        logging.info("Building EC2 bundle")
        bundle_cmdline = ['ec2-bundle-image', '--image', self.vm.filesystems[0].filename, '--cert', self.vm.ec2_cert, '--privatekey', self.vm.ec2_key, '--user', self.vm.ec2_user, '--prefix', self.vm.ec2_name, '-r', ['i386', 'x86_64'][self.vm.arch == 'amd64'], '-d', self.vm.workdir, '--kernel', self.vm.ec2_kernel, '--ramdisk', self.vm.ec2_ramdisk]

        run_cmd(*bundle_cmdline)

        logging.info("Uploading EC2 bundle")
        upload_cmdline = ['ec2-upload-bundle', '--retry', '--manifest', '%s/%s.manifest.xml' % (self.vm.workdir, self.vm.ec2_name), '--bucket', self.vm.ec2_bucket, '--access-key', self.vm.ec2_access_key, '--secret-key', self.vm.ec2_secret_key]
        run_cmd(*upload_cmdline)

        from boto.ec2.connection import EC2Connection
        conn = EC2Connection(self.vm.ec2_access_key, self.vm.ec2_secret_key)
        print conn.register_image('%s/%s.manifest.xml' % (self.vm.ec2_bucket, self.vm.ec2_name))

        return True

register_plugin(EC2)
