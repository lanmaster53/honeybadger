# HoneyBadger v2

HoneyBadger is a framework for targeted geolocation. While honeypots are traditionally used to passively detect malicious actors, HoneyBadger is an Active Defense tool to determine who the malicious actor is and where they are located. HoneyBadger leverages "agents" built in various technologies that harvest the requisite information from the target host in order to geolocate them. These agents report back to the HoneyBadger API, where the data is stored and made available in the HoneyBadger user interface.

An early prototype of HoneyBadger (v1) can be seen in the presentation "[Hide and Seek: Post-Exploitation Style](http://youtu.be/VJTrRMqHU5U)" from ShmooCon 2013. The associated Metasploit Framework modules mentioned in the above presentation can be found [here](https://github.com/v10l3nt/metasploit-framework/tree/master/modules/auxiliary/badger). Note: These modules have not been updated to work with v2 of the API.

## Getting Started

### Pre-requisites

* Python 3.x

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

4. Initialize the database. The provided username and password will become the administrator account.

    ```
    $ python
    >>> import honeybadger
    >>> honeybadger.initdb(<username>, <password>)
    ```

5. Start the HoneyBadger server. API keys are required to use maps and geolocation services.

    ```
    $ python ./honeybadger.py -gk <GOOGLE_API_KEY> -ik <IPSTACK_API_KEY>
    ```

    Honeybadger will still run without the API keys, but mapping and geolocation functionality will be limited as a result.

    View usage information with either of the following:

   ```
   $ python ./honeybadger.py -h
   $ python ./honeybadger.py --help
   ```


6. Visit the application and authenticate.
7. Add users and targets as needed using their respective pages.
8. Deploy agents for the desired target.

Clicking the "demo" button next to any of the targets will launch a demo web page containing an `HTML`, `JavaScript`, and `Applet` agent for that target.

### Fresh Start

Make a mess and want to start over fresh? Do this.

```
$ python
>>> import honeybadger
>>> honeybadger.dropdb()
>>> honeybadger.initdb(<username>, <password>)
```

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
cmd.exe /c netsh wlan show networks mode=bssid | findstr "SSID Signal Channel"
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

## Example Web Agents

### HTML

```
img = new Image();
img.src = "http://<path:honeybadger>/api/beacon/<guid:target>/HTML";
```

or

```
<img src="http://<path:honeybadger>/api/beacon/<guid:target>/HTML" width=1 height=1 />
```

### JavaScript

Note: JavaScript (HTML5) geolocation agents will not work unless deployed in a secure context (HTTPS), or local host.

```
function showPosition(position) {
    img = new Image();
    img.src = "http://<path:honeybadger>/api/beacon/<guid:target>/JavaScript?lat=" + position.coords.latitude + "&lng=" + position.coords.longitude + "&acc=" + position.coords.accuracy;
}

if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(showPosition);
}
```

### Content Security Policy

```
response.headers['X-XSS-Protection'] = '0'
response.headers['Content-Security-Policy-Report-Only'] = '<string:policy>; report-uri http://<path:honeybadger>/api/beacon/<guid:target>/Content-Security-Policy'
```

### XSS Auditor

```
response.headers['X-XSS-Protection'] = '1; report=http://<path:honeybadger>/api/beacon/<guid:target>/XSS-Protection'
```
