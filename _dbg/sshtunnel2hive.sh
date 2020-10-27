#!/bin/sh
pgrep -f "spb99-hdp-nn01.ertelecom.ru:10000" -a && kill $(pgrep -f "spb99-hdp-nn01.ertelecom.ru:10000")
echo "Starting ssh forwarding to spb99-hdp-nn01.ertelecom.ru:10000"
ssh -f -N nn03 -L 10000:spb99-hdp-nn01.ertelecom.ru:10000
echo "... Now you can connect to 127.0.0.1:10000/"
echo "If you see 'Connected to ...' and escape character test connection is ok, PRESS Ctrl-C to exit\n---\n"
telnet localhost 10000
echo "...Pss your ssh-tunnel still running, hopefully ;)"