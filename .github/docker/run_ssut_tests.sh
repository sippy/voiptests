#!/bin/sh

set -eu

cd "${VOIPTESTS_DIR:-/opt/voiptests}"

rm -rf test.logs
LOG_FILES="bob.log alice.log rtpproxy.log rtpproxy.rout.diff.txt"
if [ -n "${ARTIFACT_FILES:-}" ]
then
  LOG_FILES="${LOG_FILES} ${ARTIFACT_FILES}"
fi

run_tests()
{
  TEST_RES="ok"
  RTPP_VERSION="$1" sh -x ./test_run.sh || TEST_RES="fail"
  mkdir -p "test.logs/$1"
  for f in ${LOG_FILES}
  do
    mv "${f}" "test.logs/$1" || true
  done
  test "${TEST_RES}" = "ok"
}

run_tests debug
run_tests production
