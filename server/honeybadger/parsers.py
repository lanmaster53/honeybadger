import os

class AP(object):

    def __init__(self, ssid=None, bssid=None, ss=None, channel=None):
        self.ssid = ssid
        self.bssid = bssid
        self.ss = ss
        self.channel = channel

    @property
    def serialized_for_google(self):
        return {
            'macAddress': self.bssid,
            'signalStrength': self.ss,
            'channel': self.channel,
        }

    def __repr__(self):
        return '<AP ssid={}, bssid={}, ss={}, channel={}>'.format(self.ssid, self.bssid, self.ss, self.channel)

def parse_airport(content):
    aps = []
    lines = [l.strip() for l in content.strip().split(os.linesep)]
    for line in lines[1:]:
        words = line.split()
        aps.append(AP(ssid=words[0], bssid=words[1], ss=int(words[2]), channel=int(words[3])))
    return aps

def parse_netsh(content):
    aps = []
    lastssid = None
    lines = [l.strip() for l in content.strip().split(os.linesep)]
    for line in lines:
        words = line.split()
        # use startswith to avoid index errors
        if line.startswith('SSID'):
            lastssid = ' '.join(words[3:])
        elif line.startswith('BSSID'):
            ap = AP(ssid=lastssid)
            ap.bssid = words[3]
        elif line.startswith('Signal'):
            dbm = int(words[2][:-1]) - 100
            ap.ss = dbm
        elif line.startswith('Channel'):
            ap.channel = int(words[2])
            aps.append(ap)
    return aps

def parse_iwlist(content):
    aps = []
    lines = [l.strip() for l in content.strip().split(os.linesep)]
    for line in lines:
        words = line.split()
        if line.startswith('Cell'):
            ap = AP(bssid=words[4])
        elif line.startswith('Channel:'):
            ap.channel = int(words[0].split(':')[-1])
        elif line.startswith('Quality='):
            ap.ss = int(words[2][6:])
        elif line.startswith('ESSID:'):
            ap.ssid = line[7:-1]
            aps.append(ap)
    return aps

airport_test = '''                            SSID BSSID             RSSI CHANNEL HT CC SECURITY (auth/unicast/group)
                    gogoinflight 00:3a:9a:ea:1f:42 -78  40      N  -- NONE
                    gogoinflight 00:24:c3:50:54:22 -47  36      N  -- NONE
                    gogoinflight 00:3a:9a:ec:e6:02 -69  6       N  -- NONE
                    gogoinflight 00:24:c3:31:cd:d2 -41  1       N  -- NONE
'''

netsh_test = '''SSID 1 : Home
    Network type            : Infrastructure
    Authentication          : WPA2-Personal
    Encryption              : CCMP
    BSSID 1                 : 00:1e:c2:f6:7e:98
         Signal             : 99%
         Radio type         : 802.11n
         Channel            : 157
         Basic rates (Mbps) : 24 39 156
         Other rates (Mbps) : 18 19.5 36 48 54
    BSSID 2                 : 00:1c:10:08:b7:a5
         Signal             : 33%
         Radio type         : 802.11g
         Channel            : 11
         Basic rates (Mbps) : 1 2 5.5 11
         Other rates (Mbps) : 6 9 12 18 24 36 48 54
    BSSID 3                 : 00:1e:c2:f6:7e:97
         Signal             : 90%
         Radio type         : 802.11n
         Channel            : 1
         Basic rates (Mbps) : 1 2 5.5 11
         Other rates (Mbps) : 6 9 12 18 24 36 48 54

SSID 2 :
    Network type            : Infrastructure
    Authentication          : Open
    Encryption              : WEP
    BSSID 1                 : 62:45:b0:34:d3:53
         Signal             : 33%
         Radio type         : Any Radio Type
         Channel            : 44
         Basic rates (Mbps) :

SSID 3 : ATT5727
    Network type            : Infrastructure
    Authentication          : WPA2-Personal
    Encryption              : CCMP
    BSSID 1                 : 80:37:73:7b:7c:1f
         Signal             : 31%
         Radio type         : 802.11n
         Channel            : 11
         Basic rates (Mbps) : 1 2 5.5 11
         Other rates (Mbps) : 6 9 12 18 24 36 48 54

SSID 4 : 320Burbridge
    Network type            : Infrastructure
    Authentication          : WPA2-Personal
    Encryption              : CCMP
    BSSID 1                 : 00:1f:33:48:7f:f0
         Signal             : 40%
         Radio type         : 802.11n
         Channel            : 6
         Basic rates (Mbps) : 1 2 5.5 11
         Other rates (Mbps) : 6 9 12 18 24 36 48 54

SSID 5 : 320Burbridge_EXT
    Network type            : Infrastructure
    Authentication          : WPA2-Personal
    Encryption              : CCMP
    BSSID 1                 : c0:ff:d4:c2:07:b6
         Signal             : 30%
         Radio type         : 802.11n
         Channel            : 6
         Basic rates (Mbps) : 1 2
         Other rates (Mbps) : 5.5 6 9 11 12 18 24 36 48 54

SSID 6 : ATT3600
    Network type            : Infrastructure
    Authentication          : WPA2-Personal
    Encryption              : CCMP
    BSSID 1                 : e8:fc:af:d9:d1:14
         Signal             : 31%
         Radio type         : 802.11n
         Channel            : 1
         Basic rates (Mbps) : 1 2 5.5 11
         Other rates (Mbps) : 6 9 12 18 24 36 48 54

'''

iwlist_test = '''wlan1     Scan completed :
          Cell 01 - Address: 00:1E:C2:F6:7E:97
                    Channel:1
                    Frequency:2.412 GHz (Channel 1)
                    Quality=61/70  Signal level=-49 dBm  
                    Encryption key:on
                    ESSID:"Home"
                    Bit Rates:1 Mb/s; 2 Mb/s; 5.5 Mb/s; 11 Mb/s; 6 Mb/s
                              9 Mb/s; 12 Mb/s; 18 Mb/s
                    Bit Rates:24 Mb/s; 36 Mb/s; 48 Mb/s; 54 Mb/s
                    Mode:Master
                    Extra:tsf=000002b198bd7947
                    Extra: Last beacon: 3092ms ago
                    IE: Unknown: 0004486F6D65
                    IE: Unknown: 010882848B960C121824
                    IE: Unknown: 030101
                    IE: Unknown: 0706555320010B1E
                    IE: Unknown: 2A0102
                    IE: Unknown: 32043048606C
                    IE: IEEE 802.11i/WPA2 Version 1
                        Group Cipher : TKIP
                        Pairwise Ciphers (2) : CCMP TKIP
                        Authentication Suites (1) : PSK
                    IE: Unknown: 2D1AAC4117FFFFFF0000000000000000000000000000000000000000
                    IE: Unknown: 33027E9D
                    IE: Unknown: 3D1601001100000000000000000000000000000000000000
                    IE: Unknown: 46050200010000
                    IE: WPA Version 1
                        Group Cipher : TKIP
                        Pairwise Ciphers (1) : TKIP
                        Authentication Suites (1) : PSK
                    IE: Unknown: DD180050F2020101010003A4000027A4000042435E0062322F00
                    IE: Unknown: DD0700039301720320
                    IE: Unknown: DD0E0017F20700010106001EC2F67E97
                    IE: Unknown: DD0B0017F20100010100000007
          Cell 02 - Address: C8:B3:73:02:F0:3B
                    Channel:1
                    Frequency:2.412 GHz (Channel 1)
                    Quality=33/70  Signal level=-77 dBm  
                    Encryption key:on
                    ESSID:"319 Burbridge Ct"
                    Bit Rates:1 Mb/s; 2 Mb/s; 5.5 Mb/s; 11 Mb/s; 18 Mb/s
                              24 Mb/s; 36 Mb/s; 54 Mb/s
                    Bit Rates:6 Mb/s; 9 Mb/s; 12 Mb/s; 48 Mb/s
                    Mode:Master
                    Extra:tsf=0000000ac57bf5a0
                    Extra: Last beacon: 16024ms ago
                    IE: Unknown: 001033313920427572627269646765204374
                    IE: Unknown: 010882848B962430486C
                    IE: Unknown: 030101
                    IE: Unknown: 2A0104
                    IE: Unknown: 2F0104
                    IE: IEEE 802.11i/WPA2 Version 1
                        Group Cipher : TKIP
                        Pairwise Ciphers (2) : CCMP TKIP
                        Authentication Suites (1) : PSK
                    IE: Unknown: 32040C121860
                    IE: Unknown: 2D1AFC181BFFFF000000000000000000000000000000000000000000
                    IE: Unknown: 3D1601081500000000000000000000000000000000000000
                    IE: Unknown: 4A0E14000A002C01C800140005001900
                    IE: Unknown: 7F0101
                    IE: Unknown: DD840050F204104A0001101044000102103B000103104700101C18BB447704CE8C3AAB08F3407263FF10210005436973636F1023000D4C696E6B7379732045323530301024000776312E302E30371042000234321054000800060050F20400011011000D4C696E6B737973204532353030100800022688103C0001031049000600372A000120
                    IE: Unknown: DD090010180203F0040000
                    IE: WPA Version 1
                        Group Cipher : TKIP
                        Pairwise Ciphers (2) : CCMP TKIP
                        Authentication Suites (1) : PSK
                    IE: Unknown: DD180050F2020101800003A4000027A4000042435E0062322F00
          Cell 03 - Address: 00:1C:10:08:B7:A5
                    Channel:11
                    Frequency:2.462 GHz (Channel 11)
                    Quality=37/70  Signal level=-73 dBm  
                    Encryption key:on
                    ESSID:"Home"
                    Bit Rates:1 Mb/s; 2 Mb/s; 5.5 Mb/s; 11 Mb/s; 18 Mb/s
                              24 Mb/s; 36 Mb/s; 54 Mb/s
                    Bit Rates:6 Mb/s; 9 Mb/s; 12 Mb/s; 48 Mb/s
                    Mode:Master
                    Extra:tsf=00000029f37bf68e
                    Extra: Last beacon: 924ms ago
                    IE: Unknown: 0004486F6D65
                    IE: Unknown: 010882848B962430486C
                    IE: Unknown: 03010B
                    IE: Unknown: 2A0100
                    IE: Unknown: 2F0100
                    IE: IEEE 802.11i/WPA2 Version 1
                        Group Cipher : CCMP
                        Pairwise Ciphers (1) : CCMP
                        Authentication Suites (1) : PSK
                    IE: Unknown: 32040C121860
                    IE: Unknown: DD090010180201F0000000
                    IE: Unknown: DD180050F2020101800003A4000027A4000042435E0062322F00
          Cell 04 - Address: C8:B3:73:02:F0:3D
                    Channel:1
                    Frequency:2.412 GHz (Channel 1)
                    Quality=31/70  Signal level=-79 dBm  
                    Encryption key:off
                    ESSID:"319 Burbridge Ct-guest"
                    Bit Rates:1 Mb/s; 2 Mb/s; 5.5 Mb/s; 11 Mb/s; 18 Mb/s
                              24 Mb/s; 36 Mb/s; 54 Mb/s
                    Bit Rates:6 Mb/s; 9 Mb/s; 12 Mb/s; 48 Mb/s
                    Mode:Master
                    Extra:tsf=0000000ac57c3254
                    Extra: Last beacon: 16024ms ago
                    IE: Unknown: 0016333139204275726272696467652043742D6775657374
                    IE: Unknown: 010882848B962430486C
                    IE: Unknown: 030101
                    IE: Unknown: 2A0104
                    IE: Unknown: 2F0104
                    IE: Unknown: 32040C121860
                    IE: Unknown: 2D1AFC181BFFFF000000000000000000000000000000000000000000
                    IE: Unknown: 3D1601081500000000000000000000000000000000000000
                    IE: Unknown: 4A0E14000A002C01C800140005001900
                    IE: Unknown: 7F0101
                    IE: Unknown: DD090010180203F0040000
                    IE: Unknown: DD180050F2020101800003A4000027A4000042435E0062322F00
          Cell 05 - Address: C0:83:0A:CE:D2:C9
                    Channel:11
                    Frequency:2.462 GHz (Channel 11)
                    Quality=27/70  Signal level=-83 dBm  
                    Encryption key:on
                    ESSID:"2WIRE698"
                    Bit Rates:1 Mb/s; 2 Mb/s; 5.5 Mb/s; 11 Mb/s; 6 Mb/s
                              9 Mb/s; 12 Mb/s; 18 Mb/s
                    Bit Rates:24 Mb/s; 36 Mb/s; 48 Mb/s; 54 Mb/s
                    Mode:Master
                    Extra:tsf=00000333ab61d181
                    Extra: Last beacon: 17172ms ago
                    IE: Unknown: 00083257495245363938
                    IE: Unknown: 010882848B960C121824
                    IE: Unknown: 03010B
                    IE: Unknown: 050400010000
                    IE: Unknown: 0706555320010B1B
                    IE: Unknown: 2A0100
                    IE: Unknown: 32043048606C
          Cell 06 - Address: 00:24:B2:91:BB:1C
                    Channel:6
                    Frequency:2.437 GHz (Channel 6)
                    Quality=29/70  Signal level=-81 dBm  
                    Encryption key:on
                    ESSID:"Toadstool"
                    Bit Rates:1 Mb/s; 2 Mb/s; 5.5 Mb/s; 11 Mb/s; 18 Mb/s
                              24 Mb/s; 36 Mb/s; 54 Mb/s
                    Bit Rates:6 Mb/s; 9 Mb/s; 12 Mb/s; 48 Mb/s
                    Mode:Master
                    Extra:tsf=00000001f5c0458a
                    Extra: Last beacon: 2108ms ago
                    IE: Unknown: 0009546F616473746F6F6C
                    IE: Unknown: 010882848B962430486C
                    IE: Unknown: 030106
                    IE: Unknown: 2A0100
                    IE: Unknown: 2F0100
                    IE: IEEE 802.11i/WPA2 Version 1
                        Group Cipher : CCMP
                        Pairwise Ciphers (1) : CCMP
                        Authentication Suites (1) : PSK
                    IE: Unknown: 32040C121860
                    IE: Unknown: DD090010180200F0000000
                    IE: Unknown: DD180050F2020101800003A4000027A4000042435E0062322F00

eth0      Interface doesn't support scanning.

lo        Interface doesn't support scanning.

'''
