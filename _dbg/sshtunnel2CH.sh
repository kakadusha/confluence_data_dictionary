#!/bin/sh
#set -x
#
LOCAL_PORT="8123"
#REMOTE_SOCKET="clickhouse-proactive1.cc-omsk.ertelecom.ru:8123"  # не сработало ?
REMOTE_SOCKET="10.124.65.218:8123"  # копия на кластере бигдата
REMOTE_SOCKET9000="10.124.65.218:9000"
REMOTE_SOCKET9440="10.124.65.218:9440"
#REMOTE_SOCKET="5.3.3.47:8123"       # мало прав по дуфолту видна только одна база  spas.ertelecom.ru

pgrep -f "10.124.65.218:" -a && kill $(pgrep -f "10.124.65.218:")
echo "Starting ssh forwarding to ${REMOTE_SOCKET}"
###

#ssh -f -N nn01 -L ${LOCAL_PORT}:${REMOTE_SOCKET}
ssh -f -N nn03 -L ${LOCAL_PORT}:${REMOTE_SOCKET}
ssh -f -N nn03 -L 9000:${REMOTE_SOCKET9000}
ssh -f -N nn03 -L 9440:${REMOTE_SOCKET9440}
# go though Aida: 
# run on Napa> ssh -f -N -R 8123:localhost:8123 aidb
# run localy>  ssh -f -N aidb -L 8123:localhost:8123

echo ""
# проверка, должен вернуть "OK"
wget -nv http://localhost:${LOCAL_PORT} && cat ./index.html && rm ./index.html
###
echo "If you see OK ^ you can connect to 127.0.0.1:${LOCAL_PORT}/ or 9000, 9440 ports"
