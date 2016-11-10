# HoneyBadger v2

HoneyBadger is a framework for targeted geolocation. While honeypots are traditionally used to passively detect malicious actors, HoneyBadger is an Active Defense tool to determine who the malicious actor is and where they are located. HoneyBadger leverages "agents" built in various technologies that harvest the requisite information from the target host in order to geolocate them. These agents report back to the HoneyBadger API, which presents the data in an user interface.

An early prototype of HoneyBadger (v1) can be seen in the presentation "[Hide and Seek: Post-Exploitation Style](http://youtu.be/VJTrRMqHU5U)" from ShmooCon 2013. The associated Metasploit Framework modules mentioned in the above presentation can be found [here](https://github.com/v10l3nt/metasploit-framework/tree/master/modules/auxiliary/badger). Note: These modules have not been updated to work with v2 of the API.

## Getting Started

### Pre-requisites

* Python 2.x

### Installation (Ubuntu and OS X)

1. Install [pip](https://pip.pypa.io/en/stable/installing/).
2. Clone the HoneyBadger repository.

    ```
    $ git clone https://github.com/lanmaster53/honeybadger.git
    ```

3. Install the dependencies.

    ```
    $ cd honeybadger/server
    $ pip install -r requirements.txt
    ```

4. Initialize the database in a Python interpreter.

    ```
    $ python
    >>> import honeybadger
    >>> honeybadger.initdb()
    ^D
    ```

5. Start the HoneyBadger server.

    ```
    $ python ./honeybadger.py
    ```

6. Visit the application and register a user.
7. Add targets using the "targets" page.
8. Deploy agents for the desired target.

Clicking the "demo" button next to any of the targets will launch a demo web page containing an `HTML`, `JavaScript`, and `Applet` agent for that target.

## API Usage

### IP Geolocation

This method geolocates the target based on the source IP of the request and assigns the resolved location to the given target and agent.

Example: (Method: `GET`)

```
http://<path:honeybadger>/api/beacon/<guid:target>/<string:agent>
```

### Known Coordinates

This method accepts previously resolved location data for the given target and agent.

Example: (Method: `GET`)

```
http://<path:honeybadger>/api/beacon/<guid:target>/<string:agent>?lat=<float:latitude>&lng=<float:longitude>&acc=<integer:accuracy>
```

### Wireless Survey

This method accepts wireless survey data and parses the information on the server-side, extracting what is needed to make a Google API geolocation call. The resolved geolocation data is then assigned to the given target. Parsers currently exist for survey data from Windows, Linux and OS X using the following commands:

Windows:

```
cmd.exe /c netsh wlan show networks mode=bssid | findstr "SSID Signal"
```

Linux:

```
/bin/sh -c iwlist scan | egrep 'Address|ESSID|Signal'
```

OS X:

```
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s
```

Example: (Method: `POST`)

```
http://<path:honeybadger>/api/beacon/<guid:target>/<string:agent>
```

POST Payload:

```
os=<string:operating-system>&data=<base64:data>
```

The `os` parameter must match one of the following regular expressions:

* `re.search('^mac os x', os.lower())`
* `re.search('^windows', os.lower())`
* `re.search('^linux', os.lower())`

### Universal Parameters

All requests can include an optional `comment` parameter. This parameter is sanitized and displayed within the UI as miscellaneous information about the target or agent.
