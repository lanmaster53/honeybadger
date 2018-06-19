var map
var bounds

function load_map() {
    var coords = new google.maps.LatLng(0,0);
    var mapOptions = {
        zoom: 5,
        center: coords,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        disableDefaultUI: true,
        mapTypeControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
            position: google.maps.ControlPosition.RIGHT_TOP
        },
        panControl: true,
        panControlOptions: {
            position: google.maps.ControlPosition.RIGHT_BOTTOM
        },
        streetViewControl: true,
        streetViewControlOptions: {
            position: google.maps.ControlPosition.RIGHT_BOTTOM
        },
        zoomControl: true,
        zoomControlOptions: {
            position: google.maps.ControlPosition.RIGHT_BOTTOM
        },
    };
    map = new google.maps.Map(document.getElementById("map"), mapOptions);
    bounds = new google.maps.LatLngBounds();
}

function add_marker(opts, place, beacon) {
    var marker = new google.maps.Marker(opts);
    var infowindow = new google.maps.InfoWindow({
        autoScroll: false,
        content: place.details
    });
    google.maps.event.addListener(marker, 'click', function() {
        infowindow.open(map,marker);
    });
    // add the beacon data to its marker object
    marker.beacon = beacon;
    window['markers'].push(marker);
    bounds.extend(opts.position);
    return marker;
}

function load_markers(json) {
    var targets = [];
    var agents = [];
    for (var i = 0; i < json['beacons'].length; i++) {
        beacon = json['beacons'][i];
        // add the marker to the map
        var coords = beacon.lat+','+beacon.lng
        var comment = beacon.comment || '';
        var marker = add_marker({
            position: new google.maps.LatLng(beacon.lat,beacon.lng),
                title:beacon.ip+":"+beacon.port,
                map:map
            },{
            details:'<table class="iw-content">'
                + '<caption>'+beacon.target+'</caption>'
                + '<tr><td>Agent:</td><td>'+beacon.agent+' @ '+beacon.ip+':'+beacon.port+'</td></tr>'
                + '<tr><td>Time:</td><td>'+beacon.created+'</td></tr>'
                + '<tr><td>User-Agent:</td><td>'+beacon.useragent+'</td></tr>'
                + '<tr><td>Coordinates:</td><td><a href="https://www.google.com/maps/place/'+coords+'" target="_blank">'+coords+'</a></td></tr>'
                + '<tr><td>Accuracy:</td><td>'+beacon.acc+'</td></tr>'
                + '<tr><td>Comment:</td><td>'+comment+'</td></tr>'
                + '</table>'
            },
            beacon
        );
        // add filter checkboxes for each unique target
        if (targets.indexOf(beacon.target) === -1) {
            var checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'target';
            checkbox.value = beacon.target;
            checkbox.setAttribute('checked', 'checked');
            checkbox.checked = true;
            checkbox.addEventListener('change', function(e) {
                toggle_marker(e.target);
            });
            var filter = document.getElementById('filter-target');
            filter.appendChild(checkbox);
            filter.appendChild(document.createTextNode(' '+beacon.target));
            filter.appendChild(document.createElement('br'));
            targets.push(beacon.target);
        }
        // add filter checkboxes for each unique agent
        if (agents.indexOf(beacon.agent) === -1) {
            var checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'agent';
            checkbox.value = beacon.agent;
            checkbox.setAttribute('checked', 'checked');
            checkbox.checked = true;
            checkbox.addEventListener('change', function(e) {
                toggle_marker(e.target);
            });
            var filter = document.getElementById('filter-agent');
            filter.appendChild(checkbox);
            filter.appendChild(document.createTextNode(' '+beacon.agent));
            filter.appendChild(document.createElement('br'));
            agents.push(beacon.agent);
        }
    }
    map.fitBounds(bounds);
}

// set the map on all markers in the array
function toggle_marker(element) {
    _map = null;
    if(element.checked) {
        _map = map;
    }
    for (var i = 0; i < window['markers'].length; i++) {
        if (window['markers'][i].beacon[element.name] === element.value) {
            window['markers'][i].setMap(_map);
        }
    }
}

$(document).ready(function() {

    // load the map
    load_map();

    // load the beacons
    $.ajax({
        type: "GET",
        url: "/api/beacons",
        success: function(data) {
            // declare a storage array for markers
            window['markers'] = [];
            load_markers(data);
            flash("Markers loaded successfully.");
        },
        error: function(error) {
            console.log(error)
            flash(error.message);
        }
    });

    /*var sse = new EventSource("/subscribe");
    sse.onmessage = function(e) {
        console.log(e.data);
        load_markers(JSON.parse(e.data));
    };*/

});
