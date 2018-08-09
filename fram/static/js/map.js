proj4.defs('EPSG:3413', '+proj=stere +lat_0=90 +lat_ts=70 +lon_0=-45 +k=1 ' +
    '+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs');
var proj3413 = ol.proj.get('EPSG:3413');
proj3413.setExtent([-4194304, -4194304, 4194304, 4194304]);
//proj3413.setWorldExtent([-4194304, -4194304, 4194304, 4194304]);

//var ext =  [-29.598609808656846, 79.41875951953834, 7.528721387689651, 84.66059789200978];


var map;
var vectorLayer;
var allPointFeatures, activePointFeatures, markerStyle;
var numInFlightTiles = 0;
var layerdict;
var static_layerinfo = {
  'Bathymetry': "<p><b>Bathmetry Polar Map</b><br>Source: ahocevar, ahocevar.com/geoserver</p>",
  'LandEdge': "<p><b>LandEdge</b><br>Source: NASA's EOSDIS, worldview.earthdata.nasa.gov<br>Pixel size: 255.9x255.9m / pixel<br>Raw size: 222MB</p>"
}

// setInterval(function(){ console.trace(); }, 3000);
var defaultView = new ol.View({
  projection: 'EPSG:3413',
  center: ol.proj.transform([-4, 83.5],"WGS84", "EPSG:3413"),
  rotation: Math.PI / 7, // Quick fix instead of changing projections
  zoom: 5,
  minZoom: 3,
  extent: ol.proj.get("EPSG:3413").getExtent()
})

function setCustomLayerSource (workspace, name){
  return new ol.source.TileWMS({
      url: 'http://localhost:8080/geoserver/wms',
      //url: 'http://192.168.38.113:8080/geoserver/wms',
      params: {
        'LAYERS': workspace + ':' + name,
        'TILED': true,
        transparent: true,
        format: 'image/png',
      },
      projection: 'EPSG:3413'
    })
}

bathlayer = new ol.layer.Tile({
  source: new ol.source.TileWMS({
    url: 'https://ahocevar.com/geoserver/wms',
    crossOrigin: '',
    params: {
      'LAYERS': 'ne:NE1_HR_LC_SR_W_DR',
      'TILED': true/*,
      'crossOrigin': 'anonymous'*/
    },
    projection: 'EPSG:3413'
  })
});
bathlayer.setVisible(false);

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
  // var layernames = ["iceconc", "terra2"/*, "opticclose"*/, "s1mosv2", "s1b2",  "s2"/*, "s1_clouds", "terra_clouds"*/, "icequiverwarp", "landedge"];
  var layernames = ['seaice', 'terramos', 's1mos', 's1c', 's2c', 'icedrift']
  var workspace_default= '2018-08-08'
  layerdict = {
    "base": baselayer,
    "bathymetry": bathlayer,
  };
  //Creating and adding all custom layers
  function addCustomLayers(workspace){
      for (var i = 0; i < layernames.length; i++) {
        layerdict[layernames[i]] = new ol.layer.Tile({ source: setCustomLayerSource(workspace, layernames[i]) });
        layerdict[layernames[i]].setVisible(false);
      }
  }
  addCustomLayers(workspace_default);
  console.log(positions);
  layerdict['landedge'] = new ol.layer.Tile({ source: setCustomLayerSource('cite', 'landedge') });
  layerdict['landedge'].setVisible(false);

// Adding markers
  allPointFeatures = [];
  activePointFeatures = [];


  Array.from(positions.keys()).forEach(function(element) {
    var grid = positions.get(element).split(',');
    var tmpPoint = new ol.geom.Point(
        ol.proj.transform( [parseFloat( grid[1] ), parseFloat( grid[0] )] , 'EPSG:4326', 'EPSG:3413' )
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
          stroke: new ol.style.Stroke({
              width: 1,
              color: 'rgba(200, 200, 200, 0.8)'
          }),
          radius: 3
      }),
  });
  vectorLayer = new ol.layer.Vector({
      source: new ol.source.Vector({projection: 'EPSG:3413',features: allPointFeatures}),
      style: markerStyle
  });
  vectorLayer.setZIndex(3);

  const scaleLineControl = new ol.control.ScaleLine();
  // Init map
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
  map.addLayer(vectorLayer);

  // Create the graticule component
  // var graticule = new ol.Graticule({
  //   strokeStyle: new ol.style.Stroke({
  //     color: 'rgba(255,120,0,0.9)',
  //     width: 2,
  //     lineDash: [0.5, 4]
  //   }),
  //   showLabels: true,
  //   targetSize: 300,
  //   maxLines: 20
  // });
  // console.log(map);
  // graticule.setMap(map);


  // ------------------ LOADING LOGIC ---------------- \\
  // map.getLayers().forEach(function (layer) {
  //     var source = layer.getSource();
  //     if (source instanceof ol.source.TileImage) {
  //         source.on('tileloadstart', function () {++numInFlightTiles})
  //         source.on('tileloadend', function () {--numInFlightTiles})
  //     }
  // })
  //
  // map.on('postrender', function (evt) {
  //   if (!evt.frameState)
  //       return;
  //
  //   var numHeldTiles = 0;
  //   var wanted = evt.frameState.wantedTiles;
  //   for (var layer in wanted)
  //       if (wanted.hasOwnProperty(layer))
  //           numHeldTiles += Object.keys(wanted[layer]).length;
  //
  //   var ready = numInFlightTiles === 0 && numHeldTiles === 0;
  //   if (map.get('ready') !== ready)
  //     map.set('ready', ready);
  // });
  // map.set('ready', false);
  //
  // function whenMapIsReady(callback) {
  //     if (map.get('ready'))
  //         callback();
  //     else
  //         map.once('change:ready', whenMapIsReady.bind(null, callback));
  // }
  //
  // map.on('moveend', function (evt) {
  //   $('.loader').css("display", "block");
  //   $('.fadeout').css("display", "block");
  //   whenMapIsReady(function(){
  //     $('.loader').css("display", "none");
  //     $('.fadeout').css("display", "none");
  //   });
  // });
  // ------------------ LOADING LOGIC END ---------------- \\


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
  defaultView.animate({
    center: ol.proj.transform([-4, 83.5],"WGS84", "EPSG:3413"),
    zoom: 5
  });
}

function toggleInfo(bt){
  $('#LayerInfoContainer').toggle();
  $('#LayerInfo').text('');
  let layername = bt.id.split('Info')[0].split('bt')[1];
  if ($.inArray(layername, Object.keys(layerinfo)) != -1){
    $('#LayerInfo').html(layerinfo[layername]);
  }
  else{
    console.log(layername);
    $('#LayerInfo').html(static_layerinfo[layername]);
  }
}
function closeLayerInfo(){
  $('#LayerInfoContainer').toggle();
}

$(document).ready(function() {

  $('#btOpticClose').click(function() {
    ToggleLayer(this);
  });
  $('#btOpticMos').click(function() {
    ToggleLayer(this);
  });
  $('#btSARClose').click(function() {
    ToggleLayer(this);
  });
  $('#btSARMos').click(function() {
    ToggleLayer(this);
  });
  $('#btBathymetry').click(function() {
    ToggleLayer(this);
  });
  $('#btSeaIce').click(function() {
    ToggleLayer(this);
  });
  $('#btIceDrift').click(function() {
    ToggleLayer(this);
  });
  $('#btLandEdge').click(function() {
    ToggleLayer(this);
  });
  /*$('#btGridLines').click(function() {
    ToggleLayer(this);
  });*/

  document.getElementById("OpticClose").addEventListener('mouseup', function() {
    layerdict[this.name].setOpacity(this.value / 100);
  });
  document.getElementById("OpticMos").addEventListener('mouseup', function() {
    layerdict[this.name].setOpacity(this.value / 100);
  });
  document.getElementById("SARClose").addEventListener('mouseup', function() {
    layerdict[this.name].setOpacity(this.value / 100);
  });
  document.getElementById("SARMos").addEventListener('mouseup', function() {
    layerdict[this.name].setOpacity(this.value / 100);
  });
  document.getElementById("Bathymetry").addEventListener('mouseup', function() {
    layerdict[this.name].setOpacity(this.value / 100);
  });
  document.getElementById("SeaIce").addEventListener('mouseup', function() {
    layerdict[this.name].setOpacity(this.value / 100);
  });
  document.getElementById("IceDrift").addEventListener('mouseup', function() {
    layerdict[this.name].setOpacity(this.value / 100);
  });
  document.getElementById("LandEdge").addEventListener('mouseup', function() {
    layerdict[this.name].setOpacity(this.value / 100);
  });
  /*document.getElementById("GridLines").addEventListener('mouseup', function() {
    layerdict[this.name].setOpacity(this.value / 100);
  });*/

  function changeDate(btn){
    if (btn.id == 'forward'){
      if (activePointFeatures.length < allPointFeatures.length){
        activePointFeatures.push(allPointFeatures[activePointFeatures.length])
      } else return false;
    }
    else{
      if (activePointFeatures.length > 0){
        activePointFeatures.pop()
      } else return false;
    }
    $('#used-date').html(Array.from(positions.keys())[activePointFeatures.length-1]);
    map.removeLayer(vectorLayer);
    vectorLayer = new ol.layer.Vector({
        source: new ol.source.Vector({projection: 'EPSG:3413',features: activePointFeatures}),
        style: markerStyle
    });
    map.addLayer(vectorLayer);

  }
  $('#forward').click(function() {
    changeDate(this)
  });
  $('#back').click(function() {
    changeDate(this)
  });

});
