#!/bin/sh

set -e

BASEDIR="${BASEDIR:-$(dirname -- "${0}")/..}"
BASEDIR="$(readlink -f -- ${BASEDIR})"

. ${BASEDIR}/functions

echo "+++ hosts orig +++"
cat /etc/hosts
echo "--- hosts orig ---"
IPV6_DIS="`cat /proc/sys/net/ipv6/conf/all/disable_ipv6`"
if [ ! "${IPV6_DIS}" -eq 0 ]
then
  ${SUDO} sh -c 'echo 0 > /proc/sys/net/ipv6/conf/all/disable_ipv6'
fi
${SUDO} sh -c 'echo >> /etc/hosts; grep "^127.0.0.1" /etc/hosts | sed "s|^127.0.0.1|::1|g" >> /etc/hosts'
echo "+++ hosts patched +++"
cat /etc/hosts
echo "--- hosts patched ---"
ulimit -c unlimited
${SUDO} sh -c "echo '/tmp/core.%p.%E' > /proc/sys/kernel/core_pattern"
#${BASEDIR}/cibits/ppa_clean.sh
${SUDO} env DEBIAN_FRONTEND=noninteractive apt-get update
${SUDO} env DEBIAN_FRONTEND=noninteractive apt-get install -y gpp gdb tcpdump
if [ -e requirements.txt ]
then
  ${SUDO} ${PYTHON_CMD} -m pip install -r requirements.txt
fi
sh -x ./install_depends/opensips.sh
