#!/bin/sh

set -e

GET_MM_HASH=0
while [ ${#} -gt 0 ]
do
  case "${1}" in
  --get_mm_hash)
    GET_MM_HASH=1
    ;;
  *)
    echo "Unknown option: ${1}" >&2
    exit 2
    ;;
  esac
  shift
done

BASEDIR="${BASEDIR:-$(dirname -- "${0}")/..}"
BASEDIR="$(readlink -f -- ${BASEDIR})"

. ${BASEDIR}/functions

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

git_ls_remote_hash() {
  _repo="${1}"
  _ref="${2}"
  _hash="$(git ls-remote "${_repo}" "${_ref}" 2>/dev/null | awk 'NR == 1 { print $1 }')"
  if [ -n "${_hash}" ]
  then
    printf '%s\n' "${_hash}"
    return 0
  fi
  return 1
}

get_mm_hash() {
  if [ "${MM_REV}" != "${MM_BRANCH}" ]
  then
    _ref="${MM_REV}"
  else
    _ref="${MM_BRANCH}"
  fi

  if [ "${_ref#refs/}" != "${_ref}" ]
  then
    git_ls_remote_hash "${MM_REPO}" "${_ref}" && return 0
  else
    for _remote_ref in "refs/heads/${_ref}" "refs/tags/${_ref}^{}" "refs/tags/${_ref}" "${_ref}"
    do
      git_ls_remote_hash "${MM_REPO}" "${_remote_ref}" && return 0
    done
  fi

  if [ "${#_ref}" -eq 40 ] && [ -z "$(printf '%s' "${_ref}" | tr -d '0123456789abcdefABCDEF')" ]
  then
    printf '%s\n' "${_ref}"
    return 0
  fi

  echo "Unable to resolve ${_ref} in ${MM_REPO}" >&2
  return 1
}

if [ "${GET_MM_HASH}" = "1" ]
then
  get_mm_hash
  exit ${?}
fi

if [ -e "${BUILDDIR}/dist" ]
then
  rm -rf "${BUILDDIR}/dist"
fi
mkdir "${BUILDDIR}/dist"
cd "${BUILDDIR}/dist"

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
  case "${MM_BRANCH}" in
  2[.]3)
    mm_patch_set_append mod.rtpproxy_iodebug.diff
    ;;
  2[.]4)
    mm_patch_set_append old/mod.rtpproxy_retry.diff
    mm_patch_set_append old/mi_trace.c.2.4.diff
    ;;
  3[.]0)
    mm_patch_set_append old/mi_trace.c.3.0.diff
    ;;
  3[.]2 | 3[.]3 | 3[.]5)
    mm_patch_set_append rtpproxy_notify_drain/3.2-3.3-3.5.diff
    ;;
  3[.]4)
    mm_patch_set_append rtpproxy_notify_drain/3.4-3.6.diff
    ;;
  master)
    MM_KILL_MODULES="rabbitmq_consumer event_kafka freeswitch freeswitch_scripting dispatcher load_balancer"
    ;;
  esac
fi

if [ "${MM_TYPE}" = "b2bua" ]
then
  if [ "${SKIP_PY_DEPS}" != "1" ]
  then
    ${PYTHON_CMD} -m pip install -U -r b2bua/requirements.txt
  fi
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
  case ${MM_BRANCH} in
  master)
    _EXTRA_OPTS="CC_EXTRA_OPTS=-Werror"
    ;;
  2[.]4 | 3[.]0)
    _EXTRA_OPTS="CC_EXTRA_OPTS=-Werror -std=gnu17 -Wno-misleading-indentation"
    ;;
  *)
    _EXTRA_OPTS="CC_EXTRA_OPTS=-Werror -std=gnu17"
    ;;
  esac
  ${MAKE_CMD} -C "${MM_DIR}" "${_EXTRA_OPTS}" CC_NAME=gcc CC="${CC}" \
   NICER=0 all modules
fi

if [ "${MM_TYPE}" = "kamailio" ]
then
  case ${MM_BRANCH} in
  5[.][1234567])
    _EXTRA_OPTS="CC_EXTRA_OPTS=-std=gnu17"
    ;;
  esac
  ${MAKE_CMD} -C "${BUILDDIR}/dist/kamailio" ${_EXTRA_OPTS} CC_NAME=gcc CC="${CC}" LD="${CC}" \
   include_modules="sl tm rr maxfwd rtpproxy textops" \
   skip_modules="erlang corex sipcapture sms app_sqlang" all modules
fi

if [ "${MM_TYPE}" = "go-b2bua" ]
then
    go version
    which go
    ${MAKE_CMD} -C "${BUILDDIR}/dist/go-b2bua" all
fi

if [ "${RTPP_BRANCH}" != "DOCKER" ]
then
  cd rtpproxy
  ./configure
  ${MAKE_CMD} all install
fi
