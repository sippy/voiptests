#!/bin/sh

set -e

echo "+++ hosts orig +++"
cat /etc/hosts
echo "--- hosts orig ---"
sudo sh -c 'echo 0 > /proc/sys/net/ipv6/conf/all/disable_ipv6'
sudo sh -c 'echo >> /etc/hosts; grep "^127.0.0.1" /etc/hosts | sed "s|^127.0.0.1|::1|g" >> /etc/hosts'
echo "+++ hosts patched +++"
cat /etc/hosts
echo "--- hosts patched ---"
sudo -H DEBIAN_FRONTEND=noninteractive apt-get update
sudo -H DEBIAN_FRONTEND=noninteractive apt-get install gpp
sh -x ./install_depends/opensips.sh
