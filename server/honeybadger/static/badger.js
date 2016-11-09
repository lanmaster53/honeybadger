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

function add_marker(opts, place, target) {
    var marker = new google.maps.Marker(opts);
    var infowindow = new google.maps.InfoWindow({
        autoScroll: false,
        content: place.details
    });
    google.maps.event.addListener(marker, 'click', function() {
        infowindow.open(map,marker);
    });
    // add the marker to its target storage array
    if (!window['markers'].hasOwnProperty(target)) {
        window['markers'][target] = [];
    }
    window['markers'][target].push(marker);
    bounds.extend(opts.position);
    return marker;
}

function load_markers(json) {
    var targets = [];
    for (var i = 0; i < json['beacons'].length; i++) {
        marker = json['beacons'][i];
        // add the marker to the map
        var comment = marker.comment || '';
        var currMarker = add_marker({
            position: new google.maps.LatLng(marker.lat,marker.lng),
                title:marker.ip+":"+marker.port,
                map:map
            },{
            details:'<table class="iw-content">'
                + '<caption>'+marker.target+'</caption>'
                + '<tr><td>Agent:</td><td>'+marker.agent+' @ '+marker.ip+':'+marker.port+'</td></tr>'
                + '<tr><td>Time:</td><td>'+marker.time+'</td></tr>'
                + '<tr><td>User-Agent:</td><td>'+marker.useragent+'</td></tr>'
                + '<tr><td>Latitude:</td><td>'+marker.lat+'</td></tr>'
                + '<tr><td>Longitude:</td><td>'+marker.lng+'</td></tr>'
                + '<tr><td>Accuracy:</td><td>'+marker.acc+'</td></tr>'
                + '<tr><td>Comment:</td><td>'+comment+'</td></tr>'
                + '</table>'
            },
            marker.target
        );
        // add filter checkboxes for each target
        if (targets.indexOf(marker.target) === -1) {
            var checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'targets';
            checkbox.value = marker.target;
            checkbox.setAttribute('checked', 'checked');
            checkbox.checked = true;
            checkbox.addEventListener('change', function(e) {
                toggle_marker(e.target);
            });
            document.getElementById('filter').appendChild(checkbox);
            document.getElementById('filter').appendChild(document.createTextNode(' '+marker.target));
            document.getElementById('filter').appendChild(document.createElement('br'));
            targets.push(marker.target);
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
    for (var i = 0; i < window['markers'][element.value].length; i++) {
        window['markers'][element.value][i].setMap(_map);
    }
}

/*function open_marker(marker) {
    google.maps.event.trigger(marker, "click");
}*/

$(document).ready(function() {

    // load the map
    load_map();

    // load the beacons
    $.ajax({
        type: "GET",
        url: "/api/beacons",
        success: function(data) {
            // declare a storage array for markers
            window['markers'] = {};
            // store the raw beacons for later use
            //window['beacons'] = data['beacons'];
            //console.log(data);
            load_markers(data);
            flash("Markers loaded successfully.");
        },
        error: function(error) {
            console.log(error)
            flash(error.message);
        }
    });

    // register a target filter event handler
    /*$("input[name='targets']").on('change', function() {
        $.each($("input[name='targets']"), function() {
            if(this.checked) {
                toggle_markers(map, this.value);
            } else {
                toggle_markers(null, this.value);
            }
        });
    });*/

    /*var sse = new EventSource("/subscribe");
    sse.onmessage = function(e) {
        console.log(e.data);
        load_markers(JSON.parse(e.data));
    };*/

});
