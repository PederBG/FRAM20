// proj4.defs('EPSG:3413', '+proj=stere +lat_0=90 +lat_ts=70 +lon_0=-45 +k=1 ' +
//     '+x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs');
// var proj3413 = ol.proj.get('EPSG:3413');
// proj3413.setExtent([-4194304, -4194304, 4194304, 4194304]);

proj4.defs("EPSG:3408","+proj=laea +lat_0=90 +lon_0=0 +x_0=0 +y_0=0 +a=6371228 +b=6371228 +units=m +no_defs");
var proj3408 = ol.proj.get('EPSG:3408');
//proj3408.setExtent([-4194304, -4194304, 4194304, 4194304]);


baselayer = new ol.layer.Tile({
  source: new ol.source.TileWMS({
    url: 'https://ahocevar.com/geoserver/wms',
    crossOrigin: '',
    params: {
      'LAYERS': 'ne:NE1_HR_LC_SR_W_DR',
      'TILED': true
    },
    projection: 'EPSG:4326'
  })
});
console.log(baselayer)

// Init map
map = new ol.Map({
  layers: baselayer,
  target: 'map',
  // view: new ol.View({
  //   projection: 'EPSG:3408',
  //   center: ol.proj.transform([0, 83],"WGS84", "EPSG:3408"),
  //   zoom: 4,
  //   minZoom: 3,
  //   //extent: ol.proj.get("EPSG:3408").getExtent()
  // })
});
