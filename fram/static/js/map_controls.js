// ------ CONTROLS FOR MAP PAGE ------ \\
// https://images-cdn.9gag.com/photo/a8GpvLd_700b.jpg

// Init variables
let win = $(window);
let arrowDown = true;
let activeHistoricals = {};
let times;
const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const monthMap = {'Jan.': 'January', 'Feb.': 'February', 'March': 'March', 'April': 'April', 'May': 'May', 'June': 'June', 'July': 'July', 'Aug.': 'August', 'Sept.': 'September', 'Oct.': 'October', 'Nov.': 'November', 'Dec.': 'December'};
const nameMap = {
  's2c': 'OpticClose',
  'terramos': 'OpticMosaic',
  's1c': 'SARClose',
  's1mos': 'SARMosaic',
  'seaice': 'SeaIce',
  'icedrift': 'IceDrift'
}


// Show/hide geoserver map layers
function ToggleLayer(bt){
  let active = layerdict[bt.name].getVisible();
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

// Move map view to default area
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

  // Beautify lat/lon grid
  output = conv_grid[1].toFixed(4) + ' N, ';
  if (conv_grid[0] < 0) output += conv_grid[0].toFixed(4) *-1 + ' W';
  else output += conv_grid[0].toFixed(4) + ' E';

  $('#grid-display').html(output);

  // Show weather (requesting xml-file from an api provided by yr.no)
  let url = "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=" + conv_grid[1] + "&lon=" + conv_grid[0];
  $.get( url, function(response) {
    let times = response["properties"]['timeseries'];

    // Getting first value for next day and 3 days
    let tomorrow_string = new Date().addDays(1).toISOString().substring(0, 10);
    let tomorrow = false;
    let threedays_string = new Date().addDays(3).toISOString().substring(0, 10);
    let threedays = false;
    let sevendays_string = new Date().addDays(7).toISOString().substring(0, 10);
    let sevendays = false;

    for (let i = 0; i < times.length; i++) {
      if ( times[i]['time'].substring(0,10) == tomorrow_string && !tomorrow ){
        tomorrow = times[i]
      }
      else if ( times[i]['time'].substring(0,10) == threedays_string && !threedays ){
        threedays = times[i]
      }
      else if ( times[i]['time'].substring(0,10) == sevendays_string && !sevendays ){
        sevendays = times[i]
      }
    }

    let today_dir = times[0]['data']['instant']['details']['wind_from_direction'];
    let today_speed = times[0]['data']['instant']['details']['wind_speed'];
    let today_temp = times[0]['data']['instant']['details']['air_temperature'];

    let tomorrow_dir = tomorrow['data']['instant']['details']['wind_from_direction'];
    let tomorrow_speed = tomorrow['data']['instant']['details']['wind_speed'];
    let tomorrow_temp = tomorrow['data']['instant']['details']['air_temperature'];

    let threedays_dir = threedays['data']['instant']['details']['wind_from_direction'];
    let threedays_speed = threedays['data']['instant']['details']['wind_speed'];
    let threedays_temp = threedays['data']['instant']['details']['air_temperature'];

    let sevendays_dir = sevendays['data']['instant']['details']['wind_from_direction'];
    let sevendays_speed = sevendays['data']['instant']['details']['wind_speed'];
    let sevendays_temp = sevendays['data']['instant']['details']['air_temperature'];

    $('#weather-today').html('<b>Today:</b><br>' + today_speed + ' ' + today_dir + "<br>" + today_temp + "&#8451;");
    $('#weather-tomorrow').html('<b>Tomorrow:</b><br>' + tomorrow_speed + ' ' + tomorrow_dir + "<br>" + tomorrow_temp + "&#8451;");
    $('#weather-threedays').html('<b>3-days:</b><br>' + threedays_speed + ' ' + threedays_dir + "<br>" + threedays_temp + "&#8451;");
    $('#weather-sevendays').html('<b>7-days:</b><br>' + sevendays_speed + ' ' + sevendays_dir + "<br>" + sevendays_temp + "&#8451;");
    // $('#weather-tomorrow').html('<b>' + dayNames[new Date().addDays(1).getDay()] + ':</b><br>' + tomorrow_speed + ' ' + tomorrow_dir + "<br>" + tomorrow_temp + "&#8451;");
    // $('#weather-threedays').html('<b>' + dayNames[new Date().addDays(3).getDay()] + ':</b><br>' + threedays_speed + ' ' + threedays_dir + "<br>" + threedays_temp + "&#8451;");
    // $('#weather-sevendays').html('<b>Next ' + dayNames[new Date().addDays(7).getDay()] + ':</b><br>' + sevendays_speed + ' ' + sevendays_dir + "<br>" + sevendays_temp + "&#8451;");
  });
}


// Display grid for a spesific location on the map
function toggleCrosshair(){
  if($('#cross-x').css('display')=='none'){
    $('#btCrosshair').css('background-color', 'gray');
    map.on("moveend", displayGridCallback);
    displayGridCallback();

    // Small screens don't have the space for both..
    if ($('#historical-div').css('display')=='block' && $(window).width() < 600) toggleHistorical();
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
  let target = (navigator.userAgent.match(/(iPod|iPhone|iPad)/)) ? "body" : "html, body";
  if (arrowDown) $(target).animate({ scrollTop: $(document).height()}, 'fast');
  else $(target).animate({ scrollTop: 0 }, 'fast');
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
  if (btn != 0){
    $('#LayerInfoContainer').hide();
    if (btn.id == 'forward'){
      if (activePointFeatures.length < allPointFeatures.length){
        activePointFeatures.push(allPointFeatures[activePointFeatures.length])
      } else return false;
    }
    else if (btn.id == 'back') {
      if (activePointFeatures.length > 1){
        activePointFeatures.pop()
      } else return false;
    }
    else if (btn.id == 'fast-forward'){
      for (let i = 0; i < 20; i++) {
        if (activePointFeatures.length < allPointFeatures.length){
          activePointFeatures.push(allPointFeatures[activePointFeatures.length])
        } else break;
      }
    }
    else if (btn.id == 'fast-back'){
      for (let i = 0; i < 20; i++) {
        if (activePointFeatures.length > 1){
          activePointFeatures.pop()
        } else break;
      }
    }
    $('#used-date').html(positions[activePointFeatures.length-1][0]);
    map.removeLayer(vectorLayer);
    vectorLayer = new ol.layer.Vector({
        source: new ol.source.Vector({projection: 'EPSG:3413',features: activePointFeatures}),
        style: markerStyle
    });
    map.addLayer(vectorLayer);
  }
  layernames.forEach(function(name) {
    let date = uglifyDate(positions[activePointFeatures.length-1][0]);
    layerdict[name].setSource( setCustomLayerSource( date, name ) );

    // Disbale buttons for layers with no data
    if ($.inArray(nameMap[name], Object.keys(positions[activePointFeatures.length-1][2])) != -1){
      if ( positions[activePointFeatures.length-1][2][nameMap[name]].includes('<b>Sensing time:</b> No data<br>') ){
        $('#bt'+nameMap[name]).attr("disabled", true);
        $('#bt'+nameMap[name]).next().css('visibility', 'hidden');
      }
      else{
        $('#bt'+nameMap[name]).attr("disabled", false);
        if ($('#bt'+nameMap[name]).css('background-color') == 'rgb(128, 128, 128)')
          $('#bt'+nameMap[name]).next().css('visibility', 'visible');
      }
    }

  });
}

function toggleHistorical(){
  if($('#historical-div').css('display')=='none'){
    $('#btHistorical').css('background-color', 'gray');
    $('#btHistoricalInfo').css('visibility', 'visible')

    // Small screens don't have the space for both..
    if ($('#grid-display').css('display')=='block' && $(window).width() < 600){
      $('#btCrosshair').css('background-color', 'transparent');
      map.un("moveend", displayGridCallback);
      $('#cross-x, #cross-y, #grid-display, #weather-display').toggle();
      checkMenus();
    }
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
    let lons = $(btn)[0].value.split('|')[0].replace(/ /g,'').split(',');
    let lats = $(btn)[0].value.split('|')[1].replace(/ /g,'').split(',');

    // Make grids in right projection
    let points = [];
    for (let i = 0; i < lons.length; i++) {
      points.push(
          ol.proj.transform( [parseFloat( lons[i] ), parseFloat( lats[i] )] , 'EPSG:4326', 'EPSG:3413' )
      );
    }

    let vectorStyle = new ol.style.Style({
       stroke : new ol.style.Stroke({color : $(btn).css("background-color"), width: 2
     })
    });
    let vectorStyleA = new ol.style.Style({
       stroke : new ol.style.Stroke({color : $(btn).css("background-color"), width: 2, lineDash: [.1, 3]
     })
    });

    // Make OpenLayers vector
    vectorFeature = new ol.Feature({ geometry: new ol.geom.LineString(points) });
    ($(btn).html()[4] == 'a') ? vectorFeature.setStyle(vectorStyleA) : vectorFeature.setStyle(vectorStyle)

    let vectorLine = new ol.layer.Vector({
        source: new ol.source.Vector({
          features: [ vectorFeature ]
        })
      });

    map.addLayer(vectorLine);
    activeHistoricals[$(btn).html()] = vectorLine;
  }
}


// Fixing flow of different menus on the map (hard coding ftw..)
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
  let tmp;
  // Fix for bad date parsing in firefox
  if(navigator.userAgent.indexOf("Firefox") != -1 ){
    tmp = new Date(monthMap[dateString.split(' ')[0]] + ',' + dateString.split(' ').slice(1));
  }
  else{
    tmp = new Date(dateString);
  }
  let newDate = new Date(tmp.getTime() - (tmp.getTimezoneOffset() * 60000));
  return newDate.toISOString().split('T')[0];
}


// Help function to add days to date Object
Date.prototype.addDays = function(days) {
  let date = new Date(this.valueOf());
  date.setDate(date.getDate() + days);
  return date;
}


window.onload = function() {
  checkMenus();
  /*swal({
    icon: 'error',
    title: 'Error loading image layers',
    text: 'Because of a recent update some web browsers have issues loading image layers. Try a different browser! We are working on solving the problem.'
  });*/

};
