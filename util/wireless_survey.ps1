# Accept a command-line argument for the URI
param (
    [string]$uri = ""
)

#Input error checking: Valid argument name/value?
if($uri -eq "") {
    echo "Usage: .\wireless_survey.ps1 -uri <URI>"
    exit 1
}

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
try {
    $statuscode = (Invoke-WebRequest -Uri "$uri/CMD" -Method POST -Body $postdat).statuscode
} catch {
    $statuscode = $_.Exception.Response.StatusCode.Value__
}

# Output error checking: Expected response code?
if ([string]::IsNullOrEmpty($statuscode)){
    echo "Unable to reach the specified URI."
    echo "Check the URI and the HoneyBadger server, and try again."
    exit 1
} elseif($statuscode -eq 404) {
    echo "The requested server responded with 404."
    echo "Either the page really was not found, or the request was successful."
    echo "Check the HoneyBadger web client for data to verify."
    exit 0
} else {
    echo "The requested server responded with an unexpected response code."
    echo "Check the URI and the HoneyBadger server, and try again."
    exit 1
}