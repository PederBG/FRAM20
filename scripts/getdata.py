#! /usr/bin/env python

"""
Written by PederBG, 2018-08

This script will download and process up-to-date sensor data from multiple sources
and upload them as GeoTiff layers in a running geoserver. The geoserver will then
handle feeding layer-tiles to the front-end on request.

The script is meant to run as a cron job.

Layers:
    Sentinel-1 Optic Image Close-up (s2c)

    Terra MODIS Optic Mosaic (terramos)

    Sentinel-1 SAR High Resolution Close-up (s1c)

    Sentinel-1 SAR High Resolution Mosaic (s1mos)

    AMSR-2 Global Sea Ice Concentration (seaice)

    Low Resolution Sea Ice Drift (icedrift)

    S1 Mosaic using ESA's quicklooks (not in use)


NOTE: This script is written for Python 2.7. This is due to some library restrictions.

"""

from datetime import date, datetime, timedelta
from sentinelsat.sentinel import SentinelAPI, read_geojson, geojson_to_wkt
import zipfile
import os, sys, subprocess, glob, getopt
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
import gdal
from gdalconst import *
import urllib, urllib2
import Image
import netCDF4 as nc
from geoserver.catalog import Catalog

import fram_functions as funcs

np.set_printoptions(threshold=np.nan) # for ice-drift quiverplot

class Download(object):

    def __init__(self, **kwargs):

        # Argument options
        self.DATE = datetime.today().date()
        self.GRID = False
        self.BBOX = 'bbox.geojson'
        self.OUTDIR = None
        self.TMPDIR = None

        # Static options
        self.GDALHOME = '/usr/bin/'
        self.TMPDIR = 'tmp/'
        self.RUNDIR = os.getcwd()
        self.COLHUB_UNAME = 'PederBG'
        self.COLHUB_PW = 'Copernicus' # Not sensitiv data
        self.PROJ = 'EPSG:3413'
        self.PATH = os.path.dirname(os.path.realpath(__file__)) + '/'

        if( kwargs.get('date') ):
            self.DATE = kwargs.get('date')

        self.OUTDIR = self.PATH + str(self.DATE) + '/'
        self.TMPDIR = self.PATH + 'tmp/'

        if( kwargs.get('grid') ):
            self.GRID = kwargs.get('grid')

        if( kwargs.get('target') ):
            self.OUTDIR = kwargs.get('target') + '/' + str(self.DATE) + '/'


        # Make dirs if they don't exist
        if not os.path.isdir(self.TMPDIR):
            print('Making TMPDIR...')
            subprocess.call('mkdir ' + self.TMPDIR, shell=True)
        if not os.path.isdir(self.OUTDIR):
            print('Making OUTDIR...')
            subprocess.call('mkdir ' + self.OUTDIR, shell=True)

        if (self.GRID):
            self.BBOX = funcs.makeGeojson(self.GRID, self.TMPDIR + str(self.DATE) + '.geojson')


        # Check gdalhome path
        if not os.path.isdir(self.GDALHOME):
            print('GDALHOME path is not set')
            sys.exit(1)

    # ---------------------------------------------------------

    # Getting and processing each layer...

    # ------------------------------ S2 CLOSE-UP ----------------------------- #
    def getS2(self, outfile):
        s2Name = funcs.getSentinelFiles(self.DATE, self.COLHUB_UNAME, self.COLHUB_PW, self.TMPDIR, self.BBOX, platform='s2')[0]
        if not s2Name:
            return False
        s2FileName = '/vsizip/%s%s.zip/%s.SAFE/MTD_MSIL1C.xml' %(self.TMPDIR, s2Name, s2Name)

        ds = gdal.Open(s2FileName, GA_ReadOnly)
        rawEPSG = ds.GetSubDatasets()[0][0].split(':')[-1]
        ds = None

        s2FullName = 'SENTINEL2_L1C:"%s":TCI:%s' %(s2FileName, rawEPSG)

        tmpfile = self.TMPDIR + 's2tmp.tif'

        # PROCESSING FILE
        print("Processing files...")
        funcs.warpImage(self.GDALHOME, self.PROJ, '-tr 10 10 -order 3 -srcnodata 0 -dstalpha', s2FullName, tmpfile)

        funcs.tileImage(self.GDALHOME, tmpfile, outfile)
        funcs.buildImageOverviews(self.GDALHOME, outfile)
        print('Sentinel-2 image is ready \n')
        return outfile

    # --------------------------------- TERRA MOSAIC ------------------------------- #
    def getTerra(self, outfile):
        # DOWNLOADING NEWEST FILE WITH HTTP
        # time = str((date.today() - date(int(date.today().strftime('%Y')), 1, 1)).days -1)
        time = str(self.DATE) # NASA changed the date format
        extent = '-2251630.1978347152,-1767716.822874052,2386588.9709421024,1917931.4225647242'
        layers = 'MODIS_Terra_CorrectedReflectance_TrueColor'

        query = 'https://gibs.earthdata.nasa.gov/image-download?TIME=%s&' %time + \
        'extent=%s&epsg=3413&layers=%s&opacities=1&worldfile=true&' %(extent, layers) + \
        'format=image/jpeg&width=4530&height=3599'
        print("Query: " + query)

        with open(self.TMPDIR + "terra.zip",'wb') as f:
            try:
                f.write(urllib2.urlopen(query).read())
                print(self.TMPDIR + "terra.zip")
                f.close()
            except urllib2.HTTPError, e:
                print('Can not retrieve data. Error code: %s' %(str(e.code)))
                f.close()
                return False

        # UNZIPPING DOWNLOADED FILE
        print("Unzipping product...")
        try:
            zip_ref = zipfile.ZipFile(self.TMPDIR + 'terra' + '.zip')
            zip_ref.extractall(self.TMPDIR)
            zip_ref.close()
        except zipfile.BadZipfile:
            return False

        # FINDING FILE NAME
        tmpfile = glob.glob(self.TMPDIR + '**.jpg')[0]

        # PROCESSING FILE
        funcs.tileImage(self.GDALHOME, tmpfile, outfile)
        funcs.buildImageOverviews(self.GDALHOME, outfile)
        print('Terra MODIS mosaic is ready \n')
        return outfile

    # --------------------------------- S1 CLOSE-UP ------------------------------- #
    def getS1(self, outfile):
        s1Name = funcs.getSentinelFiles(self.DATE, self.COLHUB_UNAME, self.COLHUB_PW, self.TMPDIR, self.BBOX)[0]
        if not s1Name:
            return False

        # PROCESSING FILE
        print("Processing files...")
        tmpfile = self.TMPDIR + 's1tmp.tif'
        funcs.warpImage(self.GDALHOME, self.PROJ, '-tr 40 40 -order 3 -dstnodata 0', s1Name, tmpfile)

        funcs.tileImage(self.GDALHOME, tmpfile, outfile)
        funcs.buildImageOverviews(self.GDALHOME, outfile)
        print('Sentinel-1 image is ready \n')
        return outfile

    # --------------------------------- S1 MOSAIC -------------------------------- #
    def getS1Mos(self, outfile, max_num=3):

        tmpfiles = "" # arguments when making virtual mosaic
        downloadNames = funcs.getSentinelFiles(self.DATE, self.COLHUB_UNAME, self.COLHUB_PW, self.TMPDIR, self.BBOX, max_files=max_num)
        if not downloadNames[0]:
            return False

        for i in range(len(downloadNames)):
            tmpfile = self.TMPDIR + 's1mostmp' + str(i) + '.tif'

            # PROCESSING EACH FILE
            funcs.warpImage(self.GDALHOME, self.PROJ, '-tr 40 40 -order 3 -dstnodata 0', downloadNames[i], tmpfile)
            tmpfiles += tmpfile + ' '

        print('Making a virtual mosaic file')
        cmd = self.GDALHOME + 'gdalbuildvrt ' + self.TMPDIR + 'tmp.vrt ' + tmpfiles
        subprocess.call(cmd, shell=True)

        print('Generating real, tiled mosaic from the virtual file')

        funcs.tileImage(self.GDALHOME, self.TMPDIR + 'tmp.vrt', outfile)
        funcs.buildImageOverviews(self.GDALHOME, outfile)
        print('Sentinel-1 mosaic is ready \n')
        return outfile


    # --------------------------------- SeaIce ----------------------------------- #
    def getSeaIce(self, outfile):
        # DOWNLOADING NEWEST FILE WITH HTTP
        yestdate = (self.DATE - timedelta(1)).strftime('%Y%m%d')
        month = (self.DATE - timedelta(1)).strftime("%b").lower()
        year = yestdate[:4]

        query = 'https://seaice.uni-bremen.de/data/amsr2/asi_daygrid_swath/n6250' + \
        '/%s/%s/Arctic/asi-AMSR2-n6250-%s-v5.tif' %(year, month, yestdate)
        print("Query: " + query)

        rawfile = self.TMPDIR + 'seaiceraw.tif'
        with open(rawfile,'wb') as f:
            try:
                f.write(urllib2.urlopen(query).read())
                f.close()
            except urllib2.HTTPError, e:
                print('Can not retrieve data. Error code: %s' %(str(e.code)))
                f.close()
                return False

        tmpfile = self.TMPDIR + 'seaicetmp.tif'
        tmpfile2 = self.TMPDIR + 'seaicetmp2.tif'

        # PROCESSING FILE
        print("Processing files...")
        code = funcs.warpImage(self.GDALHOME, self.PROJ, '-dstnodata 0 -dstalpha', rawfile, tmpfile)
        if code != 0:
            return False

        print('Converting from palette to rgba')
        cmd = '%spct2rgb.py -of GTiff -rgba %s %s' %(self.GDALHOME, tmpfile, tmpfile2)
        subprocess.call(cmd, shell=True)

        funcs.tileImage(self.GDALHOME, tmpfile2, outfile)
        funcs.buildImageOverviews(self.GDALHOME, outfile, num=4)
        print('Sea ice concentration image is ready \n')
        return outfile


    # --------------------------------- IceDrift --------------------------------- #
    def getIceDrift(self, outfile):
        # DOWNLOADING NEWEST FILE WITH FTP
        enddate = (self.DATE - timedelta(1)).strftime('%Y%m%d')
        startdate = (self.DATE - timedelta(3)).strftime('%Y%m%d')
        m = (self.DATE - timedelta(1)).strftime('%m')
        Y = (self.DATE - timedelta(1)).strftime('%Y')

        query = 'ftp://osisaf.met.no/archive/ice/drift_lr/merged/%s/%s/ice_drift_' \
        'nh_polstere-625_multi-oi_%s1200-%s1200.nc' %(Y, m, startdate, enddate)
        print('Query: ' + query)
        tmpfile = self.TMPDIR + 'tmpfile.nc'
        try:
            urllib.urlretrieve(query, tmpfile)
        except IOError:
            print("Could not download image")
            return False


        # MAKE QUIVERPLOT FROM X AND Y DRIFT ESTIMATES
        print('Converting NETCDF bands to numpy arrays')
        fh = nc.Dataset(tmpfile, mode='r')
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
        plt.quiver(x, y, dx, dy, scale=1100, width=0.0007)
        fig.savefig(self.TMPDIR + 'quivertmp.png', transparent=False, format='png')
        Image.open(self.TMPDIR + 'quivertmp.png').convert('L').save(self.TMPDIR + 'quivertmp.jpg','JPEG')

        # GETTING GEOREFERENCING INFO
        sizeX, sizeY, = Image.open(self.TMPDIR + 'quivertmp.jpg').size

        file_nc = 'NETCDF:"' + tmpfile + '":dX'
        ds = gdal.Open(file_nc)
        gt = ds.GetGeoTransform()
        cornerX = gt[0]
        cornerY = gt[3]
        pxsizeX = gt[1]
        pxsizeY = gt[5]

        print(cornerX, cornerY, pxsizeX, pxsizeY)

        # Formula: new_pixel_size = (old_pixel_size / (new_im_size / old_im_size))
        new_pxsizeX = (pxsizeX / (sizeX / float(xc)))
        new_pxsizeY = (pxsizeY / (sizeY / float(yc)))

        jwg_string = "%s\n0.00000000000\n0.00000000000\n%s\n%s\n%s" \
         %(new_pxsizeX*1000, new_pxsizeY*1000, cornerX*1000, cornerY*1000)

        f = open(self.TMPDIR + "quivertmp.jgw", "w")
        f.write(jwg_string)
        f.close()

        # PROCESSING FILE
        print("Processing files...")

        tmpfile = self.TMPDIR + 'quivertmp.tif'
        tmpfile2 = self.TMPDIR + 'quivertmp2.tif'
        tmpfile3 = self.TMPDIR + 'quivertmp3.tif'

        print('Converting from worldfile to geotiff...')
        cmd = '%sgdal_translate -of GTiff %s %s' %(self.GDALHOME, self.TMPDIR + 'quivertmp.jpg', tmpfile)
        subprocess.call(cmd, shell=True)

        print('Removing noise around arrows...')
        cmd = '%sgdal_calc.py -A %s --outfile=%s --calc="255*(A>220)"' %(self.GDALHOME, tmpfile, tmpfile2)
        subprocess.call(cmd, shell=True)

        funcs.warpImage(self.GDALHOME, self.PROJ, '-srcnodata 255 -dstalpha', tmpfile2, tmpfile3)
        funcs.tileImage(self.GDALHOME, tmpfile3, outfile)
        funcs.buildImageOverviews(self.GDALHOME, outfile, num=4)
        print('Ice drift image is ready \n')
        return outfile

# --------------------------- END CLASS DOWNLOAD  ---------------------------- #



# --------------------------- GETTING DATA (MAIN) ---------------------------- #
def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hd:g:t:o:",["help", "test", "date=","grid=","target=","only=","overwrite"])
    except getopt.GetoptError:
        print('Invalid arguments. Add "-h" or "--help" for help.')
        sys.exit(1)

    date, grid, only, target, overwrite = None, None, None, None, False
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('Usage: ./getdata.py [OPTIONS...]\n\nHelp options:\n\
-h, --help       Show help\n\
--test           Test that all packages and system variables work properly\n\
-d, --date       Set date for all imagery capture (format: yyyy-mm-dd / yyyymmdd)\n\
-g, --grid       Set center grid for sentinel imagery capture (format: east-decimal,north-decimal)\n\
-t, --target     Set path to target directory (format: path/to/target)\n\
-o, --only       Only create specified layer (format: layername)\n\
--overwrite      Overwrite layers in geoserver'
            )
            sys.exit()
        elif opt == ("--test"):
            print("All packages and sytem variables seems to work properly.")
            sys.exit()
        elif opt in ("-d", "--date"):
            if '-' in arg:
                date = datetime.strptime(arg, '%Y-%m-%d').date()
            else:
                date = datetime.strptime(arg, '%Y%m%d').date()
        elif opt in ("-g", "--grid"):
            grid = arg
        elif opt in ("-t", "--target"):
            target = arg
        elif opt in ("-o", "--only"):
            only = arg
        elif opt in ("--overwrite"):
            overwrite = True
    if not opts:
        print('WARNING: No arguments provided. Using defaults.')
    # ---------------------------------------

    d = Download(date=date, grid=grid, target=target) # Making download instance

    functions = {
        's2c' : d.getS2,
        'terramos' : d.getTerra,
        's1c' : d.getS1,
        's1mos' : d.getS1Mos,
        'seaice' : d.getSeaIce,
        'icedrift' : d.getIceDrift
    }

    outfiles = []
    if only:
        outfiles.append( functions[only](d.OUTDIR + only + '.tif') )
    else:
        for k, v in functions.iteritems():
            funcs.printLayerStatus(str(k))
            outfiles.append( v(d.OUTDIR + k + '.tif') )
            print("")

    print('Created files: ' + str(outfiles) + '\n')
    # d.clean()

    # ---------------------------- UPLOAD TO GEOSERVER ---------------------------- #
    cat = Catalog("http://localhost:8080/geoserver/rest/", "admin", "geoserver")

    ws = cat.get_workspace( str(d.DATE) )
    if ws is None:
        cat.create_workspace(str(d.DATE), str(d.DATE) + 'uri')

    for layerdata in outfiles:
        if layerdata:
            layername = layerdata.split('/')[-1].split('.')[0]
            print('Adding ' + layername + ' to geoserver...')
            cat.create_coveragestore(name = layername,
                                     data = layerdata,
                                     workspace = ws,
                                     overwrite = overwrite)

    print('Sensor data for ' + str(d.DATE) + ' has been successfully uploaded!')
    print('Process finished')


if __name__ == "__main__":
    main(sys.argv[1:])
