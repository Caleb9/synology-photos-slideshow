# Builds pex package

set -x
python3.9 -m venv --upgrade-deps venv
. venv/bin/activate
pip install -U pex
make
