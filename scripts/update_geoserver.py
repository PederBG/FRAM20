import os
from geoserver.catalog import Catalog

PATH = '/root/fram19/data'
layers = [os.path.join(dp, f) for dp, dn, filenames in os.walk(PATH) for f in filenames if os.path.splitext(f)[1] == '.tif']

cat = Catalog("http://localhost:8080/geoserver/rest/", "admin", os.environ["GEOSERVER_SECRET_KEY"])
# cat = Catalog("http://localhost:8080/geoserver/rest/", "admin", "geoserver")
print(cat)

for layer in layers:
    date = layer.split('/')[-2]
    if date == 'data':
        date = 'cite'

    ws = cat.get_workspace(date)
    if ws is None:
        ws = cat.create_workspace(date, date + 'uri')

    layername = layer.split('/')[-1].split('.')[0]
    print('Adding ' + date + ':' + layername + ' to geoserver...')
    cat.create_coveragestore(name = layername,
                             data = layer,
                             workspace = ws,
                             overwrite = True)
