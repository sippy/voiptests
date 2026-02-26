#!/bin/sh

set -eux

apt-get update
apt-get install -y --no-install-recommends \
  python3 python3-pip \
  gpp gdb tcpdump gcc libc6-dev git make ca-certificates \
  libssl-dev flex bison

if [ "${MM_TYPE}" = "go-b2bua" ]
then
  apt-get install -y --no-install-recommends golang-go
fi

if [ "${MM_TYPE}" = "kamailio" ]
then
  apt-get install -y --no-install-recommends libcurl4-gnutls-dev
fi

SKIP_PY_DEPS=1 /bin/sh -x ./install_depends/opensips.sh

rm -rf /var/lib/apt/lists/*
