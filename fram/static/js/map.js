proj4.defs('EPSG:3413', '+proj=stere +lat_0=90 +lat_ts=70 +lon_0=-45 +k=1 ' +
    '+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs');
var proj3413 = ol.proj.get('EPSG:3413');
proj3413.setExtent([-4194304, -4194304, 4194304, 4194304]);
proj3413.setWorldExtent([-50, 80, 30, 87]);


var map, allPointFeatures, activePointFeatures, markerStyle, layernames, layerdict, vectorLayer, centerGrid;
var HOST_IP = 'http://185.35.187.19:8080/geoserver/wms'
// var HOST_IP = 'http://localhost:8080/geoserver/wms'
var static_layerinfo = {
  'Bathymetry': "<p><h5>Bathmetry Polar Map</h5><b>Orginal data:</b> SRTM30_Plus_v7_WinNorth50deg_Terrain_WGS84, warped to NSIDC Sea Ice Polar Stereographic North projection.</p>",
  'LandEdge': "<p><h5>Land Edges</h5><b>Source:</b> NASA, Earth Observing System Data and Information System (EOSDIS)<br><b>Available at:</b> worldview.earthdata.nasa.gov<br><b>Pixel size:</b> 255.9x255.9 meters<br><b>Raw size:</b> 222MB</p>",
  'Graticule': "<p><h5>Graticule Overlay</h5></p>"
}

// default values
const MIN_ZOOM = 3.5

if (positions.length == 0) centerGrid = ol.proj.transform([-4, 83.5],"WGS84", "EPSG:3413");
else{
  let grid = positions[positions.length-1][1].split(',');
  centerGrid = ol.proj.transform([parseFloat(grid[0]), parseFloat(grid[1])],"WGS84", "EPSG:3413");
}

var defaultView = new ol.View({
  projection: 'EPSG:3413',
  center: centerGrid,
  zoom: 5,
  minZoom: MIN_ZOOM,
  extent: ol.proj.get("EPSG:3413").getExtent()
})

function setCustomLayerSource (workspace, name){
  let SLD_style; // S1-images use different geoserver styling
  SLD_style = name.includes('s1') ? 'cite:raster2' : 'raster';

  return new ol.source.TileWMS({
      url: HOST_IP,
      params: {
        'LAYERS': workspace + ':' + name,
        'TILED': true,
        transparent: true,
        format: 'image/png',
        styles: SLD_style
      },
      projection: 'EPSG:3413'
    })
}

var parser = new ol.format.WMTSCapabilities();
var url = 'https://map1.vis.earthdata.nasa.gov/wmts-arctic/' +
    'wmts.cgi?SERVICE=WMTS&request=GetCapabilities';
fetch(url).then(function(response) {
  return response.text();
}).then(function(text) {
  var result = parser.read(text);
  var options = ol.source.WMTS.optionsFromCapabilities(result, {
    layer: 'OSM_Land_Mask',
    matrixSet: 'EPSG3413_250m'
  });
  options.crossOrigin = '';
  options.projection = 'EPSG:3413';
  options.wrapX = false;
  baselayer = new ol.layer.Tile({
    source: new ol.source.WMTS(/** @type {!olx.source.WMTSOptions} */ (options))
  });
  // Waiting for http response..

  // The order here decides z-index for images
  layernames = ['seaice', 'terramos', 's1mos', 's1c', 's2c', 'icedrift']
  var workspace_default = uglifyDate(latestDate);
  console.log(workspace_default);
  layerdict = {
    "base": baselayer,
  };
  //Creating and adding all custom layers

  // This is added first to set lowest z-index
  layerdict['bathymetry'] = new ol.layer.Tile({ source: setCustomLayerSource('cite', 'bathymetry') });
  layerdict['bathymetry'].setVisible(false);

  function addCustomLayers(workspace){
      for (var i = 0; i < layernames.length; i++) {
        layerdict[layernames[i]] = new ol.layer.Tile({ source: setCustomLayerSource(workspace, layernames[i]) });
        layerdict[layernames[i]].setVisible(false);
      }
  }
  addCustomLayers(workspace_default);

  layerdict['landedge'] = new ol.layer.Tile({ source: setCustomLayerSource('cite', 'landedge') });
  layerdict['landedge'].setVisible(false);
  layerdict['graticule'] = new ol.layer.Tile({ source: setCustomLayerSource('cite', 'graticule') });
  layerdict['graticule'].setVisible(false);


  // Init map
  const scaleLineControl = new ol.control.ScaleLine();
  map = new ol.Map({
    controls: ol.control.defaults({
       attributionOptions: {
         collapsible: false
       }
     }).extend([
       scaleLineControl
     ]),
    layers: Object.values(layerdict),
    target: 'map',
    view: defaultView
  });

  // Adding markers
  if (positions.length != 0){
    allPointFeatures = [];
    activePointFeatures = [];

    positions.forEach(function(element) {
      var grid = element[1].split(',');
      var tmpPoint = new ol.geom.Point(
          ol.proj.transform( [parseFloat( grid[0] ), parseFloat( grid[1] )] , 'EPSG:4326', 'EPSG:3413' )
      );
      var marker2 = new ol.Feature({
      geometry: tmpPoint
    });
      tmp = new ol.Feature({ geometry: tmpPoint})
      allPointFeatures.push(tmp);
      activePointFeatures.push(tmp);
    });


    // Changing last point to an arrow (station location)
    allPointFeatures[allPointFeatures.length - 1].setStyle(
        new ol.style.Style({
            image: new ol.style.RegularShape({
              fill: new ol.style.Fill({color: 'red'}),
              stroke:  new ol.style.Stroke({color: 'black', width: 1}),
              points: 3,
              radius: 6,
              rotation: Math.PI / 4,
              angle: 0
            })
          })
      );
    markerStyle = new ol.style.Style({
        image: new ol.style.Circle({
            fill: new ol.style.Fill({
                color: 'rgba(200, 50, 50, 1)'
            }),
            radius: 4
        }),
    });

    // Adding markers to map
    vectorLayer = new ol.layer.Vector({
        source: new ol.source.Vector({projection: 'EPSG:3413',features: allPointFeatures}),
        style: markerStyle
    });
    vectorLayer.setZIndex(3);

    map.addLayer(vectorLayer);
  }
});





// ------------------- CONTROLS ----------------- \\
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
    $('#LayerInfo').html(static_layerinfo[layername]);
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

function scrollUp(){
  $('html').animate({ scrollTop: 0 }, 'fast');
}

// Add controls to all buttons
// TODO: Use same names everywere and maybe set names in db
ids = ['OpticClose', 'OpticMos', 'SARClose', 'SARMos', 'Bathymetry', 'SeaIce', 'IceDrift', 'LandEdge', 'Graticule']
$(document).ready(function() {

    ids.forEach(function(id) {
        $('#bt' + id).click(function() { ToggleLayer(this) });

        $('#' + id).bind('mouseup touchend', function() {
          layerdict[this.name].setOpacity(this.value / 100);
        });
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
  $('#forward').click(function() {
    changeDate(this)
  });
  $('#back').click(function() {
    changeDate(this)
  });
});

// Needed at setup
function uglifyDate(dateString){
  let tmp = new Date(dateString);
  return new Date(tmp.getTime() - (tmp.getTimezoneOffset() * 60000)).toISOString().split('T')[0];
}
