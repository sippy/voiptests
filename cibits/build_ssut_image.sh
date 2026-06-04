#!/bin/sh

set -eux

SKIP_PY_DEPS=1 /bin/sh -x ./install_depends/opensips.sh

rm -rf /var/lib/apt/lists/*
