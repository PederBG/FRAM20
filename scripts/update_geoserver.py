import os
from geoserver.catalog import Catalog

PATH = '/root/fram19/data_dir/data'
layers = [os.path.join(dp, f) for dp, dn, filenames in os.walk(PATH) for f in filenames if os.path.splitext(f)[1] == '.geotiff']

cat = Catalog("http://localhost:8080/geoserver/rest/", "admin", os.environ["GEOSERVER_SECRET_KEY"])
# cat = Catalog("http://localhost:8080/geoserver/rest/", "admin", "geoserver")
print(cat)

for i in range(len(layers)):
    date = layers[i].split('/')[-3]

    ws = cat.get_workspace(date)
    if ws is None:
        ws = cat.create_workspace(date, date + 'uri')

    layername = layers[i].split('/')[-2]
    print('({}/{} - adding {}: {} to geoserver...'.format(i+1, len(layers), date, layername))
    cat.create_coveragestore(name = layername,
                             data = layers[i],
                             workspace = ws,
                             overwrite = True)
