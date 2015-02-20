#!/bin/sh

set -e

uname -a

. $(dirname $0)/functions

${CC} --version

rtpproxy_cmds_gen() {
  sleep 30
  echo "Gv nsess_created nsess_destroyed nsess_complete nsess_nortp nsess_owrtp nsess_nortcp nsess_owrtcp ncmds_rcvd ncmds_succd ncmds_errs ncmds_repld"
}

start_mm() {
  if [ "${MM_TYPE}" = "b2bua" ]
  then
    ${BUILDDIR}/dist/b2bua/sippy/b2bua_test.py --sip_address=127.0.0.1 \
      --sip_port=5060 --foreground=on --acct_enable=off --auth_enable=off --static_route="127.0.0.1:5062" \
      --b2bua_socket="/tmp/b2bua.sock" --rtp_proxy_clients="${RTPP_SOCK_TEST}" &
    MM_PID=${!}
    echo "${MM_PID}" > "${MM_PIDF}"
  else
    sed "s|%%RTPP_SOCK_TEST%%|${RTPP_SOCK_TEST}|" < opensips.cfg.in > opensips.cfg
    ./dist/opensips/opensips -f opensips.cfg -D -P "${MM_PIDF}" &
    MM_PID=${!}
  fi
}  

#"${BUILDDIR}/install_depends/opensips.sh"

RTPP_PIDF="${BUILDDIR}/rtpproxy.pid"
MM_PIDF="${BUILDDIR}/opensips.pid"
ALICE_PIDF="${BUILDDIR}/alice.pid"
BOB_PIDF="${BUILDDIR}/bob.pid"

cd ${BUILDDIR}

for pidf in "${RTPP_PIDF}" "${MM_PIDF}" "${ALICE_PIDF}" "${BOB_PIDF}"
do
  if [ ! -e "${pidf}" ]
  then
    continue
  fi
  pid=`cat ${pidf}`
  kill -TERM "${pid}" || true
done

rtpproxy_cmds_gen | ${RTPPROXY} -p "${RTPP_PIDF}" -d info -f -s stdio: -s "${RTPP_SOCK_UDP}" \
  -s "${RTPP_SOCK_CUNIX}" -s "${RTPP_SOCK_UNIX}" > rtpproxy.rout &
RTPP_PID=${!}
start_mm
echo "${MM_PID}" > "${MM_PIDF}"
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
kill -TERM ${MM_PID}
echo "MM_PID: ${MM_PID}"
wait ${MM_PID}
MM_RC="${?}"
kill -HUP ${RTPP_PID}
echo "RTPP_PID: ${RTPP_PID}"
wait ${RTPP_PID}
RTPP_RC="${?}"

rm -f "${ALICE_PIDF}" "${BOB_PIDF}"

diff -u rtpproxy.rout rtpproxy.${MM_TYPE}.output
RTPP_CHECK_RC="${?}"

report_rc "${ALICE_RC}" "Checking if Alice is happy"
report_rc "${BOB_RC}" "Checking if Bob is happy"
report_rc "${RTPP_RC}" "Checking RTPproxy exit code"
report_rc "${MM_RC}" "Checking ${MM_TYPE} exit code"
report_rc "${RTPP_CHECK_RC}" "Checking RTPproxy stdout"
