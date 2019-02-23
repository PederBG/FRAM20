// ------ LOGIC FOR OPENLAYERS AND GEOSERVER ------ \\

// Init variables
const HOST_IP = 'http://185.35.187.19:8080/geoserver/wms';
// const HOST_IP = 'http://localhost:8080/geoserver/wms';
const MIN_ZOOM = 3.5;

var map, allPointFeatures, activePointFeatures, markerStyle, layernames, layerdict, vectorLayer, centerGrid;
const STATIC_LAYERINFO = {
  'Bathymetry': "<p><h5>Bathmetry Polar Map</h5><b>Orginal data:</b> SRTM30_Plus_v7_WinNorth50deg_Terrain_WGS84, warped to NSIDC Sea Ice Polar Stereographic North projection.</p>",
  'Magnetic': "<p><h5>Magnetic Anomali Overlay</h5></p>",
  'Gravity': "<p><h5>Freeair Gravity Overlay</h5></p>",
  'LandEdge': "<p><h5>Land Edges</h5><b>Source:</b> NASA, Earth Observing System Data and Information System (EOSDIS)<br><b>Available at:</b> worldview.earthdata.nasa.gov<br><b>Pixel size:</b> 255.9x255.9 meters<br><b>Raw size:</b> 222MB</p>",
  'Graticule': "<p><h5>Graticule Overlay</h5></p>",
  'Historical': "<p><h5>Ice drift 1. April - 1. August for the years 2012-2018</h5></p>Ice velocity fields from TOPAZ reanalysis.<br><b>Source:</b> E.U. Copernicus Marine Service Information - drift trajectories from MET Norway, OpenDrift  model."
}



// Setting projection for openlayers map
proj4.defs('EPSG:3413', '+proj=stere +lat_0=90 +lat_ts=70 +lon_0=-45 +k=1 ' +
    '+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs');
var proj3413 = ol.proj.get('EPSG:3413');
proj3413.setExtent([-4194304, -4194304, 4194304, 4194304]);
proj3413.setWorldExtent([-50, 80, 30, 87]);



// Set default view
if (positions.length == 0) centerGrid = ol.proj.transform([-4, 83.5],"WGS84", "EPSG:3413");
else{
  let grid = positions[positions.length-1][1].split(',');
  centerGrid = ol.proj.transform([parseFloat(grid[0]), parseFloat(grid[1])],"WGS84", "EPSG:3413");
}

var defaultView = new ol.View({
  projection: 'EPSG:3413',
  center: centerGrid,
  zoom: 4,
  minZoom: MIN_ZOOM,
  extent: ol.proj.get("EPSG:3413").getExtent()
})

// Define function to get raster data from geoserver
function setCustomLayerSource (workspace, name){
  let SLD_style; // S1-images use different geoserver styling
  SLD_style = name.indexOf('s1') != -1 ? 'cite:raster2' : 'raster';

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

// Getting base map using jquery get-syntax
var parser = new ol.format.WMTSCapabilities();
var url = 'https://map1.vis.earthdata.nasa.gov/wmts-arctic/' +
    'wmts.cgi?SERVICE=WMTS&request=GetCapabilities';

$.get( url, function(response) {
  var result = parser.read(response);
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


  // The order here decides z-index for images
  layernames = ['seaice', 'terramos', 's1mos', 's1c', 's2c', 'icedrift']
  var workspace_default = uglifyDate(latestDate);
  layerdict = {
    "base": baselayer,
  };

  // This is added first to set lowest z-index
  layerdict['bathymetry'] = new ol.layer.Tile({ source: setCustomLayerSource('cite', 'bathymetry') });
  layerdict['bathymetry'].setVisible(false);
  layerdict['magnetic'] = new ol.layer.Tile({ source: setCustomLayerSource('cite', 'magnetic') });
  layerdict['magnetic'].setVisible(false);
  layerdict['gravity'] = new ol.layer.Tile({ source: setCustomLayerSource('cite', 'gravity') });
  layerdict['gravity'].setVisible(false);

  // Creating and adding all custom layers
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


  // Init actual map
  const scaleLineControl = new ol.control.ScaleLine();
  map = new ol.Map({
    controls: ol.control.defaults({
       attributionOptions: {
         collapsible: false
       }
     }).extend([
       scaleLineControl
     ]),
    layers: Object.keys(layerdict).map(function(e) {return layerdict[e]}), // Object.values() is not supported by IE..
    target: 'map',
    view: defaultView
  });

  // Adding markers from positions in db
  if (positions.length != 0){
    allPointFeatures = [];
    activePointFeatures = [];

    let stopCondition = true;

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
      if (stopCondition) activePointFeatures.push(tmp);

      // If second-to-last layer is set to default
      if (element[0] == latestDate) stopCondition = false;
    });


    // Changing last point to an arrow (current station location)
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




// ------------------- INIT LAYER BUTTONS ----------------- \\

// TODO: Use same names everywere and maybe set names in db
ids = ['OpticClose', 'OpticMos', 'SARClose', 'SARMos', 'Bathymetry', 'Magnetic', 'Gravity', 'SeaIce', 'IceDrift', 'LandEdge', 'Graticule']
$(document).ready(function() {

    ids.forEach(function(id) {
        $('#bt' + id).click(function() { ToggleLayer(this) });

        $('#' + id).bind('mouseup touchend', function() {
          layerdict[this.name].setOpacity(this.value / 100);
        });
    });

    $('#forward').click(function() {
      changeDate(this)
    });
    $('#back').click(function() {
      changeDate(this)
    });
});
