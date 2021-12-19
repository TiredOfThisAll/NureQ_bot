SCRIPT_PATH=$(dirname "${BASH_SOURCE[0]}")
SRC_PATH="${SCRIPT_PATH}/../src"
nohup python3.8 $SRC_PATH/bot_main.py &
nohup python3.8 $SRC_PATH/web_main.py
