"""
Written by PederBG, 2018-08

Help function used when downloading and processing images.
"""

from datetime import date, datetime, timedelta
from sentinelsat.sentinel import SentinelAPI, read_geojson, geojson_to_wkt
import zipfile
import subprocess, glob


# Help function for downloading satellite products
def getSentinelFiles(DATE, COLHUB_UNAME, COLHUB_PW, TMPDIR, bbox, max_files=1, polarization='hh', platform='s1', time_window=1):
    print('Arguments -> Box: %s, Max downloads: %s, Polarization: %s, Platform: %s' \
        %(bbox, max_files, polarization, platform))
    api = SentinelAPI(COLHUB_UNAME, COLHUB_PW, 'https://colhub.met.no/#/home')
    # api = SentinelAPI(self.COLHUB_UNAME, self.COLHUB_PW, 'https://scihub.copernicus.eu/dhus/#/home')
    date = DATE.strftime('%Y%m%d')
    yestdate = (DATE - timedelta(time_window)).strftime('%Y%m%d') # 4 day interval in dev

    footprint = geojson_to_wkt(read_geojson(bbox))
    if platform == 's1':
        products = api.query(footprint,
                        # ("20180805", "20180807"),
                        (yestdate, date),
                         platformname='Sentinel-1',
                         producttype='GRD',
                         sensoroperationalmode='EW'
                         )
    elif platform == 's2':
        products = api.query(footprint,
                        # ("20180805", "20180807"),
                        (yestdate, date),
                         platformname='Sentinel-2',
                         cloudcoverpercentage=(0, 70) # TODO: find reasonable threshold
                         )
    else:
        print('Not a valid platform!')
        return [False]

    if len(products) == 0:
        print("No files found at date: " + date)
        return [False]
    print("Found", len(products), "Sentinel images.")

    if platform == 's2':
        products_df = api.to_dataframe(products).sort_values(['cloudcoverpercentage', 'size'], ascending=[True, True])
        products_df = products_df.head(1)
    else:
        products_df = api.to_dataframe(products).sort_values('size', ascending=True)

    downloadNames = []

    for i in range(len(products_df)):
        if i == max_files: # Prevents too large mosaic file
            break
        product_size = float(products_df['size'].values[i].split(' ')[0])
        product_name = products_df['filename'].values[i][:-5]

        product_clouds = ''
        if platform == 's2':
            product_clouds = ', Cloudcover: ' + str(products_df['cloudcoverpercentage'].values[i])
        print("Name: %s, size: %s MB%s" %(product_name, product_size, product_clouds))

        # if max_files == 1: # No point with ingestion date in mosaics with several images
        #     self.returns[platform + 'c'] = products_df['ingestiondate'].values[i]
        api.download(products_df['uuid'][i], TMPDIR)

        if platform == 's1':
            # UNZIPPING DOWNLOADED FILE
            print("Unzipping product...")
            zip_ref = zipfile.ZipFile(TMPDIR + product_name + '.zip')
            zip_ref.extractall(TMPDIR)
            zip_ref.close()

            geofiles = glob.glob(TMPDIR + product_name + '.SAFE/measurement/*')
            # FINDING RIGHT POLARIZATION FILE (now using HH-polarization)
            if '-' + polarization + '-' in geofiles[0]:
                downloadNames.append(geofiles[0])
            else:
                downloadNames.append(geofiles[1])

        elif platform == 's2':
            downloadNames.append(product_name)
    return downloadNames



# Tiling GeoTiff files for bether rendering performance
def tileImage(GDALHOME, infile, outfile):
    print('Tiling image for bether rendering performance...')
    cmd = '%sgdal_translate -of GTiff -co TILED=YES %s %s' %(GDALHOME, infile, outfile)
    subprocess.call(cmd, shell=True)


# Building overview images for bether rendering performance
# TODO difference between tileImage and buildImageOverviews ?
def buildImageOverviews(GDALHOME, outfile, num=5):
    print("Building overview images for bether rendering performance...")
    opt = ['2', '4', '8', '16', '32', '64']
    overviews = ""
    for i in range(num):
        overviews += opt[i] + ' '
    cmd = '%sgdaladdo -r average %s %s' %(GDALHOME, outfile, overviews[:-1])
    subprocess.call(cmd, shell=True)

def warpImage(GDALHOME, proj, custom_args, infile, outfile):
        print("Warping to NSIDC Sea Ice Polar Stereographic North projection...")
        cmd = '%sgdalwarp -of GTiff -t_srs %s %s %s %s' %(GDALHOME, proj, custom_args, infile, outfile)
        return subprocess.call(cmd, shell=True)


# Removing tmp files
def clean(TMPDIR):
    print('\nCleaning used files...')
    cmd = 'rm -r ' + TMPDIR
    subprocess.call(cmd, shell=True)


# Build geojson bounding box from input coordinates
def makeGeojson(grid, outfile, xstep, ystep):
    print('Making geojson bounding box...')
    east = grid.split(',')[0]
    north = grid.split(',')[1]

    topLeft = str( float(east) - xstep ) + ',' + str( float(north) + ystep )
    topRight = str( float(east) + xstep ) + ',' + str( float(north) + ystep )
    bottomRight = str( float(east) + xstep ) + ',' + str( float(north) - ystep )
    bottomLeft = str( float(east) - xstep ) + ',' + str( float(north) - ystep )
    json_string = '{"type":"FeatureCollection","features":[\n\
    {"type":"Feature","properties":{},"geometry":{\n\
        "type":"Polygon","coordinates":[[\n\
            [' + topLeft + '],\n\
            [' + topRight + '],\n\
            [' + bottomRight + '],\n\
            [' + bottomLeft + '],\n\
            [' + topLeft + ']\n\
        ]]\n\
    }}\n\
]}'
    f = open(outfile, "w")
    f.write(json_string)
    f.close()
    return outfile


def printLayerStatus(str):
    print('--------------------------------------------------')
    print('Generating layer: %s' %(str))
    print('--------------------------------------------------')
