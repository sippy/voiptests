#!/bin/sh

set -e

BASEDIR="${BASEDIR:-$(dirname -- "${0}")/..}"
BASEDIR="$(readlink -f -- ${BASEDIR})"

. ${BASEDIR}/functions

echo "+++ hosts orig +++"
cat /etc/hosts
echo "--- hosts orig ---"
sudo sh -c 'echo 0 > /proc/sys/net/ipv6/conf/all/disable_ipv6'
sudo sh -c 'echo >> /etc/hosts; grep "^127.0.0.1" /etc/hosts | sed "s|^127.0.0.1|::1|g" >> /etc/hosts'
echo "+++ hosts patched +++"
cat /etc/hosts
echo "--- hosts patched ---"
ulimit -c unlimited
sudo sh -c "echo '/tmp/core.%p.%E' > /proc/sys/kernel/core_pattern"
sudo -H DEBIAN_FRONTEND=noninteractive apt-get update
sudo -H DEBIAN_FRONTEND=noninteractive apt-get install -y gpp gdb
if [ -e requirements.txt ]
then
  sudo ${PYTHON_CMD} -m pip install -r requirements.txt
fi
sh -x ./install_depends/opensips.sh
