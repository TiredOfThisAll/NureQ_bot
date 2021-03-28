trap killgroup SIGINT

killgroup(){
    kill -9 $web_pid
    kill -9 $bot_pid
}

python3 ../src/bot_main.py &
bot_pid=$!
python3 ../src/web_main.py &
web_pid=$!

wait $web_pid
wait $bot_pid
