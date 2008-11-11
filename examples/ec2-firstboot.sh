#!/bin/bash

#
# Regenerate the ssh host key
#

rm -f /etc/ssh/ssh_host_*_key*

ssh-keygen -f /etc/ssh/ssh_host_rsa_key -t rsa -N '' | logger -s -t "ec2"
ssh-keygen -f /etc/ssh/ssh_host_dsa_key -t dsa -N '' | logger -s -t "ec2"

# This allows user to get host keys securely through console log
echo "-----BEGIN SSH HOST KEY FINGERPRINTS-----" | logger -s -t "ec2"
ssh-keygen -l -f /etc/ssh/ssh_host_rsa_key.pub | logger -s -t "ec2"
ssh-keygen -l -f /etc/ssh/ssh_host_dsa_key.pub | logger -s -t "ec2"
echo "-----END SSH HOST KEY FINGERPRINTS-----" | logger -s -t "ec2"

depmod -a

exit 0
