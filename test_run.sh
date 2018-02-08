#!/bin/sh

set -e

uname -a

. $(dirname $0)/functions

${CC} --version

rtpproxy_cmds_gen() {
  if [ x"${RTPP_PRE_STAT_TIMEOUT}" != x"" ]
  then
    sleep ${RTPP_PRE_STAT_TIMEOUT}
    cat "${BUILDDIR}/rtpproxy.stats.input"
    RTPP_STAT_TIMEOUT=$((${RTPP_STAT_TIMEOUT} - ${RTPP_PRE_STAT_TIMEOUT}))
  fi
  sleep ${RTPP_STAT_TIMEOUT}
  cat "${BUILDDIR}/rtpproxy.stats.input"
}

start_mm() {
  if [ -e "${MM_PIDF}" ]
  then
    rm "${MM_PIDF}"
  fi
  MM_CFG=""
  case "${MM_TYPE}" in
  go-b2bua)
    MM_LOG="${BUILDDIR}/b2bua.log"
    MM_SIPLOG="${BUILDDIR}/sip.log"
    test -e ${MM_SIPLOG} && rm ${MM_SIPLOG}
    ${BUILDDIR}/dist/go-b2bua/b2bua_radius/b2bua_radius -L ${MM_SIPLOG} \
        -static_route="localhost:5062;ash=SIP-Hello1%3A%20World%21;ash=SIP-Hello2%3A%20World%21" \
        -rtp_proxy_clients="${RTPP_SOCK_TEST}" -b2bua_socket="${MM_SOCK}" -rtpp_hrtb_ival=120 \
        -rtpp_hrtb_retr_ival=120 >${MM_LOG} 2>&1 &
    MM_PID=${!}
    ALICE_ARGS="-46"
    ;;
  b2bua)
    MM_LOG="${BUILDDIR}/b2bua.log"
    if [ -e ${MM_LOG} ]
    then
      rm ${MM_LOG}
    fi
    SIPLOG_LOGFILE_FILE="${MM_LOG}" SIPLOG_BEND="file" \
     ${BUILDDIR}/dist/b2bua/sippy/b2bua_test.py --sip_address='*' \
     --sip_port=5060 --foreground=on --acct_enable=off --auth_enable=off \
     --static_route="localhost:5062;ash=SIP-Hello1%3A%20World%21;ash=SIP-Hello2%3A%20World%21" \
     --b2bua_socket="${MM_SOCK}" --rtp_proxy_clients="${RTPP_SOCK_TEST}" \
     --logfile="${MM_LOG}" &
    MM_PID=${!}
    ALICE_ARGS="-46"
    ;;

  opensips)
    MM_CFG="opensips.cfg"
    for file in "${MM_CFG}.in" rtpproxy.opensips.output.in
    do
      ${PP_CMD} -DRTPP_SOCK_TEST=\"${RTPP_SOCK_TEST}\" -DOPENSIPS_VER=${MM_VER} \
       -DOPENSIPS_VER_FULL=${MM_VER_FULL} "${file}" | grep -v '^#' | \
       cat -s > "${file%.in}"
    done
    set +e
    ${BUILDDIR}/dist/opensips/opensips -f "${MM_CFG}" -C
    MM_DRUN_RC="${?}"
    report_rc_log "${MM_DRUN_RC}" "${MM_CFG}" "Checking ${MM_TYPE} config"
    set -e
    ${BUILDDIR}/dist/opensips/opensips -f "${MM_CFG}" ${MM_ARGS} -F -E -n 1 &
    MM_PID=${!}
    ALICE_ARGS="-46"
    ;;

  kamailio)
    MM_CFG="kamailio.cfg"
    if [ "${MM_BRANCH}" != "master" -a ${MM_VER_FULL} -lt 50 ]
    then
      KROOT="${BUILDDIR}/dist/kamailio"
    else
      KROOT="${BUILDDIR}/dist/kamailio/src"
      KOPTS="-Y /tmp"
    fi
    KBIN="${KROOT}/kamailio"
    KAM_MPATH="${KROOT}/modules/"
    for file in "${MM_CFG}.in" rtpproxy.kamailio.output.in
    do
      ${PP_CMD} -DRTPP_SOCK_TEST=\"${RTPP_SOCK_TEST}\" -DKAMAILIO_VER=${MM_VER} \
       -DKAMAILIO_VER_FULL=${MM_VER_FULL} -DKAM_MPATH=\"${KAM_MPATH}\" \
       "${file}" | cat -s | grep -v '^#' | cat -s > "${file%.in}"
    done
    #sed "s|%%RTPP_SOCK_TEST%%|${RTPP_SOCK_TEST}|" < kamailio.cfg.in > kamailio.cfg
    set +e
    "${KBIN}" ${KOPTS} -f "${MM_CFG}" -c
    MM_DRUN_RC="${?}"
    report_rc_log "${MM_DRUN_RC}" "${MM_CFG}" "Checking ${MM_TYPE} config"
    set -e
    "${KBIN}" ${KOPTS} -f "${MM_CFG}" -DD -E -n 1 &
    MM_PID=${!}
    ALICE_ARGS="-46"
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

if [ x"${MM_SOCK}" != x"" ]
then
  RTPP_NOTIFY_ARG="-n ${MM_SOCK} -W 45"
fi

if [ -e "${RTPP_SOCK_BARE}" ]
then
  rm "${RTPP_SOCK_BARE}"
fi

MR_TIME="`python ${RTPPROXY_DIST}/python/sippy_lite/sippy/tools/getmonotime.py -S ${RTPPROXY_DIST}/python/sippy_lite -r`"
SIPLOG_TSTART="`echo ${MR_TIME} | awk '{print $2}'`"
export SIPLOG_TSTART
SIPLOG_TFORM="rel"
export SIPLOG_TFORM
RTPP_LOG_TSTART="`echo ${MR_TIME} | awk '{print $1}'`"
export RTPP_LOG_TSTART
RTPP_LOG_TFORM="rel"
export RTPP_LOG_TFORM

rtpproxy_cmds_gen | ${RTPPROXY} -p "${RTPP_PIDF}" -d dbug -f -s stdio: -s "${RTPP_SOCK_UDP}" \
  -s "${RTPP_SOCK_CUNIX}" -s "${RTPP_SOCK_UNIX}" -s "${RTPP_SOCK_UDP6}" -s "${RTPP_SOCK_TCP}" \
  -s "${RTPP_SOCK_TCP6}" -m 12000 -M 15000 -6 '/::' -l '0.0.0.0' ${RTPP_NOTIFY_ARG} > rtpproxy.rout 2>rtpproxy.log &
RTPP_PID=${!}
sleep 1
i=0
while [ ! -e "${RTPP_SOCK_BARE}" ]
do
  if [ ${i} -gt 4 ]
  then
    report_rc_log 1 "rtpproxy.rout rtpproxy.log" "Waiting for the RTPproxy to become ready"
  fi
  sleep 1
  i=$((${i} + 1))
done
start_mm
python alice.py "${ALICE_ARGS}" -t "${TEST_SET}" -l '*' -P 5061 \
 -T ${ALICE_TIMEOUT} 2>alice.log &
ALICE_PID=${!}
echo "${ALICE_PID}" > "${ALICE_PIDF}"
python bob.py -l '*' -P 5062 -T ${BOB_TIMEOUT} 2>bob.log &
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

diff -uB rtpproxy.${MM_TYPE}.output rtpproxy.rout
RTPP_CHECK_RC="${?}"

report_rc_log "${ALICE_RC}" "${MM_CFG} alice.log bob.log rtpproxy.log" "Checking if Alice is happy"
report_rc_log "${BOB_RC}" "${MM_CFG} bob.log alice.log rtpproxy.log" "Checking if Bob is happy"
report_rc_log "${RTPP_RC}" "${MM_CFG} rtpproxy.log" "Checking RTPproxy exit code"
if [ x"${MM_LOG}" != x"" ]
then
  report_rc_log "${MM_RC}" "${MM_LOG}" "Checking ${MM_TYPE} exit code"
else
  report_rc "${MM_RC}" "Checking ${MM_TYPE} exit code"
fi
report_rc_log "${RTPP_CHECK_RC}" rtpproxy.log "Checking RTPproxy stdout"
