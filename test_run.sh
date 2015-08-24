#!/bin/sh

set -e

uname -a

. $(dirname $0)/functions

${CC} --version

rtpproxy_cmds_gen() {
  sleep ${RTPP_STAT_TIMEOUT}
  cat "${BUILDDIR}/rtpproxy.stats.input"
}

start_mm() {
  if [ -e "${MM_PIDF}" ]
  then
    rm "${MM_PIDF}"
  fi
  case "${MM_TYPE}" in
  b2bua)
    ${BUILDDIR}/dist/b2bua/sippy/b2bua_test.py --sip_address=127.0.0.1 \
     --sip_port=5060 --foreground=on --acct_enable=off --auth_enable=off --static_route="127.0.0.1:5062" \
     --b2bua_socket="${MM_SOCK}" --rtp_proxy_clients="${RTPP_SOCK_TEST}" \
     --logfile="${BUILDDIR}/b2bua.log" &
    MM_PID=${!}
    ;;

  opensips)
    OPENSIPS_VER=`echo ${MM_BRANCH} | sed 's|[.]||g'`
    cpp -DRTPP_SOCK_TEST=\"${RTPP_SOCK_TEST}\" -DOPENSIPS_VER=${OPENSIPS_VER} \
      opensips.cfg.in > opensips.cfg
    ./dist/opensips/opensips -f opensips.cfg -C
    ./dist/opensips/opensips -f opensips.cfg -D &
    MM_PID=${!}
    ;;

  kamailio)
    sed "s|%%RTPP_SOCK_TEST%%|${RTPP_SOCK_TEST}|" < kamailio.cfg.in > kamailio.cfg
    ./dist/kamailio/kamailio -f kamailio.cfg -D &
    MM_PID=${!}
    ;;

  *)
    echo "Unknown MM_TYPE: ${MM_TYPE}" 1>&2
    return 1
  esac

  echo ${MM_PID} > "${MM_PIDF}"
  sleep ${MM_INIT_DELAY}
  return 0
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

if [ "${MM_SOCK}" != "" ]
then
  RTPP_NOTIFY_ARG="-n ${MM_SOCK} -W 45"
fi

if [ -e "${RTPP_SOCK_BARE}" ]
then
  rm "${RTPP_SOCK_BARE}"
fi

SIPLOG_TSTART="`python -c 'from time import time; print(time());'`"
export SIPLOG_TSTART
SIPLOG_TFORM="rel"
export SIPLOG_TFORM

rtpproxy_cmds_gen | ${RTPPROXY} -p "${RTPP_PIDF}" -d info -f -s stdio: -s "${RTPP_SOCK_UDP}" \
  -s "${RTPP_SOCK_CUNIX}" -s "${RTPP_SOCK_UNIX}" -s "${RTPP_SOCK_UDP6}" -s "${RTPP_SOCK_TCP}" \
  -s "${RTPP_SOCK_TCP6}" -m 12000 -M 15000 ${RTPP_NOTIFY_ARG} > rtpproxy.rout 2>rtpproxy.log &
RTPP_PID=${!}
i=0
while [ ! -e "${RTPP_SOCK_BARE}" ]
do
  if [ ${i} -gt 5 ]
  then
    fail_rd 1 "Waiting for the RTPproxy to become ready"
  fi
  sleep 1
  i=$((${i} + 1))
done
start_mm
python alice.py -t "${TEST_SET}" -l 127.0.0.1 -P 5061 -T ${ALICE_TIMEOUT} 2>alice.log &
ALICE_PID=${!}
echo "${ALICE_PID}" > "${ALICE_PIDF}"
python bob.py -l 127.0.0.1 -P 5062 -T ${BOB_TIMEOUT} 2>bob.log &
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
if [ ${ALICE_RC} -eq 0 -a ${BOB_RC} -eq 0 -a ${MM_RC} -eq 0 ]
then
  # Always give the RTPproxy enough time to execute final stats command,
  # before we SIGHUP it
  python -c "from time import time, sleep; tleft=${SIPLOG_TSTART} + ${RTPP_STAT_TIMEOUT} + 5 - time(); sleep(tleft) if tleft > 0 else False;"
fi
kill -HUP ${RTPP_PID}
echo "RTPP_PID: ${RTPP_PID}"
wait ${RTPP_PID}
RTPP_RC="${?}"

rm -f "${ALICE_PIDF}" "${BOB_PIDF}"

diff -u rtpproxy.${MM_TYPE}.output rtpproxy.rout
RTPP_CHECK_RC="${?}"

report_rc_log "${ALICE_RC}" "alice.log bob.log rtpproxy.log" "Checking if Alice is happy"
report_rc_log "${BOB_RC}" "bob.log alice.log rtpproxy.log" "Checking if Bob is happy"
report_rc_log "${RTPP_RC}" rtpproxy.log "Checking RTPproxy exit code"
report_rc "${MM_RC}" "Checking ${MM_TYPE} exit code"
report_rc_log "${RTPP_CHECK_RC}" rtpproxy.log "Checking RTPproxy stdout"
