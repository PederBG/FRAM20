"""
Download all sensor data needed to create the image layers.

S1 Close-up
S1 Mosaic using ESA's quicklooks
S1 Mosaic using raw data
Terra MODIS Mosaic

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

np.set_printoptions(threshold=np.nan) # for ice-drift quiverplot


GDALHOME = '/usr/bin/'
TMPDIR = 'tmp/'
RUNDIR = os.getcwd()
DATE = datetime.today()
TDIR = DATE.date()
COLHUB_UNAME = 'PederBG'
COLHUB_PW = 'Copernicus'
PROJ = 'EPSG:3413'

if not os.path.isdir(GDALHOME):
    print('GDALHOME path is not set')
    exit()

# if not os.path.isdir(TMPDIR):
#     subprocess.call('mkdir ' + TMPDIR, shell=True)
#     subprocess.call('mkdir ' + TMPDIR + 's1mos_output', shell=True)
#     subprocess.call('mkdir ' + TMPDIR + 's1mos_translate', shell=True)
#     subprocess.call('mkdir ' + TMPDIR + 's1mos_warp', shell=True)
#     subprocess.call('mkdir ' + TMPDIR + 's1mos_vrt_mosaic', shell=True)


def clean():
    s1Name = "yolo"
    cmd = 'rm -r ' + TMPDIR + ' && rm -r ' + s1Name + '*'
    subprocess.call(cmd, shell=True)


# --------------------------------- S1 CLOSE-UP ------------------------------- #

def getS1(bbox): # bbox should be .geojson format
    outfile = 's1c'
    api = SentinelAPI(COLHUB_UNAME, COLHUB_PW,
                  'https://colhub.met.no/#/home')
    date = DATE.strftime('%Y-%m-%d').replace('-', '')
    yestdate = (DATE - timedelta(1)).strftime('%Y-%m-%d').replace('-', '')

    footprint = geojson_to_wkt(read_geojson(bbox))
    products = api.query(footprint,
                     (yestdate, date),
                     platformname='Sentinel-1',
                     producttype='GRD',
                     sensoroperationalmode='EW'
                     )
    if len(products) == 0:
        print("No files found at date: " + date)
        quit()
    print("Found", len(products), "Sentinel-1 images.")

    products_df = api.to_dataframe(products).sort_values('size',
                    ascending=False).index[0]
    s1Name = api.get_product_odata(products_df)["title"]
    product_size = int(api.get_product_odata(products_df)["size"])
    #for i in range(len(products_df)):
    print "Name:", s1Name + ", size:", str(product_size / 1000000), "MB."
    api.download(products_df)

    # UNZIPPING DOWNLOADED FILE
    print("Unzipping product...")
    zip_ref = zipfile.ZipFile(s1Name + '.zip')
    zip_ref.extractall()
    zip_ref.close()

    # PROCESSING FILE
    print("Processing files...")
    tmpfile = TMPDIR + 's1tmp'
    print("Warping to NSIDC Sea Ice Polar Stereographic North projection")
    cmd = GDALHOME + 'gdalwarp -of GTiff -t_srs ' + PROJ + ' -tr 40 40 -order 3' + \
        ' -dstnodata 0 ' + s1Name + '.SAFE/manifest.safe ' + tmpfile + '.tif'
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)

    print('Tiling image and removing color bands')
    cmd = GDALHOME + 'gdal_translate -b 1 -co TILED=YES ' + tmpfile + '.tif ' + \
        outfile + '.tif'
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)

    print("Building overview images")
    cmd = GDALHOME + 'gdaladdo -r average ' + outfile + '.tif 2 4 8 16 32'
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)


# --------------------------------- TERRA MOSAIC ------------------------------- #
def getTerra():
    outfile = 'terramos'

    # DOWNLOADING NEWEST FILE WITH HTTP
    # time = str((date.today() - date(int(date.today().strftime('%Y')), 1, 1)).days -1)
    time = str(DATE.date()) # NASA changed the date format
    extent = '-2251630.1978347152,-1767716.822874052,2386588.9709421024,1917931.4225647242'
    layers = 'MODIS_Terra_CorrectedReflectance_TrueColor'

    query = 'https://gibs.earthdata.nasa.gov/image-download?TIME=%s&' %time + \
    'extent=%s&epsg=3413&layers=%s&opacities=1&worldfile=true&' %(extent, layers) + \
    'format=image/jpeg&width=4530&height=3599'
    print("Query: " + query)

    urllib.urlretrieve (query, TMPDIR + "terra.zip")

    # UNZIPPING DOWNLOADED FILE
    print("Unzipping product...")
    zip_ref = zipfile.ZipFile(TMPDIR + 'terra' + '.zip')
    zip_ref.extractall(TMPDIR)
    zip_ref.close()

    # FINDING FILE NAME
    tmpfile = glob.glob('tmp/**.jpg')[0]

    # PROCESSING FILE
    print('Converting jpg/jwg to tiled geotiff')
    cmd = GDALHOME + 'gdal_translate -of GTiff -co TILED=YES ' + tmpfile + ' ' + \
        outfile + '.tif'
    print("CMD: " + cmd)
    subprocess.call(str(cmd), shell=True)

    print("Building overview images")
    cmd = GDALHOME + 'gdaladdo -r average ' + outfile + '.tif 2 4 8 16 32'
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)


# --------------------------------- S1 MOSAIC -------------------------------- #
def getS1Mos(bbox="bbox.geojson", max_num=2): # bbox should be .geojson format
    outfile = "s1mos.tif" # name of the finished result

    api = SentinelAPI(COLHUB_UNAME, COLHUB_PW, 'https://colhub.met.no/#/home')
    # api = SentinelAPI(COLHUB_UNAME, COLHUB_PW, 'https://scihub.copernicus.eu/dhus/#/home')
    date = DATE.strftime('%Y-%m-%d').replace('-', '')
    yestdate = (DATE - timedelta(1)).strftime('%Y-%m-%d').replace('-', '')

    footprint = geojson_to_wkt(read_geojson(bbox))
    products = api.query(footprint,
                    #  ("20180804", "20180805"),
                     (yestdate, date),
                     platformname='Sentinel-1',
                     producttype='GRD',
                     sensoroperationalmode='EW'
                     )
    if len(products) == 0:
        print("No files found at date: " + date)
        quit()
    print("Found", len(products), "Sentinel-1 images.")

    products_df = api.to_dataframe(products) #.sort_values('size', ascending=True)

    downloadNames = []

    for i in range(len(products_df)):
        if i == max_num: # Prevents too large mosaic file
            break
        product_size = int(api.get_product_odata(products_df.index[i])["size"])
        product_name = api.get_product_odata(products_df.index[i])["title"]
        downloadNames.append(product_name)
        print "Name:", product_name, "size:", str(product_size / 1000000), "MB."

        api.download(products_df.index[i])

    # downloadNames = ['S1A_EW_GRDM_1SDH_20180804T082602_20180804T082707_023094_028204_8657',
    #                  'S1B_EW_GRDM_1SDH_20180804T091444_20180804T091524_012111_0164D0_6844'
    #                 ]

    tmpfiles = "" # arguments when making virtual mosaic

    for i in range(len(downloadNames)):

        # UNZIPPING DOWNLOADED FILE
        print("Unzipping product...")
        zip_ref = zipfile.ZipFile(downloadNames[i] + '.zip')
        zip_ref.extractall(TMPDIR)
        zip_ref.close()

        geofiles = glob.glob(downloadNames[i] + '.SAFE/measurement/*')
        # FINDING RIGHT POLARIZATION FILE (now using HH-polarization)
        if '-hh-' in geofiles[0]:
            geofile = geofiles[0]
        else:
            geofile = geofiles[1]

        tmpfile = TMPDIR + 's1mostmp' + str(i) + '.tif'

        # PROCESSING EACH FILE
        print("Warping to NSIDC Sea Ice Polar Stereographic North projection")
        cmd = GDALHOME + 'gdalwarp -of GTiff -t_srs ' + PROJ + ' -tr 40 40 -order 3' + \
        ' -dstnodata 0 ' + geofile + ' ' + tmpfile
        tmpfiles += tmpfile + ' '
        print("CMD: " + cmd)
        subprocess.call(cmd, shell=True)

    print('Making a virtual mosaic file')
    cmd = GDALHOME + 'gdalbuildvrt ' + TMPDIR + 'tmp.vrt ' + tmpfiles
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)

    print('Generating real, tiled mosaic from the virtual file')
    cmd = GDALHOME + 'gdal_translate -co TILED=YES ' + TMPDIR + 'tmp.vrt ' + outfile
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)

    print("Building overview images")
    cmd = GDALHOME + 'gdaladdo -r average ' + outfile + ' 2 4 8 16 32'
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)


# --------------------------------- SeaIce ----------------------------------- #
def getSeaIce():
    outfile = 'seaice.tif'

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
    subprocess.call(cmd, shell=True)

    print('Converting from palette to rgba')
    cmd = '%spct2rgb.py -of GTiff -rgba %s %s' %(GDALHOME, tmpfile, tmpfile2)
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)

    print('Tiling image')
    cmd = '%sgdal_translate -co TILED=YES %s %s' %(GDALHOME, tmpfile2, outfile)
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)

    print("Building overview images")
    cmd = '%sgdaladdo -r average %s 2 4 8 16 32' %(GDALHOME, outfile)
    print("CMD: " + cmd)
    subprocess.call(cmd, shell=True)


# --------------------------------- IceDrift --------------------------------- #


def getIceDrift():
    outfile = 'icedrift.tif'

    # TODO: Difference between sh-polstere and nh-polstere ice drift ??

    # DOWNLOADING NEWEST FILE WITH FTP
    enddate = DATE.strftime('%Y-%m-%d').replace('-', '')
    startdate = (DATE - timedelta(2)).strftime('%Y-%m-%d').replace('-', '')

    startdate = "20180803" #TODO: remove
    enddate = "20180805" #TODO: remove

    query = 'ftp://osisaf.met.no/prod/ice/drift_lr/merged/ice_drift_sh_' + \
    'polstere-625_multi-oi_%s1200-%s1200.nc' %(startdate, enddate)
    # urllib.urlretrieve(query, 'tmpfile.nc')

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
    Image.open(TMPDIR + 'quivertmp.png').convert('RGB').save(TMPDIR + 'quivertmp.jpg','JPEG')

    # GETTING GEOREFERENCING INFO
    sizeX, sizeY, = Image.open(TMPDIR + 'quivertmp.jpg').size

    file_nc = 'NETCDF:"tmpfile.nc":dX'
    ds = gdal.Open(file_nc)
    gt = ds.GetGeoTransform()
    cornerX = gt[0]
    cornerY = gt[3]
    pxsizeX = gt[1]
    pxsizeY =-gt[5]

    # TODO: new_pixel_size = (old_pixel_size / (new_im_size /old_im_size)) * 1000

    print(cornerX, cornerY, pxsizeX, pxsizeY)

    f = open(TMPDIR + "quivertmp.jwg", "w")
    f.write()


getIceDrift()











# ------------------------------ S1 MOSAIC (old) ----------------------------- #
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
