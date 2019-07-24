#!/bin/bash

# Input error checking: Valid argument count?
if [[ "$#" -ne 1 ]]; then
    echo "Usage: ./wireless_survey.sh <URL>"
    exit 1
fi

# Get wireless information
wireless_data=$(iwlist scan 2>&1 | egrep 'Address|ESSID|Signal')

# Create post data string
post_data="os=linux&data=$(echo "$wireless_data" | base64 -w 0)"

# Send the data to the URL supplied via command line argument. Store the response code.
response_code=$(curl -d "$post_data" "$1/CMD" --write-out %{http_code} --silent --output /dev/null)
curl_code="$?"

# Output error checking: Expected response code?
if [[ $response_code -eq "000" ]]; then
    echo "Unable to reach the specified URL. Curl response code: $curl_code."
    exit 1;
elif [[ $response_code -eq "404" ]]; then
    echo "The requested server responded with 404."
    echo "Either the page really was not found, or the request was successful."
    echo "Check the HoneyBadger web client for data to verify."
    exit 0;
else
    echo "The URL responded with an unexpected response code."
    echo "Check the URL and the HoneyBadger server, and try again."
    exit 1;
fi
