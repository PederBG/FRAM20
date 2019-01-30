"""
Written by PederBG, 2018-08

This class handles downloading and processing of up-to-date sensor data from
multiple sources.

Layers:
    Sentinel-1 Optic Image Close-up (s2c)
    Terra MODIS Optic Mosaic (terramos)
    Sentinel-1 SAR High Resolution Close-up (s1c)
    Sentinel-1 SAR Lower Resolution Mosaic (s1mos)
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
import gdal
from gdalconst import *
import urllib, urllib2
import Image
import netCDF4 as nc

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import fram_functions as funcs

np.set_printoptions(threshold=sys.maxsize) # for ice-drift quiverplot

class DownloadManager(object):

    def __init__(self, **kwargs):

        # Argument options
        self.DATE = datetime.today().date()
        self.GRID = False
        self.BBOX = 'bbox.geojson'
        self.LARGEBBOX = 'bbox.geojson'
        self.OUTDIR = None
        self.TMPDIR = None

        # Static options
        self.GDALHOME = '/usr/bin/'
        self.TMPDIR = 'tmp/'
        self.RUNDIR = os.getcwd()
        self.COLHUB_UNAME = os.environ["COLHUB_USERNAME"]
        self.COLHUB_PW = os.environ["COLHUB_PASSWORD"]
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

        # Delete old tmp dir and data content
        print(('rm ' + self.TMPDIR + ' ' + self.OUTDIR))
        subprocess.call('rm -r ' + self.TMPDIR + ' ' + self.OUTDIR, shell=True)

        # Make dirs if they don't exist
        if not os.path.isdir(self.TMPDIR):
            print('Making TMPDIR...')
            subprocess.call('mkdir ' + self.TMPDIR, shell=True)
        if not os.path.isdir(self.OUTDIR):
            print('Making OUTDIR...')
            subprocess.call('mkdir -p ' + self.OUTDIR, shell=True)

        if (self.GRID):
            self.BBOX = funcs.makeGeojson(self.GRID, self.TMPDIR + str(self.DATE) + '.geojson', 1, 1, 0.01, 0.01)
            self.LARGEBBOX = funcs.makeGeojson(self.GRID, self.TMPDIR + str(self.DATE) + '_large.geojson', 20, 70, 1.5, 6)


        # Check gdalhome path
        if not os.path.isdir(self.GDALHOME):
            print('GDALHOME path is not set')
            sys.exit(1)

        # Make layer info file
        self.infoFile = open(self.TMPDIR + 'layerinfo.txt', 'a+')

    # ---------------------------------------------------------

    # Download and process each layer...

    # ------------------------------ S2 CLOSE-UP ----------------------------- #
    def getS2(self, outfile):
        s2Name = funcs.getSentinelFiles(self.DATE, self.COLHUB_UNAME, self.COLHUB_PW, self.TMPDIR, self.BBOX, platform='s2')[0]
        if not s2Name:
            return False
        s2FileName = '/vsizip/%s%s.zip/%s.SAFE/MTD_MSIL1C.xml' %(self.TMPDIR, s2Name, s2Name)

        ds = gdal.Open(s2FileName, GA_ReadOnly)
        rawEPSG = ds.GetSubDatasets()[0][0].split(':')[-1]

        # Get layerInfoFile
        self.infoFile.write('s2c_time|' + str(ds.GetMetadataItem("PRODUCT_START_TIME") + "\n"))
        self.infoFile.write('s2c_clouds|' + str(ds.GetMetadataItem("CLOUD_COVERAGE_ASSESSMENT") + "\n"))
        self.infoFile.close()
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
        tmpfile = glob.glob(self.TMPDIR + 'nasa-worldview-**.jpg')[0]

        # PROCESSING FILE
        funcs.tileImage(self.GDALHOME, tmpfile, outfile)
        funcs.buildImageOverviews(self.GDALHOME, outfile)
        print('Terra MODIS mosaic is ready \n')
        return outfile

    # --------------------------------- S1 CLOSE-UP ------------------------------- #
    def getS1(self, outfile, max_num=3):

        tmpfiles = '' # arguments when making virtual mosaic
        downloadNames = funcs.getSentinelFiles(self.DATE, self.COLHUB_UNAME, self.COLHUB_PW, self.TMPDIR, self.BBOX, max_files=max_num)
        if not downloadNames[0]:
            return False

        for i in range(len(downloadNames)):
            tmpfile = self.TMPDIR + 's1tmp_' + str(i) + '.tif'

            funcs.warpImage(self.GDALHOME, self.PROJ, '-tr 40 40 -order 3 -dstnodata 0', downloadNames[i], tmpfile)
            tmpfiles = tmpfile + ' ' + tmpfiles

        print('Making a virtual mosaic file...')
        cmd = self.GDALHOME + 'gdalbuildvrt ' + self.TMPDIR + 'tmp1.vrt ' + tmpfiles
        subprocess.call(cmd, shell=True)

        print('Generating real, tiled mosaic from the virtual file...')

        funcs.tileImage(self.GDALHOME, self.TMPDIR + 'tmp1.vrt', outfile)
        funcs.buildImageOverviews(self.GDALHOME, outfile)
        print('Sentinel-1 high resolution image is ready \n')
        return outfile

    # --------------------------------- S1 MOSAIC -------------------------------- #
    def getS1Mos(self, outfile, max_num=50):

        tmpfiles = "" # arguments when making virtual mosaic
        downloadNames = funcs.getSentinelFiles(self.DATE, self.COLHUB_UNAME, self.COLHUB_PW, self.TMPDIR, self.LARGEBBOX, max_files=max_num, time_window=1)
        if not downloadNames[0]:
            return False

        for i in range(len(downloadNames)):
            tmpfile = self.TMPDIR + 's1mostmp_' + str(i) + '.tif'
            tmpfile2 = self.TMPDIR + 's1mostmp2_' + str(i) + '.tif'

            # PROCESSING EACH FILE
            print('Converting image to lower resolution...')
            cmd = self.GDALHOME + 'gdal_translate -of GTiff -outsize 20% 20% ' + downloadNames[i] + ' ' + tmpfile
            print(cmd)
            subprocess.call(cmd, shell=True)

            funcs.warpImage(self.GDALHOME, self.PROJ, '-order 3 -dstnodata 0', tmpfile, tmpfile2)
            tmpfiles = tmpfile2 + ' ' + tmpfiles

        print('Making a virtual mosaic file...')
        cmd = self.GDALHOME + 'gdalbuildvrt ' + self.TMPDIR + 'tmp2.vrt ' + tmpfiles
        subprocess.call(cmd, shell=True)

        print('Generating real, tiled mosaic from the virtual file...')

        funcs.tileImage(self.GDALHOME, self.TMPDIR + 'tmp2.vrt', outfile)
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
        fig = plt.figure(figsize=(11.9*5, 17.7*3), frameon=False) #TODO: fix hardcode
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)
        plt.quiver(x, y, dx, dy, width=0.0007)
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

        # MAKING JGW FILE USED FOR GEOREFERENCING
        jgw_string = "%s\n0.00000000000\n0.00000000000\n%s\n%s\n%s" \
         %(new_pxsizeX*1000, new_pxsizeY*1000, cornerX*1000, cornerY*1000)

        f = open(self.TMPDIR + "quivertmp.jgw", "w")
        f.write(jgw_string)
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
