proj4.defs('EPSG:3413', '+proj=stere +lat_0=90 +lat_ts=70 +lon_0=-45 +k=1 ' +
    '+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs');
var proj3413 = ol.proj.get('EPSG:3413');
proj3413.setExtent([-4194304, -4194304, 4194304, 4194304]);
proj3413.setWorldExtent([-50, 80, 30, 87]);


var map, allPointFeatures, activePointFeatures, markerStyle, layernames, layerdict, vectorLayer;
var static_layerinfo = {
  'Bathymetry': "<p><h5>Bathmetry Polar Map</h5><b>Source:</b> Ahocevar Geospatial Solutions<br><b>Available at:</b> ahocevar.com/geoserver</p>",
  'LandEdge': "<p><h5>Land Edges</h5><b>Source:</b> NASA, Earth Observing System Data and Information System (EOSDIS)<br><b>Available at:</b> worldview.earthdata.nasa.gov<br><b>Pixel size:</b> 255.9x255.9 meters<br><b>Raw size:</b> 222MB</p>"
}

// default values
const MIN_ZOOM = 3.5

var defaultView = new ol.View({
  projection: 'EPSG:3413',
  center: ol.proj.transform([-4, 83.5],"WGS84", "EPSG:3413"),
  // rotation: Math.PI / 7, // Quick fix instead of changing projections
  zoom: 5,
  minZoom: MIN_ZOOM,
  extent: ol.proj.get("EPSG:3413").getExtent()
})

// Create the graticule component
const labelStyle = new ol.style.Text({
  font: '9px Calibri,sans-serif',
  textBaseline: 'bottom',
  fill: new ol.style.Fill({
    color: 'rgba(0,0,0,1)'
  }),
  stroke: new ol.style.Stroke({
    color: 'rgba(255,255,255,1)',
    width: 3
  })
});
const strokeStyle = new ol.style.Stroke({
  color: 'rgba(255,120,0,0.9)',
  width: 1,
})

let graticule = new ol.Graticule({
  strokeStyle: strokeStyle,
  showLabels: true,
  maxLines: 200,
  targetSize: 400,
  // lonLabelPosition: 0.05,
  // latLabelPosition: 0.95,
  lonLabelStyle: labelStyle,
  latLabelStyle: labelStyle
});

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

// Adding bathymetry layer
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
  layernames = ['seaice', 'terramos', 's1mos', 's1c', 's2c', 'icedrift']
  var workspace_default = uglifyDate(latestDate);
  console.log(workspace_default);
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
          stroke: new ol.style.Stroke({
              width: 3,
              color: 'rgba(200, 200, 200, 0.8)'
          }),
          radius: 3
      }),
  });

  // Adding markers to map
  vectorLayer = new ol.layer.Vector({
      source: new ol.source.Vector({projection: 'EPSG:3413',features: allPointFeatures}),
      style: markerStyle
  });
  vectorLayer.setZIndex(3);

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
  map.addLayer(vectorLayer);
  toggleGrid();


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

function toggleGrid(){
  if (graticule.getMap()){
    graticule.setMap();
    defaultView.setMinZoom(MIN_ZOOM)
    $('#btGridLines').css("background-color", "transparent")
  }
  else{
    graticule.setMap(map);
    defaultView.setMinZoom(1)
    $('#btGridLines').css("background", "gray")
  }
}

// Add controls to all buttons
// TODO: Use same names everywere and maybe set names in db
ids = ['OpticClose', 'OpticMos', 'SARClose', 'SARMos', 'Bathymetry', 'SeaIce', 'IceDrift', 'LandEdge']
$(document).ready(function() {

    ids.forEach(function(id) {
        $('#bt' + id).click(function() { ToggleLayer(this) });

        document.getElementById(id).addEventListener('mouseup', function() {
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
