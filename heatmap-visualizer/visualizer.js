
fetch("/GOOGLE_API_KEY")
  .then( function(result) { return result.text() })
  .then(function(key){
    var url = "https://maps.googleapis.com/maps/api/js?key=" + key + "&libraries=visualization&callback=initMap";
    var googleScript = document.createElement("script");
    googleScript.setAttribute("src", url);
    document.head.appendChild(googleScript);
  });

fetch("/maps")
  .then(function(result) { return result.json(); })
  .then(
    function(maps) {
      var selector = document.getElementById("map-selector");
      maps.forEach(function(map) {
        var option = document.createElement("option");
        option.text = map;
        selector.add(option);
      });
    }
  );

var map, heatmap;

function initMap() {
  map = new google.maps.Map(document.getElementById('map'), {
    zoom: 10,
    center: {lat: 40.818241, lng: -73.947435},
    mapTypeId: google.maps.MapTypeId.ROADMAP
  });

  heatmap = new google.maps.visualization.HeatmapLayer({
    data: [],
    map: map
  });
}

function onSelectMap() {
  var mapName = document.getElementById("map-selector").value;

  if (!mapName) {
    heatmap.set("data", [])
    return;
  }

  fetch("/maps/" + mapName)
    .then(function(result) { return result.json(); })
    .then(function(map) {
      var data = map.data.map(function(dataPoint) {
        return {
          location: new google.maps.LatLng(dataPoint.lat, dataPoint.lon),
          weight: dataPoint.weight
        };
      });

      console.log(data)
      heatmap.set("data", data);
      heatmap.set("radius", map.pointRadius);
    });
}
