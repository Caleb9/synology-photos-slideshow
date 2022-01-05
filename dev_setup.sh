# Sets up development environment

set -x
python3.9 -m venv --clear --upgrade-deps venv
. venv/bin/activate
pip install -r requirements/dev.txt
