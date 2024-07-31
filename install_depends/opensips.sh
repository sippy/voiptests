#!/bin/sh

set -e

BASEDIR="${BASEDIR:-$(dirname -- "${0}")/..}"
BASEDIR="$(readlink -f -- ${BASEDIR})"

. ${BASEDIR}/functions

if [ -e "${BUILDDIR}/dist" ]
then
  rm -rf "${BUILDDIR}/dist"
fi
mkdir "${BUILDDIR}/dist"
cd "${BUILDDIR}/dist"

MM_PATCH_SET=""

mm_patch_set_append() {
  if [ -z "${MM_PATCH_SET}" ]
  then
    MM_PATCH_SET="${1}"
  else
    MM_PATCH_SET="${MM_PATCH_SET} ${1}"
  fi
}

case "${MM_TYPE}" in
opensips)
  MM_REPO=${MM_REPO:-"https://github.com/OpenSIPS/opensips.git"}
  ;;
b2bua)
  MM_REPO=${MM_REPO:-"https://github.com/sippy/b2bua.git"}
  ;;
kamailio)
  MM_REPO=${MM_REPO:-"https://github.com/kamailio/kamailio.git"}
  ;;
go-b2bua)
  MM_REPO=${MM_REPO:-"https://github.com/sippy/go-b2bua.git"}
  ;;
*)
  echo "Bogus MM_TYPE=\"${MM_TYPE}\"" 2>&1
  exit 1
  ;;
esac

git clone -b "${MM_BRANCH}" "${MM_REPO}" "${MM_TYPE}"
MM_GIT="git -C ${MM_TYPE}"
if [ "${MM_REV}" != "${MM_BRANCH}" ]
then
  ${MM_GIT} checkout "${MM_REV}"
fi
${MM_GIT} rev-parse HEAD

if [ "${MM_TYPE}" = "opensips" ]
then
  MM_DIR="${BUILDDIR}/dist/opensips"
  perl -pi -e 's|-O[3-9]|-O0 -g3|' "${MM_DIR}/Makefile.defs"
  if [ "${MM_BRANCH}" = "2.3" ]
  then
    mm_patch_set_append mod.rtpproxy_iodebug.diff
  fi
  if [ "${MM_BRANCH}" = "2.4" ]
  then
    mm_patch_set_append old/mod.rtpproxy_retry.diff
  fi
  if [ "${MM_BRANCH}" = "master" ]
  then
    MM_KILL_MODULES="rabbitmq_consumer event_kafka"
  fi
fi

if [ "${MM_TYPE}" = "b2bua" ]
then
  ( cat ${BASEDIR}/install_depends/b2bua_radius.py.fix; \
  grep -v '^from sippy.Rtp_proxy_client import Rtp_proxy_client' b2bua/sippy/b2bua_radius.py ) | \
   sed "s|%%SIPPY_ROOT%%|${BASEDIR}/dist/b2bua|" > b2bua/sippy/b2bua_test.py
  chmod 755 b2bua/sippy/b2bua_test.py
  ${PYTHON_CMD} -m pip install -U -r b2bua/requirements.txt
fi

if [ "${MM_TYPE}" = "kamailio" ]
then
  perl -pi -e 's|-O[3-9]|-O0 -g3| ; s|^run_target = .[(]run_prefix[)]/.[(]run_dir[)]|run_target = /tmp/kamailio|' \
   ${BUILDDIR}/dist/kamailio/Makefile.defs
  if [ "${MM_BRANCH}" = "4.4" ]
  then
    mm_patch_set_append contact_flds_separator.4.x.patch
  fi
  if [ "${MM_BRANCH}" = "5.0" -o "${MM_BRANCH}" = "5.1" ]
  then
    mm_patch_set_append contact_flds_separator.patch
  fi
fi

for p in ${MM_PATCH_SET}
do
  ${MM_GIT} apply "${BUILDDIR}/install_depends/${MM_TYPE}/${p}"
done

if [ "${RTPP_BRANCH}" != "DOCKER" ]
then
  git clone -b "${RTPP_BRANCH}" --recursive https://github.com/sippy/rtpproxy.git
else
  git clone --recursive https://github.com/sippy/rtpproxy.git
fi
RTP_GIT="git -C rtpproxy"
${RTP_GIT} rev-parse HEAD

if [ "${MM_TYPE}" = "opensips" ]
then
  for m in ${MM_KILL_MODULES}
  do
    rm -rf "${MM_DIR}/modules/${m}"
  done
  if [ "${MM_BRANCH}" = "master" ]
  then
    _EXTRA_OPTS="CC_EXTRA_OPTS=-Werror"
  fi
  ${MAKE_CMD} -C "${MM_DIR}" ${_EXTRA_OPTS} CC_NAME=gcc CC="${CC}" \
   NICER=0 all modules
fi

if [ "${MM_TYPE}" = "kamailio" ]
then
  ${MAKE_CMD} -C "${BUILDDIR}/dist/kamailio" CC_NAME=gcc CC="${CC}" LD="${CC}" \
   include_modules="sl tm rr maxfwd rtpproxy textops" \
   skip_modules="erlang corex sipcapture sms app_sqlang" all modules
fi

if [ "${MM_TYPE}" = "go-b2bua" ]
then
    go version
    which go
    ${MAKE_CMD} -C "${BUILDDIR}/dist/go-b2bua" all
fi

cd rtpproxy
./configure

if [ "${RTPP_BRANCH}" != "DOCKER" ]
then
  ${MAKE_CMD} all install
fi
