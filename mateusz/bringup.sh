#!/bin/bash

set -eux

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
TOP_DIR=$SCRIPT_DIR/../

sudo snap install --classic deno

deno install -f $TOP_DIR/brili.ts
deno install -f --allow-env --allow-read $TOP_DIR/ts2bril.ts

pushd $TOP_DIR/bril-txt > /dev/null
pip install --user flit
flit install --symlink --user
popd > /dev/null

pip install --user turnt

if ! grep -q snap/deno $HOME/.bashrc ; then
	echo 'export PATH="/home/mateusz/snap/deno/105/.deno/bin:$PATH"' >> $HOME/.bashrc
fi
