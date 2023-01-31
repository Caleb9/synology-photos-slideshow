# Sets up development environment

set -x
python3.9 -m venv --upgrade-deps venv
. venv/bin/activate
pip install -r requirements/dev.txt
