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

class EC2(Plugin):
    name = 'EC2 integration'

    def register_options(self):
        group = self.vm.setting_group('EC2 integation')
        group.add_option('--ec2', action='store_true', help='Build for EC2')
	group.add_option('--ec2-name', metavar='EC2_NAME', help='Name for the EC2 instance')
        group.add_option('--ec2-cert', metavar='CERTFILE', help='PEM encoded public certificate for EC2')
        group.add_option('--ec2-key', metavar='KEYFILE', help='PEM encoded private key for EC2')
        group.add_option('--ec2-user', metavar='AWS_ACCOUNT', help='EC2 user ID (a.k.a. AWS account number, not AWS access key ID)')
        group.add_option('--ec2-bucket', metavar='BUCKET', help='S3 bucket to hold the AMI')
        group.add_option('--ec2-access-key', metavar='ACCESS_ID', help='AWS access key ID')
        group.add_option('--ec2-secret-key', metavar='SECRET_ID', help='AWS secret access key')
	group.add_option('--ec2-kernel', metavar='EC2_KERNEL', help='EC2 AKI to use')
	group.add_option('--ec2-ramdisk', metavar='EC2_RAMDISK', help='EC2 ARI to use')
        self.vm.register_setting_group(group)

    def preflight_check(self):
        if not self.vm.ec2:
            return True

	if not self.vm.ec2_name:
	   raise VMBuilderUserError('When building for EC2 you must supply the name for the instance.')
        
        if not self.vm.ec2_cert:
            raise VMBuilderUserError('When building for EC2 you must provide your PEM encoded public key certificate using the --ec2-cert option')

        if not self.vm.ec2_key:
            raise VMBuilderUserError('When building for EC2 you must provide your PEM encoded private key file the --ec2-key option')

        if not self.vm.ec2_user:
            raise VMBuilderUserError('When building for EC2 you must provide your EC2 user ID (your AWS account number, not your AWS access key ID)')

	if not self.vm.ec2_kernel:
	    raise VMBuilderUserError('When building for EC2 you must provide the AKI')

	if not self.vm.ec2_ramdisk:
	    raise VMBuilderUserError('When building for Ec2 you must provide the ARI')

        if not self.vm.addpkg:
             self.vm.addpkg = []

        self.vm.addpkg += ['ec2-init']

    def deploy(self):
        if not self.vm.ec2:
            return False
        bundle_cmdline = ['ec2-bundle-image', '--image', self.vm.filesystems[0].filename, '--cert', self.vm.ec2_cert, '--privatekey', self.vm.ec2_key, '--user', self.vm.ec2_user, '--prefix', self.vm.ec2_name, '-r', ['i386', 'x86_64'][self.vm.arch == 'amd64'], '-d', self.vm.workdir, '--kernel', self.vm.ec2_kernel, '--ramdisk', self.vm.ec2_ramdisk]

        run_cmd(*bundle_cmdline)

        upload_cmdline = ['ec2-upload-bundle', '--manifest', '%s/%s.manifest.xml' % (self.vm.workdir, self.vm.ec2_name), '--bucket', self.vm.ec2_bucket, '--access-key', self.vm.ec2_access_key, '--secret-key', self.vm.ec2_secret_key]
        run_cmd(*upload_cmdline)

        from boto.ec2.connection import EC2Connection
        conn = EC2Connection(self.vm.ec2_access_key, self.vm.ec2_secret_key)
        print conn.register_image('%s/%s.manifest.xml' % (self.vm.ec2_bucket, self.vm.ec2_name))

        return True

register_plugin(EC2)
