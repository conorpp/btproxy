#!/usr/bin/env bash

pid=$(ps aux | grep bluetoothd | grep -vP 'replace|grep'| awk '{print $2}' )
sudo kill -9 $pid
sudo LD_PRELOAD=./blocksdp.so bluetoothd $@ -n
