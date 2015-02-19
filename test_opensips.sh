#!/bin/sh

set -e

. $(dirname $0)/functions

rtpproxy_cmds_gen() {
  sleep 30
  echo "G nsess_created nsess_destroyed nsess_complete nsess_nortp nsess_owrtp nsess_nortcp nsess_owrtcp ncmds_rcvd ncmds_succd ncmds_errs ncmds_repld"
}

if [ -e "${BUILDDIR}/dist" ]
then
  rm -rf "${BUILDDIR}/dist"
fi
mkdir "${BUILDDIR}/dist"
cd "${BUILDDIR}/dist"

git clone -b 1.10 git@github.com:OpenSIPS/opensips.git
git clone git@github.com:sippy/b2bua.git
git clone git@github.com:sippy/rtpproxy.git

perl -pi -e 's|-O[3-9]|-O0 -g3|' ${BUILDDIR}/dist/opensips/Makefile.defs
##bash
gmake -C "${BUILDDIR}/dist/opensips" CC_NAME=gcc CC="${CC}" all modules
cd rtpproxy
./configure
make all

RTPP_PIDF="${BUILDDIR}/rtpproxy.pid"
OPSPS_PIDF="${BUILDDIR}/opensips.pid"
ALICE_PIDF="${BUILDDIR}/alice.pid"
BOB_PIDF="${BUILDDIR}/bob.pid"

cd ${BUILDDIR}

for pidf in "${RTPP_PIDF}" "${OPSPS_PIDF}" "${ALICE_PIDF}" "${BOB_PIDF}"
do
  if [ ! -e "${pidf}" ]
  then
    continue
  fi
  pid=`cat ${pidf}`
  kill -TERM "${pid}" || true
done

rtpproxy_cmds_gen | ${RTPPROXY} -p "${RTPP_PIDF}" -d info -f -s stdio: -s udp:127.0.0.1:22222 -s cunix:/tmp/rtpproxy.csock -s unix:/tmp/rtpproxy.sock > rtpproxy.rout &
RTPP_PID=${!}
./dist/opensips/opensips -f opensips.cfg -D -P "${OPSPS_PIDF}" &
OPENSIPS_PID=${!}
python alice.py 127.0.0.1 5061 &
ALICE_PID=${!}
echo "${ALICE_PID}" > "${ALICE_PIDF}"
python bob.py 127.0.0.1 5062 &
BOB_PID=${!}
echo "${BOB_PID}" > "${BOB_PIDF}"
wait ${ALICE_PID}
wait ${BOB_PID}
kill -HUP ${RTPP_PID}
echo "RTPP_PID: ${RTPP_PID}"
wait ${RTPP_PID}
kill -TERM ${OPENSIPS_PID}
echo "OPENSIPS_PID: ${OPENSIPS_PID}"
wait ${OPENSIPS_PID}

rm -f "${ALICE_PIDF}" "${BOB_PIDF}"

diff -u rtpproxy.rout rtpproxy.output
