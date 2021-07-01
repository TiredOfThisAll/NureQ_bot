SCRIPT_PATH=$(dirname "${BASH_SOURCE[0]}")
SRC_PATH="${SCRIPT_PATH}/../src"
pycodestyle $SRC_PATH

