#!/bin/bash

trap cleanup 1 2 3 6

cleanup() {
   exit 1
}

ACCOUNT="ubuntu"

echo
echo "======================================================"
echo "CONFIGURATION OF YOUR UBUNTU EC2 IMAGE"
echo "======================================================"
echo "Your EC2 image is about to be finished to be set up."
echo
echo "------------------------------------------------------"

PASSWORD=$(uuidgen -r | head -c8)

echo "New password for ${ACCOUNT} account: ${PASSWORD}"
echo "ubuntu:${PASSWORD}" | chpasswd -m
passwd -u ${ACCOUNT}

echo "Setting up ssh public keys for the ${ACCOUNT} account."
[ ! -e /home/${ACCOUNT}/.ssh ] && mkdir -p /home/${ACCOUNT}/.ssh
cp -a /root/.ssh/authorized_keys* /home/${ACCOUNT}/.ssh
chown -R ${ACCOUNT}:${ACCOUNT} /home/${ACCOUNT}/.ssh

echo
echo "------------------------------------------------------"
echo "Please select software that you wish to install:"

tasksel --section server

echo
echo "------------------------------------------------------"
echo
echo "We are now going to log you out of the root account."
echo "To perform administrative tasks please use the ${ACCOUNT} account"
echo "in combination with sudo using the password: ${PASSWORD}"
echo
echo "======================================================"
echo

touch /root/firstlogin_done

kill -HUP $PPID

