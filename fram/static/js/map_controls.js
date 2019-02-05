// ------ CONTROLS FOR MAP-PAGE ------ \\

// Init variables
let win = $(window);
let arrowDown = true;

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


function setDefaultView(){
  if (positions.length == 0) centerGrid = ol.proj.transform([-4, 83.5],"WGS84", "EPSG:3413");
  else centerGrid = activePointFeatures[activePointFeatures.length-1].getProperties().geometry.A;
  defaultView.animate({
    center: centerGrid,
    zoom: 5
  });
}


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


function displayGridCallback(){
  raw_grid = map.getView().getCenter();
  conv_grid = ol.proj.transform( [parseFloat( raw_grid[0] ), parseFloat( raw_grid[1] )] , 'EPSG:3413', 'EPSG:4326' )

  output = conv_grid[1].toFixed(4) + ' N, '
  if (conv_grid[0] < 0) output += conv_grid[0].toFixed(4) *-1 + ' W'
  else output += conv_grid[0].toFixed(4) + ' E'

  $('#grid-display').html(output);
}
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
  $('#cross-x, #cross-y, #grid-display').toggle();
}

// Scrolling up/down
function scrollDown(){
  if (arrowDown) $('html').animate({ scrollTop: $(document).height()}, 'fast');
  else $('html').animate({ scrollTop: 0 }, 'fast');
}

// Control button for scrolling up/down
win.scroll(function() {
  if ( ( win.scrollTop() + 0.7 * win.innerHeight() ) > window.innerHeight ) {
    arrowDown = false;
    $('#scroll-down').css('transform','rotate(' + 180 + 'deg)');
  }
  else{
    arrowDown = true;
    $('#scroll-down').css('transform','rotate(' + 0 + 'deg)');
  }
});


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


function uglifyDate(dateString){
  let tmp = new Date(dateString);
  return new Date(tmp.getTime() - (tmp.getTimezoneOffset() * 60000)).toISOString().split('T')[0];
}
