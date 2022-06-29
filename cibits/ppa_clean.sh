#!/bin/sh

set -e
set -x

badppas="ppa.launchpad.net"

for ppa in ${badppas}
do
    mfiles="`grep -l ${ppa} /etc/apt/sources.list.d/*`"
    if [ -z "${mfiles}" ]
    then
      continue
    fi
    for mfile in ${mfiles}
    do
      newname="/tmp/`basename ${mfile}`"
      grep -v ${ppa} "${mfile}" > "${newname}" || true
      sudo mv "${newname}" "${mfile}"
    done
done
