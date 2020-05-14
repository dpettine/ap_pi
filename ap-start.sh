#!/bin/bash
DIR=$(dirname "$0")

# Start Http Server application
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Start AP application
attmpt=1
PID=`ps -eaf | grep pi_ap | grep -v grep | awk '{print $2}'`

if [[ "" !=  "$PID" ]]; then
	echo "AP application  is already running. PID:" $PID | tee -a $DIR/log/pi_ap.log
else
	while [ "" ==  "$PID"  -a  $attmpt -lt 4 ]
	do
        	echo "starting AP application attempt number" $attmpt | tee -a $DIR/log/pi_ap.log
        	python3 pi_ap.py &>> $DIR/log/pi_ap.log &
        	sleep 10
        	PID=`ps -eaf | grep pi_ap | grep -v grep | awk '{print $2}'`
        	attmpt=$((attmpt+1))
	done
	
	if [[ "" !=  "$PID" ]]; then
        	echo "AP application started" | tee -a $DIR/log/pi_ap.log
	else
        	echo "Couldn't start AP application" | tee -a $DIR/log/pi_ap.log
	fi
fi
