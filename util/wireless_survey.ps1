# Accept a command-line argument for the URI
param (
    [string]$uri = ""
)

# Poll for wireless network information with Netsh
$wifi = netsh wlan show networks mode=bssid | findstr "SSID Signal Channel"

# Set encoding of wifi data
$wifibytes = [System.Text.Encoding]::UTF8.GetBytes($wifi)

# Base64-encode the wifi data bytes
$wifienc = [Convert]::ToBase64String($wifibytes)

# Assemble post data
$postdat = @{os='windows';data=$wifienc}

# Send POST request to server, using CMD as agent
Invoke-WebRequest -Uri "$uri/CMD" -Method POST -Body $postdat
