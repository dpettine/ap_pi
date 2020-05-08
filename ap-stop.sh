#!/bin/bash

echo "stopping AP application"
PID=`ps -eaf | grep pi_ap | grep -v grep | awk '{print $2}'`
if [[ "" !=  "$PID" ]]; then
  sudo kill -9 $PID
fi

PID=`ps -eaf | grep pi_ap | grep -v grep | awk '{print $2}'`

if [[ "" ==  "$PID" ]]; then
        echo "AP application stopped"
else
        echo "Couldn't stop AP application. Please retry !"
fi

