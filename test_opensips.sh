#!/bin/sh

set -e

uname -a

. $(dirname $0)/functions

${CC} --version

rtpproxy_cmds_gen() {
  sleep 30
  echo "G nsess_created nsess_destroyed nsess_complete nsess_nortp nsess_owrtp nsess_nortcp nsess_owrtcp ncmds_rcvd ncmds_succd ncmds_errs ncmds_repld"
}

#"${BUILDDIR}/install_depends/opensips.sh"

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

set +e

wait ${ALICE_PID}
ALICE_RC="${?}"
wait ${BOB_PID}
BOB_RC="${?}"
kill -TERM ${OPENSIPS_PID}
echo "OPENSIPS_PID: ${OPENSIPS_PID}"
wait ${OPENSIPS_PID}
OPENSIPS_RC="${?}"
kill -HUP ${RTPP_PID}
echo "RTPP_PID: ${RTPP_PID}"
wait ${RTPP_PID}
RTPP_RC="${?}"

rm -f "${ALICE_PIDF}" "${BOB_PIDF}"

diff -u rtpproxy.rout rtpproxy.output
RTPP_CHECK_RC="${?}"
report_rc "${ALICE_RC}" "Checking if Alice is happy"
report_rc "${BOB_RC}" "Checking if Bob is happy"
report_rc "${RTPP_RC}" "Checking RTPproxy exit code"
report_rc "${OPENSIPS_RC}" "Checking OpenSIPS exit code"
report_rc "${RTPP_CHECK_RC}" "Checking RTPproxy stdout"
