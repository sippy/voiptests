#!/bin/sh

set -e

uname -a
echo "/proc/sys/kernel/core_pattern: "`cat /proc/sys/kernel/core_pattern`
ulimit -c
getent --version | head -n 1
if ! getent ahosts ::
then
  echo "WARNING: IPv6 is broken!" >&2
fi

. $(dirname $0)/functions

if [ ! -z "`which ${CC}`" ]
then
  ${CC} --version
fi

PYTHON_CMD="${PYTHON_CMD:-"python"}"

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

pp_file() {
  file="${1}"
  fname="`basename ${file}`"
  shift
  ${PP_CMD} "${@}" "${file}" -o "${fname%.in}.pp"
  grep -v '^#' "${fname%.in}.pp" | cat -s > "${fname%.in}${PP_SUF}"
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
    test -e ${MM_LOG} && rm ${MM_LOG}
    ${MM_ROOT}/b2bua_radius -L ${MM_LOG} \
        -static_route="localhost:5062;ash=SIP-Hello1%3A%20World%21;ash=SIP-Hello2%3A%20World%21" \
        -rtp_proxy_clients="${RTPP_SOCK_TEST}" -b2bua_socket="${MM_SOCK}" -rtpp_hrtb_ival=120 \
        --allowed_pts="18,0,2,4,8,96,98,98,101" \
        -rtpp_hrtb_retr_ival=120 -u -acct_enable=0 -f >${MM_LOG} 2>&1 &
    MM_PID=${!}
    ;;
  b2bua)
    MM_LOG="${BUILDDIR}/b2bua.log"
    if [ -e ${MM_LOG} ]
    then
      rm ${MM_LOG}
    fi
    sed "s|%%SIPPY_ROOT%%|${MM_ROOT}|g" ${BUILDDIR}/install_depends/b2bua_radius.py.fix > \
      ${MM_ROOT}/sippy/b2bua_test.py
    chmod 755 ${MM_ROOT}/sippy/b2bua_test.py
    SIPLOG_LOGFILE_FILE="${MM_LOG}" SIPLOG_BEND="file" \
     ${PYTHON_CMD} ${MM_ROOT}/sippy/b2bua_test.py --sip_address='*' \
     --sip_port=5060 --foreground=on --acct_enable=off --auth_enable=off \
     --static_route="localhost:5062;ash=SIP-Hello1%3A%20World%21;ash=SIP-Hello2%3A%20World%21" \
     --b2bua_socket="${MM_SOCK}" --rtp_proxy_clients="${RTPP_SOCK_TEST}" \
     --allowed_pts="18,0,2,4,8,[G726-40/8000],[G726-24/8000],[G726-16/8000],[telephone-event/8000]" \
     --logfile="${MM_LOG}" &
    MM_PID=${!}
    ;;

  opensips)
    MM_CFG="opensips.cfg"
    MM_BIN="${MM_ROOT}/opensips"
    pp_file "scenarios/${MM_AUTH}/${MM_CFG}.in" -DRTPP_SOCK_TEST=\"${RTPP_SOCK_TEST}\" -DOPENSIPS_VER=${MM_VER} \
     -DOPENSIPS_VER_FULL=${MM_VER_FULL} -DMM_AUTH="${MM_AUTH}" -DMM_ROOT="${MM_ROOT}" \
     -DRTPPC_TYPE="${RTPPC_TYPE}" -DRTPP_LISTEN="${RTPP_LISTEN}"
    for nret in 0 1 2
    do
      PP_SUF=".nr${nret}" pp_file scenarios/${MM_AUTH}/rtpproxy.opensips.output.in -DOPENSIPS_VER=${MM_VER} \
       -DOPENSIPS_VER_FULL=${MM_VER_FULL} -DNRET=${nret}
    done
    set +e
    ${MM_BIN} -f "${MM_CFG}" -C
    MM_DRUN_RC="${?}"
    if [ ${MM_DRUN_RC} -gt 127 ]
    then
      apt install -y gdb
      gdb --batch -ex "run" -ex "bt" --args ${MM_BIN} -f "${MM_CFG}" -C
    fi
    report_rc_log "${MM_DRUN_RC}" "${MM_CFG}" "Checking ${MM_TYPE} config"
    set -e
    echo "--- Config Begins ---"
    cat -n "${MM_CFG}"
    echo "--- Config Ends ---"
    _MM_ARGS="-f ${MM_CFG} ${MM_ARGS} -F -n 1"
    if [ "${MM_BRANCH}" != "master" -a "${MM_VER}" -lt 30 ]
    then
      _MM_ARGS="${_MM_ARGS} -E"
    fi
    ${MM_BIN} ${_MM_ARGS} &
    MM_PID=${!}
    ;;

  kamailio)
    MM_CFG="kamailio.cfg"
    if [ "${MM_BRANCH}" != "master" -a ${MM_VER_FULL} -lt 50 ]
    then
      KROOT="${MM_ROOT}"
    else
      KROOT="${MM_ROOT}/src"
      KOPTS="-Y /tmp"
    fi
    KBIN="${KROOT}/kamailio"
    KAM_MPATH="${KROOT}/modules/"
    pp_file "${MM_CFG}.in" -DRTPP_SOCK_TEST=\"${RTPP_SOCK_TEST}\" -DKAMAILIO_VER=${MM_VER} \
     -DKAMAILIO_VER_FULL=${MM_VER_FULL} -DKAM_MPATH=\"${KAM_MPATH}\"
    for nret in 0 1 2
    do
      PP_SUF=".nr${nret}" pp_file scenarios/${MM_AUTH}/rtpproxy.kamailio.output.in -DKAMAILIO_VER=${MM_VER} \
       -DKAMAILIO_VER_FULL=${MM_VER_FULL} -DNRET=${nret}
    done
    #sed "s|%%RTPP_SOCK_TEST%%|${RTPP_SOCK_TEST}|" < kamailio.cfg.in > kamailio.cfg
    set +e
    "${KBIN}" ${KOPTS} -f "${MM_CFG}" -c
    MM_DRUN_RC="${?}"
    report_rc_log "${MM_DRUN_RC}" "${MM_CFG}" "Checking ${MM_TYPE} config"
    set -e
    "${KBIN}" ${KOPTS} -f "${MM_CFG}" -DD -E -n 1 &
    MM_PID=${!}
    ;;

  *)
    echo "Unknown MM_TYPE: ${MM_TYPE}" 1>&2
    return 1
  esac

  ALICE_ARGS="${ALICE_ARGS:-"-46"}"
  echo ${MM_PID} > "${MM_PIDF}"
  sleep ${MM_INIT_DELAY}
  return 0
}

#"${BUILDDIR}/install_depends/opensips.sh"

RTPP_PIDF="${BUILDDIR}/rtpproxy.pid"
MM_PIDF="${BUILDDIR}/sstua.pid"
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

GMTM="${RTPPROXY_DIST}/python/sippy_lite/sippy/tools/getmonotime.py"
if [ ! -e "${GMTM}" ]
then
  GMTM="${RTPPROXY_DIST}/python/tools/getmonotime.py"
else
  GMTM="${GMTM} -S ${RTPPROXY_DIST}/python/sippy_lite"
fi

MR_TIME="`${PYTHON_CMD} ${GMTM} -r`"
SIPLOG_TSTART="`echo ${MR_TIME} | awk '{print $2}'`"
export SIPLOG_TSTART
SIPLOG_TFORM="rel"
export SIPLOG_TFORM
RTPP_LOG_TSTART="`echo ${MR_TIME} | awk '{print $1}'`"
export RTPP_LOG_TSTART
RTPP_LOG_TFORM="rel"
export RTPP_LOG_TFORM

RTPP_LISTEN="-l 0.0.0.0"
if [ "${ALICE_ARGS}" != "-4" ]
then
  RTPP_LISTEN="${RTPP_LISTEN} -6 /::"
fi

if [ "${RTPPC_TYPE}" != "rtp.io" ]
then
  RTPP_ARGS="-p ${RTPP_PIDF} -d dbug -F -f -s stdio: -s ${RTPP_SOCK_UDP} \
    -s ${RTPP_SOCK_CUNIX} -s ${RTPP_SOCK_UNIX} -s ${RTPP_SOCK_TCP} \
    -m 12000 -M 15000 ${RTPP_LISTEN} ${RTPP_NOTIFY_ARG}"
  if [ "${RTPPC_TYPE}" = "udp6" ]
  then
    RTPP_ARGS="${RTPP_ARGS} -s ${RTPP_SOCK_UDP6}"
  fi
  if [ "${RTPPC_TYPE}" = "tcp6" ]
  then
    RTPP_ARGS="${RTPP_ARGS} -s ${RTPP_SOCK_TCP6}"
  fi
  rtpproxy_cmds_gen | ${RTPPROXY} ${RTPP_ARGS} > rtpproxy.rout 2>rtpproxy.log &
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
  sleep 1
fi

MM_AUTH="${MM_AUTH}" ${PYTHON_CMD} bob.py -l '*' -P 5062 -T ${BOB_TIMEOUT} 2>bob.log &
BOB_PID=${!}
echo "${BOB_PID}" > "${BOB_PIDF}"
start_mm
MM_AUTH="${MM_AUTH}" ${PYTHON_CMD} alice.py "${ALICE_ARGS}" -t "${TEST_SET}" -l '*' -P 5061 \
 -T ${ALICE_TIMEOUT} 2>alice.log &
ALICE_PID=${!}
echo "${ALICE_PID}" > "${ALICE_PIDF}"

set +e

wait ${ALICE_PID}
ALICE_RC="${?}"
wait ${BOB_PID}
BOB_RC="${?}"
if ! kill -TERM ${MM_PID}
then
  for corefile in `${SUDO} find /tmp/ -type f -name core\*`
  do
    gdb -batch --command=${BUILDDIR}/gdb.gettrace ${MM_BIN} ${corefile} >&2
  done
fi
echo "MM_PID: ${MM_PID}"
wait ${MM_PID}
MM_RC="${?}"
if [ ${ALICE_RC} -eq 0 -a ${BOB_RC} -eq 0 -a ${MM_RC} -eq 0 ]
then
  # Always give the RTPproxy enough time to execute final stats command,
  # before we SIGHUP it
  ${PYTHON_CMD} -c "from time import time, sleep; tleft=${SIPLOG_TSTART} + ${RTPP_STAT_TIMEOUT} + 5 - time(); sleep(tleft) if tleft > 0 else False;"
fi
if [ "${RTPPC_TYPE}" != "rtp.io" ]
then
  kill -HUP ${RTPP_PID}
  echo "RTPP_PID: ${RTPP_PID}"
  wait ${RTPP_PID}
  RTPP_RC="${?}"
else
  RTPP_RC=0
fi

rm -f "${ALICE_PIDF}" "${BOB_PIDF}"

if [ "${RTPPC_TYPE}" != "rtp.io" ]
then
  if [ "${MM_TYPE}" != "opensips" -a "${MM_TYPE}" != "kamailio" ]
  then
    RTPP_OUT="rtpproxy.${MM_TYPE}.output"
    if [ "${RTPP_VERSION}" != "debug" ]
    then
      grep -v "^MEMDEB" "${RTPP_OUT}" > "${RTPP_OUT}.pp"
      RTPP_OUT="${RTPP_OUT}.pp"
    fi
    diff -uB "${RTPP_OUT}" rtpproxy.rout
    RTPP_CHECK_RC="${?}"
  else
    for nret in 0 1 2
    do
      RTPP_OUT="rtpproxy.${MM_TYPE}.output.nr${nret}"
      if [ "${RTPP_VERSION}" != "debug" ]
      then
        grep -v "^MEMDEB" "${RTPP_OUT}" > "${RTPP_OUT}.pp"
        RTPP_OUT="${RTPP_OUT}.pp"
      fi
      diff -uB "${RTPP_OUT}" rtpproxy.rout
      RTPP_CHECK_RC="${?}"
      if [ ${RTPP_CHECK_RC} -eq 0 ]
      then
        break
      fi
    done
  fi
fi

report_rc_log "${ALICE_RC}" "${MM_CFG} alice.log bob.log rtpproxy.log ${MM_LOG}" "Checking if Alice is happy"
report_rc_log "${BOB_RC}" "${MM_CFG} bob.log alice.log rtpproxy.log ${MM_LOG}" "Checking if Bob is happy"

if [ "${RTPPC_TYPE}" != "rtp.io" ]
then
  report_rc_log "${RTPP_RC}" "${MM_CFG} rtpproxy.log ${MM_LOG}" "Checking RTPproxy exit code"
  if [ x"${MM_LOG}" != x"" ]
  then
    report_rc_log "${RTPP_CHECK_RC}" "rtpproxy.log ${MM_LOG}" "Checking RTPproxy stdout"
  else
    report_rc_log "${RTPP_CHECK_RC}" rtpproxy.log "Checking RTPproxy stdout"
  fi
fi
if [ x"${MM_LOG}" != x"" ]
then
  report_rc_log "${MM_RC}" "${MM_LOG}" "Checking ${MM_TYPE} exit code"
else
  report_rc "${MM_RC}" "Checking ${MM_TYPE} exit code"
fi
