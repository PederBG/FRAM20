"""
Written by PederBG, 2018-08

This script will download and process up-to-date sensor data from multiple sources
and upload them as GeoTiff layers in a running geoserver. The geoserver will then
handle feeding layer-tiles to the front-end on request.

The script is meant to run as a cron job every day (or in a longer interval).

Layers:
    Sentinel-1 Optic Image Close-up (s2c)

    Terra MODIS Optic Mosaic (terramos)

    Sentinel-1 SAR High Resolution Close-up (s1c)

    Sentinel-1 SAR High Resolution Mosaic (s1mos)

    AMSR-2 Global Sea Ice Concentration (seaice)

    Low Resolution Sea Ice Drift (icedrift)

    S1 Mosaic using ESA's quicklooks (not in use)


NOTE: This script is written for Python 2.7. This is due to some library restrictions

"""

from datetime import date, datetime, timedelta
from sentinelsat.sentinel import SentinelAPI, read_geojson, geojson_to_wkt
import zipfile
import os, sys, subprocess, glob
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
import gdal
import urllib
import Image
import netCDF4 as nc
from geoserver.catalog import Catalog

np.set_printoptions(threshold=np.nan) # for ice-drift quiverplot


GDALHOME = '/usr/bin/'
TMPDIR = 'tmp/'
DATE = datetime.today()
OUTDIR = str(DATE.date()) + '/'
RUNDIR = os.getcwd()
DATE = datetime.today()
COLHUB_UNAME = 'PederBG'
COLHUB_PW = 'Copernicus'
PROJ = 'EPSG:3413'


if not os.path.isdir(GDALHOME):
    print('GDALHOME path is not set')
    exit()

if not os.path.isdir(TMPDIR):
    subprocess.call('mkdir ' + TMPDIR, shell=True)
if not os.path.isdir(OUTDIR):
    subprocess.call('mkdir ' + OUTDIR, shell=True)


def clean():
    s1Name = "yolo"
    cmd = 'rm -r ' + TMPDIR + ' && rm -r ' + s1Name + '*'
    subprocess.call(cmd, shell=True)

# --------------------------------- HELP FUNCTIONS------------------------------- #
def getSentinelFiles(bbox="bbox.geojson", max_files=1, polarization='hh', platform='s1'):
    print('Arguments -> Box: %s, Max downloads: %s, Polarization: %s, Platform: %s' \
        %(bbox, max_files, polarization, platform))
    # api = SentinelAPI(COLHUB_UNAME, COLHUB_PW, 'https://colhub.met.no/#/home')
    api = SentinelAPI(COLHUB_UNAME, COLHUB_PW, 'https://scihub.copernicus.eu/dhus/#/home')
    date = DATE.strftime('%Y-%m-%d').replace('-', '')
    yestdate = (DATE - timedelta(1)).strftime('%Y-%m-%d').replace('-', '')

    footprint = geojson_to_wkt(read_geojson(bbox))
    if platform == 's1':
        products = api.query(footprint,
                        #  ("20180805", "20180807"),
                         (yestdate, date),
                         platformname='Sentinel-1',
                         producttype='GRD',
                         sensoroperationalmode='EW'
                         )
    elif platform == 's2':
        products = api.query(footprint,
                        #  ("20180805", "20180807"),
                         (yestdate, date),
                         platformname='Sentinel-2',
                         cloudcoverpercentage=(0, 60) # TODO: find reasonable threshold
                         )
    else:
        print('Not a valid platform!')
        return False

    if len(products) == 0:
        print("No files found at date: " + date)
        return False
    print("Found", len(products), "Sentinel images.")

    products_df = api.to_dataframe(products) #.sort_values('size', ascending=True)

    downloadNames = []

    for i in range(len(products_df)):
        if i == max_files: # Prevents too large mosaic file
            break
        product_size = int(api.get_product_odata(products_df.index[i])["size"])
        product_name = api.get_product_odata(products_df.index[i])["title"]
        # downloadNames.append(TMPDIR + product_name)
        print "Name:", product_name, "size:", str(product_size / 1000000), "MB."

        api.download(products_df.index[i], TMPDIR)

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

def tileImage(infile, outfile):
    print('Tiling image')
    cmd = '%sgdal_translate -of GTiff -co TILED=YES %s %s' %(GDALHOME, infile, outfile)
    subprocess.call(cmd, shell=True)


def buildImageOverviews(outfile, num=5):
    print("Building overview images")
    opt = ['2', '4', '8', '16', '32', '64']
    overviews = ""
    for i in range(num):
        overviews += opt[i] + ' '
    cmd = '%sgdaladdo -r average %s %s' %(GDALHOME, outfile, overviews[:-1])
    subprocess.call(cmd, shell=True)
#-------------------------------------------------------------------------------#

# --------------------------------- S2 CLOSE-UP ------------------------------- #
def getS2():
    outfile = OUTDIR + 's2c.tif'
    s2Name = getSentinelFiles(platform='s2')[0]
    if not s2Name:
        return False
    # s2Name = 'S2A_MSIL1C_20180806T171901_N0206_R012_T27XWM_20180806T204942'

    s2FullName = 'SENTINEL2_L1C:"/vsizip/%s%s.zip/%s.SAFE/MTD_MSIL1C.xml":TCI:EPSG_32627' \
        %(TMPDIR, s2Name, s2Name)

    tmpfile = TMPDIR + 's2tmp.tif'

    # PROCESSING FILE
    print("Processing files...")
    print("Warping to NSIDC Sea Ice Polar Stereographic North projection")
    cmd = GDALHOME + 'gdalwarp -of GTiff -t_srs ' + PROJ + ' -tr 10 10 -order 3' + \
        ' -srcnodata 0 -dstalpha ' + s2FullName + ' ' + tmpfile
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)

    tileImage(tmpfile, outfile)
    buildImageOverviews(outfile)
    print('Sentinel-2 image is ready \n')
    return outfile

# --------------------------------- TERRA MOSAIC ------------------------------- #
def getTerra():
    outfile = OUTDIR + 'terramos'

    # DOWNLOADING NEWEST FILE WITH HTTP
    # time = str((date.today() - date(int(date.today().strftime('%Y')), 1, 1)).days -1)
    time = str(DATE.date()) # NASA changed the date format
    extent = '-2251630.1978347152,-1767716.822874052,2386588.9709421024,1917931.4225647242'
    layers = 'MODIS_Terra_CorrectedReflectance_TrueColor'

    query = 'https://gibs.earthdata.nasa.gov/image-download?TIME=%s&' %time + \
    'extent=%s&epsg=3413&layers=%s&opacities=1&worldfile=true&' %(extent, layers) + \
    'format=image/jpeg&width=4530&height=3599'
    print("Query: " + query)

    urllib.urlretrieve(query, TMPDIR + "terra.zip")

    # UNZIPPING DOWNLOADED FILE
    print("Unzipping product...")
    try:
        zip_ref = zipfile.ZipFile(TMPDIR + 'terra' + '.zip')
        zip_ref.extractall(TMPDIR)
        zip_ref.close()
    except zipfile.BadZipfile:
        return False

    # FINDING FILE NAME
    tmpfile = glob.glob('tmp/**.jpg')[0]

    # PROCESSING FILE
    tileImage(tmpfile, outfile)
    buildImageOverviews(outfile)
    print('Terra MODIS mosaic is ready \n')
    return outfile

# --------------------------------- S1 CLOSE-UP ------------------------------- #
def getS1():
    outfile = OUTDIR + 's1c.tif'
    s1Name = getSentinelFiles()[0]
    if not s1Name:
        return False

    # PROCESSING FILE
    print("Processing files...")
    tmpfile = TMPDIR + 's1tmp.tif'
    print("Warping to NSIDC Sea Ice Polar Stereographic North projection")
    cmd = GDALHOME + 'gdalwarp -of GTiff -t_srs ' + PROJ + ' -tr 40 40 -order 3' + \
        ' -dstnodata 0 ' + s1Name + ' ' + tmpfile
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)

    tileImage(tmpfile, outfile)
    buildImageOverviews(outfile)
    print('Sentinel-1 image is ready \n')
    return outfile

# --------------------------------- S1 MOSAIC -------------------------------- #
def getS1Mos(bbox="bbox.geojson", max_num=4): # bbox should be .geojson format
    outfile = OUTDIR + "s1mos.tif" # name of the finished result

    tmpfiles = "" # arguments when making virtual mosaic
    downloadNames = getSentinelFiles(max_files=max_num)
    if not downloadNames:
        return False
    print(downloadNames)

    for i in range(len(downloadNames)):
        tmpfile = TMPDIR + 's1mostmp' + str(i) + '.tif'

        # PROCESSING EACH FILE
        print("Warping to NSIDC Sea Ice Polar Stereographic North projection")
        cmd = GDALHOME + 'gdalwarp -of GTiff -t_srs ' + PROJ + ' -tr 40 40 -order 3' + \
        ' -dstnodata 0 ' + downloadNames[i] + ' ' + tmpfile
        tmpfiles += tmpfile + ' '
        print("CMD: " + cmd)
        subprocess.call(cmd, shell=True)

    print('Making a virtual mosaic file')
    cmd = GDALHOME + 'gdalbuildvrt ' + TMPDIR + 'tmp.vrt ' + tmpfiles
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)

    print('Generating real, tiled mosaic from the virtual file')

    tileImage(TMPDIR + 'tmp.vrt', outfile)
    buildImageOverviews(outfile)
    print('Sentinel-1 mosaic is ready \n')
    return outfile


# --------------------------------- SeaIce ----------------------------------- #
def getSeaIce():
    outfile = OUTDIR + 'seaice.tif'

    # DOWNLOADING NEWEST FILE WITH HTTP
    month = DATE.strftime("%b").lower()
    yestdate = (DATE - timedelta(1)).strftime('%Y-%m-%d').replace('-', '')
    year = yestdate[:4]

    query = 'https://seaice.uni-bremen.de/data/amsr2/asi_daygrid_swath/n6250' + \
    '/%s/%s/Arctic/asi-AMSR2-n6250-%s-v5.tif' %(year, month, yestdate)
    print("Query: " + query)

    rawfile = TMPDIR + 'seaiceraw.tif'
    urllib.urlretrieve (query, rawfile)

    tmpfile = TMPDIR + 'seaicetmp.tif'
    tmpfile2 = TMPDIR + 'seaicetmp2.tif'

    # PROCESSING FILE
    print("Processing files...")
    print("Warping to NSIDC Sea Ice Polar Stereographic North projection")
    cmd = GDALHOME + 'gdalwarp -of GTiff -t_srs ' + PROJ + \
        ' -dstnodata 0 -dstalpha ' + rawfile + ' ' + tmpfile
    print("CMD: " + cmd)
    code = subprocess.call(cmd, shell=True)
    if code != 0:
        return False

    print('Converting from palette to rgba')
    cmd = '%spct2rgb.py -of GTiff -rgba %s %s' %(GDALHOME, tmpfile, tmpfile2)
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)

    tileImage(tmpfile2, outfile)
    buildImageOverviews(outfile, num=4)
    print('Sea ice concentration image is ready \n')
    return outfile


# --------------------------------- IceDrift --------------------------------- #
def getIceDrift():
    outfile = OUTDIR + 'icedrift.tif'

    # DOWNLOADING NEWEST FILE WITH FTP
    enddate = (DATE - timedelta(1)).strftime('%Y-%m-%d').replace('-', '')
    startdate = (DATE - timedelta(3)).strftime('%Y-%m-%d').replace('-', '')

    # startdate = "20180803" #TODO: remove
    # enddate = "20180805" #TODO: remove

    query = 'ftp://osisaf.met.no/prod/ice/drift_lr/merged/ice_drift_nh_' + \
    'polstere-625_multi-oi_%s1200-%s1200.nc' %(startdate, enddate)
    print('Query: ' + query)
    try:
        urllib.urlretrieve(query, 'tmpfile.nc')
    except IOError:
        return False

    # MAKE QUIVERPLOT FROM X AND Y DRIFT ESTIMATES
    print('Converting NETCDF bands to numpy arrays')
    fh = nc.Dataset('tmpfile.nc', mode='r')
    dx = (fh.variables['dX'][:][0])
    dy = (fh.variables['dY'][:][0])

    # GETTING DIMENSIONS
    xc = fh.dimensions['xc'].size
    yc = fh.dimensions['yc'].size
    x = np.linspace(0, xc, xc)
    y = np.linspace(yc, 0, yc)

    print('Making quiverplot from dX and dY ice drift estimates')
    fig = plt.figure(figsize=(11.9*3, 17.7*3), frameon=False) #TODO: fix hardcode
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    plt.quiver(x, y, dx, dy, scale=900, width=0.001)
    fig.savefig(TMPDIR + 'quivertmp.png', transparent=False, format='png')
    Image.open(TMPDIR + 'quivertmp.png').convert('L').save(TMPDIR + 'quivertmp.jpg','JPEG')

    # GETTING GEOREFERENCING INFO
    sizeX, sizeY, = Image.open(TMPDIR + 'quivertmp.jpg').size

    file_nc = 'NETCDF:"tmpfile.nc":dX'
    ds = gdal.Open(file_nc)
    gt = ds.GetGeoTransform()
    cornerX = gt[0]
    cornerY = gt[3]
    pxsizeX = gt[1]
    pxsizeY = gt[5]

    print(cornerX, cornerY, pxsizeX, pxsizeY)

    # Formula: new_pixel_size = (old_pixel_size / (new_im_size /old_im_size))
    new_pxsizeX = (pxsizeX / (sizeX / float(xc)))
    new_pxsizeY = (pxsizeY / (sizeY / float(yc)))

    jwg_string = "%s\n0.00000000000\n0.00000000000\n%s\n%s\n%s" \
     %(new_pxsizeX*1000, new_pxsizeY*1000, cornerX*1000, cornerY*1000)

    f = open(TMPDIR + "quivertmp.jgw", "w")
    f.write(jwg_string)
    f.close()

    # PROCESSING FILE
    print("Processing files...")

    tmpfile = TMPDIR + 'quivertmp.tif'
    tmpfile2 = TMPDIR + 'quivertmp2.tif'
    tmpfile3 = TMPDIR + 'quivertmp3.tif'

    print('Converting from worldfile to geotiff')
    cmd = '%sgdal_translate -of GTiff %s %s' %(GDALHOME, TMPDIR + 'quivertmp.jpg', tmpfile)
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)

    print('Removing noise around arrows')
    cmd = '%sgdal_calc.py -A %s --outfile=%s --calc="255*(A>220)"' %(GDALHOME, tmpfile, tmpfile2)
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)

    print("Warping to NSIDC Sea Ice Polar Stereographic North projection")
    cmd = GDALHOME + 'gdalwarp -t_srs ' + PROJ + \
        ' -srcnodata 255 -dstalpha ' + tmpfile2 + ' ' + tmpfile3
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)

    tileImage(tmpfile3, outfile)
    buildImageOverviews(outfile, num=4)
    print('Ice drift image is ready \n')
    return outfile



# ------------------------------ GETTING DATA -------------------------------- #
outfiles = [
    getS2(),
    getTerra(),
    getS1(),
    getS1Mos(),
    getSeaIce(),
    getIceDrift()
]
# outfiles = ['2018-08-08/s1c.tif', '2018-08-08/s2c.tif', '2018-08-08/terramos',
#     '2018-08-08/s1mos.tif', '2018-08-08/seaice.tif', '2018-08-08/icedrift.tif']
print('Created files: ' + str(outfiles) + '\n')

# ---------------------------- UPLOAD TO GEOSERVER ---------------------------- #
cat = Catalog("http://localhost:8080/geoserver/rest/", "admin", "geoserver")
# cat.create_workspace(str(DATE.date()), str(DATE.date()) + 'uri')

ws = cat.get_workspace( str(DATE.date()) )

for layerdata in outfiles:
    layername = layerdata.split('/')[1].split('.')[0]
    print('Adding ' + layername + ' to geoserver...')
    cat.create_coveragestore(name = layername,
                             data = layerdata,
                             workspace = ws,
                             overwrite = True)

print('Sensor data for ' + str(DATE.date()) + ' has been successfully uploaded!')
print('Process finished')









# ------------------------------ S1 MOSAIC (not used) ----------------------------- #
def makeProductsFile():
    api = SentinelAPI(COLHUB_UNAME, COLHUB_PW, 'https://colhub.met.no/#/home')

    date = DATE.strftime('%Y-%m-%d').replace('-', '')
    yestdate = (DATE - timedelta(2)).strftime('%Y-%m-%d').replace('-', '')
    results = []

    with open(TMPDIR + 'colhub_products.txt', 'w') as meta_file:
        # Splitting the footprint in two because the area is too big.
        footprint = geojson_to_wkt(read_geojson("articv1.geojson"))
        products = api.query(footprint,
                         (yestdate, date),
                         platformname='Sentinel-1',
                         producttype='GRD',
                         sensoroperationalmode='EW'
                         )

        products_df = api.to_dataframe(products)
        for i in range(len(products_df)):
            meta = api.get_product_odata(products_df.index[i], full=True)
            line = meta['id'] + ';' + meta['title'] + ';' + meta['footprint'] + \
                ';' + meta['Pass direction']
            print("Writing line: " + str(i) + "/" + str(len(products_df)) + ", ID: " + meta['id'])
            meta_file.write(line + '\n')
            results.append(meta['id'])

        footprint = geojson_to_wkt(read_geojson("articv2.geojson"))
        products = api.query(footprint,
                         (yestdate, date),
                         platformname='Sentinel-1',
                         producttype='GRD',
                         sensoroperationalmode='EW'
                         )

        products_df = api.to_dataframe(products)
        for i in range(len(products_df)):
            meta = api.get_product_odata(products_df.index[i], full=True)
            if (meta['id'] not in results): #Stop overlapping images from beeing added twice
                line = meta['id'] + ';' + meta['title'] + ';' + meta['footprint'] + \
                    ';' + meta['Pass direction']
                print("Writing line: " + str(i) + "/" + str(len(products_df)) + ", ID: " + meta['id'])
                meta_file.write(line + '\n')
            else:
                print("Skip duplicate file:" + str(i) + '/' + str(len(products_df)))


def downloadQuicklooks():
    with open(TMPDIR + 'colhub_products.txt', 'r') as infile:
        lines = infile.readlines()
        for line in lines:
            uuid, fname, polygon, direction = line.split(';')

            # Retrieve Quicklook
            o_fname = str(TMPDIR + 's1mos_output/' + fname + '.jpeg')
            query_string = "https://colhub.met.no/odata/v1/Products('%s')/Products('Quicklook')/\$value" %uuid
            wget_cmd = 'wget --no-check-certificate --continue --user="%s" --password="%s" --output-document="%s" "%s"' % (COLHUB_UNAME, COLHUB_PW, o_fname, query_string )

            # Run subprocess
            subprocess.call(wget_cmd, shell=True)

def s1applygcp(infile, outfile, gcps ):
    """ Apply GCPS in file by means of gdal_translate
        """

    cmd = str("gdal_translate -of GTiff -co \"COMPRESS=LZW\" " +
        "-a_srs \"+proj=longlat +ellps=WGS84\" ")
    for gcp in gcps:
        cmd = cmd + " -gcp " + gcp
    cmd = str(cmd +  " " + infile + " " + outfile)
    retcode = subprocess.call(cmd, shell=True)
    if retcode < 0:
        print 'Error in warping file %s' % infiles[band]
        sys.exit(-1)
    return os.path.isfile(outfile)

def s1warp(output_dir, output_fname, infile, d_srs):
    """ Regridding by means of gdal_warp. """
    outfile = str(output_dir + output_fname)

    gdal.Warp(outfile, infile, format='GTiff',
              dstSRS=d_srs, dstNodata=0)

    """ TEST APPLYING NEAR BLACK"""
    outfile_new = str(output_dir + 'near_black_' + output_fname)
    cmd = str("nearblack -of GTiff -co \"COMPRESS=LZW\" " +
        "-o %s %s ") %(outfile_new,outfile)
    retcode = subprocess.call(cmd, shell=True)
    os.remove(outfile)
    return os.path.isfile(outfile_new)

def s1_mosaic(vrt_mosaicFile,mosaicFile):
    print "\nCreating GeoTIFF mosaic"
    gdal.Warp(mosaicFile, vrt_mosaicFile, format='GTiff',
              srcNodata=0, dstNodata=0,outputType=gdal.GDT_Byte)
    return os.path.isfile(mosaicFile)


def s1_mosaic_vrt(infiles_path,vrt_mosaicFile):
    print "\nCreating vrt mosaic file"
    cmd = 'gdalbuildvrt -srcnodata 0 -vrtnodata 0 %s %s  ' % (vrt_mosaicFile, infiles_path)
    retcode = subprocess.call(cmd, shell=True)
    return os.path.isfile(vrt_mosaicFile)

def createS1Mosaic():
    with open(TMPDIR + 'colhub_products.txt', 'r') as infile:
        lines = infile.readlines()
        for line in lines:
            uuid, fname, polygon, direction = line.split(';')
            direction = direction.strip()


            img_file = str(TMPDIR + 's1mos_output/' + fname + '.jpeg')
            data = plt.imread(img_file)

            # OLD POLYGON CONV
            polygon_string = polygon.split('(')[2].split(')')[0]
            bb = [] # bounding box
            for pair in polygon_string.split(','):
                f_pair =  [coord for coord in pair.split()]
                bb.append(pair)
            lons = np.array([])

            for p in bb:
                lon, lat =  p.split()
                lons = np.append(lons,float(lon))

            gcps = []
            yMax = data.shape[0]
            xMax = data.shape[0]

            if direction == "ASCENDING":
                im_position = {'ul':'0 0', 'll':'0 %f' % yMax, 'ur':'%f 0' %xMax, 'lr': '%f %f' %(xMax, yMax)}
                im_idx = {'ul':0, 'll':3, 'ur':1, 'lr': 2}
            elif direction == "DESCENDING":
                im_position = {'ur':'0 0', 'lr':'0 %f' % yMax, 'ul':'%f 0' %xMax, 'll': '%f %f' %(xMax, yMax)}
                im_idx = {'ul':3, 'll':0, 'ur':2, 'lr': 1}

            for pos in im_position.keys():
                gcp = str(im_position[pos] + ' ' + bb[im_idx[pos]])
                gcps.append(gcp)

            gcp_fname = str(TMPDIR + 's1mos_translate/' + fname + '.tif')
            s1applygcp(img_file, gcp_fname ,gcps)
            d_srs = PROJ # NSIDC Ease 2
            out_dir = TMPDIR + 's1mos_warp/'
            out_name = str(fname + '.tif')
            if abs(lons.max()-lons.min()) > 300:
                print '\n Test this product manually! Errors for products crossing 180th-meridian %s' %fname
            else:
                s1warp(output_dir=out_dir, output_fname=out_name, infile=gcp_fname, d_srs=d_srs)

            warped_files = TMPDIR + 's1mos_warp/*.tif'
            vrt_mosaic_outfile = TMPDIR + 's1mos_vrt_mosaic/s1_mosaic_%s.vrt' %DATE.strftime('%Y-%m-%d_%H:%M')
            mosaic_outfile = 'latest_s1_mosaic.tif'

            # build virtual mosaic dataset
            vrt_ok = s1_mosaic_vrt(infiles_path=warped_files, vrt_mosaicFile=vrt_mosaic_outfile)
            mosaic_ok = s1_mosaic(vrt_mosaicFile=vrt_mosaic_outfile, mosaicFile=mosaic_outfile)

def getS1Mosaic():
    print("Fetching metadata...")
    makeProductsFile()
    print("Downloading quicklooks...")
    downloadQuicklooks()
    print("Generating mosaic...")
    createS1Mosaic()
    print("Sentinel-1 mosaic created!")
