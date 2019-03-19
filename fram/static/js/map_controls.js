// ------ CONTROLS FOR MAP-PAGE ------ \\

// Init variables
let win = $(window);
let arrowDown = true;
let activeHistoricals = {};
let times;
const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];


// Show/hide geoserver map layers
function ToggleLayer(bt){
  var active = layerdict[bt.name].getVisible();
  layerdict[bt.name].setVisible(!active);
  if (!active){
    $('#'+bt.id).css("background-color", "gray")
    $('#'+bt.id).next().css('visibility', 'visible')
  }
  else{
    $('#'+bt.id).css("background", "transparent")
    $('#'+bt.id).next().css('visibility', 'hidden')
  }
}

// Move map view to default view area
function setDefaultView(){
  if (positions.length == 0) centerGrid = ol.proj.transform([-4, 83.5],"WGS84", "EPSG:3413");
  else centerGrid = activePointFeatures[activePointFeatures.length-1].getProperties().geometry.A;
  defaultView.animate({
    center: centerGrid,
    zoom: 4
  });
}

// Show/hide info box for a geoserver layer
function toggleInfo(bt){
  $('#LayerInfoContainer').toggle();
  $('#LayerInfo').text('');
  let layername = bt.id.split('Info')[0].split('bt')[1];
  if ($.inArray(layername, Object.keys(positions[activePointFeatures.length-1][2])) != -1){
    $('#LayerInfo').html(positions[activePointFeatures.length-1][2][layername]);
  }
  else{
    $('#LayerInfo').html(STATIC_LAYERINFO[layername]);
  }
}
function closeLayerInfo(){
  $('#LayerInfoContainer').toggle();
}

// Help function for toggleCrosshair and get weather
function displayGridCallback(){
  raw_grid = map.getView().getCenter();
  conv_grid = ol.proj.transform( [parseFloat( raw_grid[0] ), parseFloat( raw_grid[1] )] , 'EPSG:3413', 'EPSG:4326' );

  output = conv_grid[1].toFixed(4) + ' N, ';
  if (conv_grid[0] < 0) output += conv_grid[0].toFixed(4) *-1 + ' W';
  else output += conv_grid[0].toFixed(4) + ' E';

  $('#grid-display').html(output);

  // Show weather
  let url = "https://api.met.no/weatherapi/locationforecastlts/1.3/?lat=" + conv_grid[1] + "&lon=" + conv_grid[0];
  console.log(url);
  $.get( url, function(response) {
    let times = response.getElementsByTagName("time");

    // Getting first value for next day and 3 days
    let tomorrow_string = new Date().addDays(1).toISOString().substring(0, 10);
    let tomorrow = false;
    let threedays_string = new Date().addDays(3).toISOString().substring(0, 10);
    let threedays = false;
    let sevendays_string = new Date().addDays(7).toISOString().substring(0, 10);
    let sevendays = false;

    for (var i = 0; i < times.length; i++) {
      if ( times[i].getAttribute("from").substring(0,10) == tomorrow_string && !tomorrow ){
        tomorrow = times[i]
      }
      else if ( times[i].getAttribute("from").substring(0,10) == threedays_string && !threedays ){
        threedays = times[i]
      }
      else if ( times[i].getAttribute("from").substring(0,10) == sevendays_string && !sevendays ){
        sevendays = times[i]
      }
    }

    let today_dir = times[0].getElementsByTagName("windDirection")[0].getAttribute("name");
    let today_speed = times[0].getElementsByTagName("windSpeed")[0].getAttribute("mps");

    let tomorrow_dir = tomorrow.getElementsByTagName("windDirection")[0].getAttribute("name");
    let tomorrow_speed = tomorrow.getElementsByTagName("windSpeed")[0].getAttribute("mps");

    let threedays_dir = threedays.getElementsByTagName("windDirection")[0].getAttribute("name");
    let threedays_speed = threedays.getElementsByTagName("windSpeed")[0].getAttribute("mps");

    let sevendays_dir = sevendays.getElementsByTagName("windDirection")[0].getAttribute("name");
    let sevendays_speed = sevendays.getElementsByTagName("windSpeed")[0].getAttribute("mps");

    $('#weather-today').html('<b>Today:</b><br>' + today_speed + ' ' + today_dir);
    $('#weather-tomorrow').html('<b>' + dayNames[new Date().addDays(1).getDay()] + ':</b><br>' + tomorrow_speed + ' ' + tomorrow_dir);
    $('#weather-threedays').html('<b>' + dayNames[new Date().addDays(3).getDay()] + ':</b><br>' + threedays_speed + ' ' + threedays_dir);
    $('#weather-sevendays').html('<b>Next ' + dayNames[new Date().addDays(7).getDay()] + ':</b><br>' + sevendays_speed + ' ' + sevendays_dir);

  });
}


// Display grid for a spesific location on the map
function toggleCrosshair(){
  if($('#cross-x').css('display')=='none'){
    $('#btCrosshair').css('background-color', 'gray');
    map.on("moveend", displayGridCallback);
    displayGridCallback();
  }
  else{
    $('#btCrosshair').css('background-color', 'transparent');
    map.un("moveend", displayGridCallback);

  }
  $('#cross-x, #cross-y, #grid-display, #weather-display').toggle();
  checkMenus();
}

// Scrolling window up/down
function scrollWindow(){
  if (arrowDown) $('html').animate({ scrollTop: $(document).height()}, 'fast');
  else $('html').animate({ scrollTop: 0 }, 'fast');
}

// Control button for scrolling up/down
win.scroll(function() {
  if ( ( win.scrollTop() + 0.7 * win.innerHeight() ) > window.innerHeight ) {
    arrowDown = false;
    $('#scroll-window').css('transform','rotate(' + 180 + 'deg)');
  }
  else{
    arrowDown = true;
    $('#scroll-window').css('transform','rotate(' + 0 + 'deg)');
  }
});

// Changing date for the geoserver layers
function changeDate(btn){
  $('#LayerInfoContainer').hide();
  if (btn.id == 'forward'){
    if (activePointFeatures.length < allPointFeatures.length){
      activePointFeatures.push(allPointFeatures[activePointFeatures.length])
    } else return false;
  }
  else{
    if (activePointFeatures.length > 1){
      activePointFeatures.pop()
    } else return false;
  }
  $('#used-date').html(positions[activePointFeatures.length-1][0]);
  map.removeLayer(vectorLayer);
  vectorLayer = new ol.layer.Vector({
      source: new ol.source.Vector({projection: 'EPSG:3413',features: activePointFeatures}),
      style: markerStyle
  });
  map.addLayer(vectorLayer);

  layernames.forEach(function(name) {
    let date = uglifyDate(positions[activePointFeatures.length-1][0]);
    layerdict[name].setSource( setCustomLayerSource( date, name ) );
  });
}

function toggleHistorical(){
  if($('#historical-div').css('display')=='none'){
    $('#btHistorical').css('background-color', 'gray');
    $('#btHistoricalInfo').css('visibility', 'visible')

  }
  else{
    $('#btHistorical').css('background-color', 'transparent');
    $('#btHistoricalInfo').css('visibility', 'hidden')


  }
  $('#historical-div').toggle();
  checkMenus();
}


// Make historical ice drift trajectory (shitty solution..)
function showHistorical(btn){

  // Remove a  plot
  if ($(btn).html() in activeHistoricals) {
    $(btn).css({"border-color":"transparent", "opacity": "0.8"});
    map.removeLayer(activeHistoricals[$(btn).html()])
    delete activeHistoricals[$(btn).html()];
  }

  // Add a new plot
  else{
    $(btn).css({"border-color": "black", "border-width":"0.15em", "border-style":"solid", "opacity": "1"});
    // Get data
    let lons = $(btn)[0].value.split('|')[0].split(', ');
    let lats = $(btn)[0].value.split('|')[1].split(', ');

    // Make grids in right projection
    let points = [];
    for (var i = 0; i < lons.length; i++) {
      points.push(
          ol.proj.transform( [parseFloat( lons[i] ), parseFloat( lats[i] )] , 'EPSG:4326', 'EPSG:3413' )
      );
    }

    var vectorStyle = new ol.style.Style({
       stroke : new ol.style.Stroke({color : $(btn).css("background-color"), width: 2
     })
    });
    var vectorStyleA = new ol.style.Style({
       stroke : new ol.style.Stroke({color : $(btn).css("background-color"), width: 2, lineDash: [.1, 3]
     })
    });

    // Make OpenLayers vector

    vectorFeature = new ol.Feature({ geometry: new ol.geom.LineString(points) });
    ($(btn).html()[4] == 'a') ? vectorFeature.setStyle(vectorStyleA) : vectorFeature.setStyle(vectorStyle)

    var vectorLine = new ol.layer.Vector({
        source: new ol.source.Vector({
          features: [ vectorFeature ]
        })
      });

    map.addLayer(vectorLine);
    activeHistoricals[$(btn).html()] = vectorLine;
  }
}

// Fixing flow of different menus on the map
// Hard coding ftw..
function checkMenus(){
  if($(window).width() < 600){

    if($('#historical-div').css('display')=='block' && $('#grid-display').css('display') =='block'){
      $('#grid-display').css('margin-top', '0.5em');
      $('#weather-display').css('margin-top', '3.05em');
      $('#historical-div').css('margin-top', '10em');
    }
    else{
      $('#grid-display').css('margin-top', '0.5em');
      $('#historical-div').css('margin-top', '0.5em');
    }
  }

  else{
    if($('#historical-div').css('display')=='block'){
      $('#grid-display').css('margin-top', '3.5em');
      $('#weather-display').css('margin-top', '6.9em');
      $('#historical-div').css('margin-top', '0.5em');
    }
    else{
      $('#grid-display').css('margin-top', '0.5em');
      $('#weather-display').css('margin-top', '3.05em');
    }
  }
}

// Check the flow of menus when window is resized
$( window ).resize(function() {
  checkMenus();
});

// Help function to convert easy-to-read date into database date
function uglifyDate(dateString){
  let tmp = new Date(dateString);
  return new Date(tmp.getTime() - (tmp.getTimezoneOffset() * 60000)).toISOString().split('T')[0];
}

window.onload = function() {
  checkMenus();
};

// Help function to add days to date Object
Date.prototype.addDays = function(days) {
  var date = new Date(this.valueOf());
  date.setDate(date.getDate() + days);
  return date;
}
