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
import os, sys, subprocess, glob, getopt
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
import gdal
import urllib
import Image
import netCDF4 as nc
from geoserver.catalog import Catalog

np.set_printoptions(threshold=np.nan) # for ice-drift quiverplot

class Command(object):

    def __init__(self):
        # Argument options
        self.DATE = datetime.today().date()
        self.GRID = False
        self.BBOX = "bbox.geojson" # default

        # Static options
        self.GDALHOME = '/usr/bin/'
        self.TMPDIR = 'tmp/'
        self.OUTDIR = str(self.DATE) + '/'
        self.RUNDIR = os.getcwd()
        self.COLHUB_UNAME = 'PederBG'
        self.COLHUB_PW = 'Copernicus'
        self.PROJ = 'EPSG:3413'


        if not os.path.isdir(self.GDALHOME):
            print('GDALHOME path is not set')
            exit()

    def makeDirs(self):
        self.OUTDIR = str(self.DATE) + '/'
        if not os.path.isdir(self.TMPDIR):
            subprocess.call('mkdir ' + self.TMPDIR, shell=True)
        if not os.path.isdir(self.OUTDIR):
            subprocess.call('mkdir ' + self.OUTDIR, shell=True)

    def clean(self):
        s1Name = "yolo"
        cmd = 'rm -r ' + self.TMPDIR + ' && rm -r ' + s1Name + '*'
        subprocess.call(cmd, shell=True)

    # --------------------------------- HELP FUNCTIONS------------------------------- #
    def getSentinelFiles(self, bbox, max_files=1, polarization='hh', platform='s1'):
        print('Arguments -> Box: %s, Max downloads: %s, Polarization: %s, Platform: %s' \
            %(bbox, max_files, polarization, platform))
        # api = SentinelAPI(self.COLHUB_UNAME, self.COLHUB_PW, 'https://colhub.met.no/#/home')
        api = SentinelAPI(self.COLHUB_UNAME, self.COLHUB_PW, 'https://scihub.copernicus.eu/dhus/#/home')
        date = self.DATE.strftime('%Y%m%d')
        yestdate = (self.DATE - timedelta(1)).strftime('%Y%m%d')

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
            # downloadNames.append(self.TMPDIR + product_name)
            print "Name:", product_name, "size:", str(product_size / 1000000), "MB."

            api.download(products_df.index[i], self.TMPDIR)

            if platform == 's1':
                # UNZIPPING DOWNLOADED FILE
                print("Unzipping product...")
                zip_ref = zipfile.ZipFile(self.TMPDIR + product_name + '.zip')
                zip_ref.extractall(self.TMPDIR)
                zip_ref.close()

                geofiles = glob.glob(self.TMPDIR + product_name + '.SAFE/measurement/*')
                # FINDING RIGHT POLARIZATION FILE (now using HH-polarization)
                if '-' + polarization + '-' in geofiles[0]:
                    downloadNames.append(geofiles[0])
                else:
                    downloadNames.append(geofiles[1])

            elif platform == 's2':
                downloadNames.append(product_name)
        return downloadNames

    def tileImage(self, infile, outfile):
        print('Tiling image')
        cmd = '%sgdal_translate -of GTiff -co TILED=YES %s %s' %(self.GDALHOME, infile, outfile)
        subprocess.call(cmd, shell=True)


    def buildImageOverviews(self, outfile, num=5):
        print("Building overview images")
        opt = ['2', '4', '8', '16', '32', '64']
        overviews = ""
        for i in range(num):
            overviews += opt[i] + ' '
        cmd = '%sgdaladdo -r average %s %s' %(self.GDALHOME, outfile, overviews[:-1])
        subprocess.call(cmd, shell=True)
    #-------------------------------------------------------------------------------#

    # --------------------------------- S2 CLOSE-UP ------------------------------- #
    def getS2(self):
        outfile = self.OUTDIR + 's2c.tif'
        # s2Name = self.getSentinelFiles(self.BBOX, platform='s2')[0]
        s2Name = 'S2A_MSIL1C_20180807T164901_N0206_R026_T27XWM_20180807T201734'
        if not s2Name:
            return False
        # s2Name = 'S2A_MSIL1C_20180806T171901_N0206_R012_T27XWM_20180806T204942'

        s2FullName = 'SENTINEL2_L1C:"/vsizip/%s%s.zip/%s.SAFE/MTD_MSIL1C.xml":TCI:EPSG_32627' \
            %(self.TMPDIR, s2Name, s2Name)

        tmpfile = self.TMPDIR + 's2tmp.tif'

        # PROCESSING FILE
        print("Processing files...")
        print("Warping to NSIDC Sea Ice Polar Stereographic North projection")
        cmd = self.GDALHOME + 'gdalwarp -of GTiff -t_srs ' + self.PROJ + ' -tr 10 10 -order 3' + \
            ' -srcnodata 0 -dstalpha ' + s2FullName + ' ' + tmpfile
        print("CMD: " + cmd)
        subprocess.call(cmd, shell=True)

        self.tileImage(tmpfile, outfile)
        self.buildImageOverviews(outfile)
        print('Sentinel-2 image is ready \n')
        return outfile

    # --------------------------------- TERRA MOSAIC ------------------------------- #
    def getTerra(self):
        outfile = self.OUTDIR + 'terramos'

        # DOWNLOADING NEWEST FILE WITH HTTP
        # time = str((date.today() - date(int(date.today().strftime('%Y')), 1, 1)).days -1)
        time = str(self.DATE) # NASA changed the date format
        extent = '-2251630.1978347152,-1767716.822874052,2386588.9709421024,1917931.4225647242'
        layers = 'MODIS_Terra_CorrectedReflectance_TrueColor'

        query = 'https://gibs.earthdata.nasa.gov/image-download?TIME=%s&' %time + \
        'extent=%s&epsg=3413&layers=%s&opacities=1&worldfile=true&' %(extent, layers) + \
        'format=image/jpeg&width=4530&height=3599'
        print("Query: " + query)

        urllib.urlretrieve(query, self.TMPDIR + "terra.zip")

        # UNZIPPING DOWNLOADED FILE
        print("Unzipping product...")
        try:
            zip_ref = zipfile.ZipFile(self.TMPDIR + 'terra' + '.zip')
            zip_ref.extractall(self.TMPDIR)
            zip_ref.close()
        except zipfile.BadZipfile:
            return False

        # FINDING FILE NAME
        tmpfile = glob.glob('tmp/**.jpg')[0]

        # PROCESSING FILE
        self.tileImage(tmpfile, outfile)
        self.buildImageOverviews(outfile)
        print('Terra MODIS mosaic is ready \n')
        return outfile

    # --------------------------------- S1 CLOSE-UP ------------------------------- #
    def getS1(self):
        outfile = self.OUTDIR + 's1c.tif'
        s1Name = self.getSentinelFiles(self.BBOX)[0]
        if not s1Name:
            return False

        # PROCESSING FILE
        print("Processing files...")
        tmpfile = self.TMPDIR + 's1tmp.tif'
        print("Warping to NSIDC Sea Ice Polar Stereographic North projection")
        cmd = self.GDALHOME + 'gdalwarp -of GTiff -t_srs ' + self.PROJ + ' -tr 40 40 -order 3' + \
            ' -dstnodata 0 ' + s1Name + ' ' + tmpfile
        print("CMD: " + cmd)
        subprocess.call(cmd, shell=True)

        self.tileImage(tmpfile, outfile)
        self.buildImageOverviews(outfile)
        print('Sentinel-1 image is ready \n')
        return outfile

    # --------------------------------- S1 MOSAIC -------------------------------- #
    def getS1Mos(self, max_num=4): # bbox should be .geojson format
        outfile = self.OUTDIR + "s1mos.tif" # name of the finished result

        tmpfiles = "" # arguments when making virtual mosaic
        downloadNames = self.getSentinelFiles(self.BBOX, max_files=max_num)
        if not downloadNames:
            return False
        print(downloadNames)

        for i in range(len(downloadNames)):
            tmpfile = self.TMPDIR + 's1mostmp' + str(i) + '.tif'

            # PROCESSING EACH FILE
            print("Warping to NSIDC Sea Ice Polar Stereographic North projection")
            cmd = self.GDALHOME + 'gdalwarp -of GTiff -t_srs ' + self.PROJ + ' -tr 40 40 -order 3' + \
            ' -dstnodata 0 ' + downloadNames[i] + ' ' + tmpfile
            tmpfiles += tmpfile + ' '
            print("CMD: " + cmd)
            subprocess.call(cmd, shell=True)

        print('Making a virtual mosaic file')
        cmd = self.GDALHOME + 'gdalbuildvrt ' + self.TMPDIR + 'tmp.vrt ' + tmpfiles
        print("CMD: " + cmd)
        subprocess.call(cmd, shell=True)

        print('Generating real, tiled mosaic from the virtual file')

        self.tileImage(self.TMPDIR + 'tmp.vrt', outfile)
        self.buildImageOverviews(outfile)
        print('Sentinel-1 mosaic is ready \n')
        return outfile


    # --------------------------------- SeaIce ----------------------------------- #
    def getSeaIce(self):
        outfile = self.OUTDIR + 'seaice.tif'

        # DOWNLOADING NEWEST FILE WITH HTTP
        month = self.DATE.strftime("%b").lower()
        yestdate = (self.DATE - timedelta(1)).strftime('%Y%m%d')
        year = yestdate[:4]

        query = 'https://seaice.uni-bremen.de/data/amsr2/asi_daygrid_swath/n6250' + \
        '/%s/%s/Arctic/asi-AMSR2-n6250-%s-v5.tif' %(year, month, yestdate)
        print("Query: " + query)

        rawfile = self.TMPDIR + 'seaiceraw.tif'
        urllib.urlretrieve (query, rawfile)

        tmpfile = self.TMPDIR + 'seaicetmp.tif'
        tmpfile2 = self.TMPDIR + 'seaicetmp2.tif'

        # PROCESSING FILE
        print("Processing files...")
        print("Warping to NSIDC Sea Ice Polar Stereographic North projection")
        cmd = self.GDALHOME + 'gdalwarp -of GTiff -t_srs ' + self.PROJ + \
            ' -dstnodata 0 -dstalpha ' + rawfile + ' ' + tmpfile
        print("CMD: " + cmd)
        code = subprocess.call(cmd, shell=True)
        if code != 0:
            return False

        print('Converting from palette to rgba')
        cmd = '%spct2rgb.py -of GTiff -rgba %s %s' %(self.GDALHOME, tmpfile, tmpfile2)
        print("CMD: " + cmd)
        subprocess.call(cmd, shell=True)

        self.tileImage(tmpfile2, outfile)
        self.buildImageOverviews(outfile, num=4)
        print('Sea ice concentration image is ready \n')
        return outfile


    # --------------------------------- IceDrift --------------------------------- #
    def getIceDrift(self):
        outfile = self.OUTDIR + 'icedrift.tif'

        # DOWNLOADING NEWEST FILE WITH FTP
        enddate = (self.DATE - timedelta(1)).strftime('%Y%m%d')
        startdate = (self.DATE - timedelta(3)).strftime('%Y%m%d')

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
        fig.savefig(self.TMPDIR + 'quivertmp.png', transparent=False, format='png')
        Image.open(self.TMPDIR + 'quivertmp.png').convert('L').save(self.TMPDIR + 'quivertmp.jpg','JPEG')

        # GETTING GEOREFERENCING INFO
        sizeX, sizeY, = Image.open(self.TMPDIR + 'quivertmp.jpg').size

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

        f = open(self.TMPDIR + "quivertmp.jgw", "w")
        f.write(jwg_string)
        f.close()

        # PROCESSING FILE
        print("Processing files...")

        tmpfile = self.TMPDIR + 'quivertmp.tif'
        tmpfile2 = self.TMPDIR + 'quivertmp2.tif'
        tmpfile3 = self.TMPDIR + 'quivertmp3.tif'

        print('Converting from worldfile to geotiff')
        cmd = '%sgdal_translate -of GTiff %s %s' %(self.GDALHOME, self.TMPDIR + 'quivertmp.jpg', tmpfile)
        print("CMD: " + cmd)
        subprocess.call(cmd, shell=True)

        print('Removing noise around arrows')
        cmd = '%sgdal_calc.py -A %s --outfile=%s --calc="255*(A>220)"' %(self.GDALHOME, tmpfile, tmpfile2)
        print("CMD: " + cmd)
        subprocess.call(cmd, shell=True)

        print("Warping to NSIDC Sea Ice Polar Stereographic North projection")
        cmd = self.GDALHOME + 'gdalwarp -t_srs ' + self.PROJ + \
            ' -srcnodata 255 -dstalpha ' + tmpfile2 + ' ' + tmpfile3
        print("CMD: " + cmd)
        subprocess.call(cmd, shell=True)

        self.tileImage(tmpfile3, outfile)
        self.buildImageOverviews(outfile, num=4)
        print('Ice drift image is ready \n')
        return outfile

    def makeGeojson(self, grid, outfile):
        east = grid.split(',')[0]
        north = grid.split(',')[1]

        topRight = str( float(east) - 0.001 ) + ',' + north
        bottomRight = str( float(east) - 0.001 ) + ',' + str( float(north) - 0.001 )
        bottomLeft = east + ',' + str( float(north) - 0.001 )
        json_string = '{"type":"FeatureCollection","features":[\n\
    {"type":"Feature","properties":{},"geometry":{\n\
        "type":"Polygon","coordinates":[[\n\
            [' + grid + '],\n\
            [' + topRight + '],\n\
            [' + bottomRight + '],\n\
            [' + bottomLeft + '],\n\
            [' + grid + ']\n\
        ]]\n\
    }}\n\
]}'
        f = open(outfile, "w")
        f.write(json_string)
        f.close()
        return outfile


    # ------------------------------ GETTING DATA -------------------------------- #
    def main(self, argv):
        try:
            opts, args = getopt.getopt(argv,"hd:g:",["date=","grid="])
        except getopt.GetoptError:
            print('Invalid arguments. Add "-h" for help.')
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print('Usage: getdata.py [OPTIONS...]\n\nHelp options:\n-h         \
      Show help\n-d, --date       Set date for all imagery capture (format: yyyy-mm-dd / yyyymmdd)\n\
-g, --grid       Set center grid for sentinel imagery capture (format: north-decimal,east-decimal)\n'
                )
                sys.exit()
            elif opt in ("-d", "--date"):
                if '-' in arg:
                    self.DATE = datetime.strptime(arg, '%Y-%m-%d').date()
                else:
                    self.DATE = datetime.strptime(arg, '%Y%m%d').date()
            elif opt in ("-g", "--grid"):
                self.GRID = arg
        self.makeDirs()
        if self.GRID:
            self.BBOX = self.makeGeojson(self.GRID, self.TMPDIR + str(self.DATE) + '.geojson')
        if not opts:
            print('WARNING: No arguments provided. Using defaults.')
        quit()
        outfiles = [
            self.getS2(),
            self.getTerra(),
            self.getS1(),
            self.getS1Mos(),
            self.getSeaIce(),
            self.getIceDrift()
        ]
        # outfiles = ['2018-08-08/s2c.tif', '2018-08-08/terramos',
        # '2018-08-08/s1c.tif', '2018-08-08/s1mos.tif', '2018-08-08/seaice.tif', '2018-08-08/icedrift.tif']
        print('Created files: ' + str(outfiles) + '\n')

        # ---------------------------- UPLOAD TO GEOSERVER ---------------------------- #
        cat = Catalog("http://localhost:8080/geoserver/rest/", "admin", "geoserver")

        ws = cat.get_workspace( str(self.DATE) )
        if ws is None:
            cat.create_workspace(str(self.DATE), str(self.DATE) + 'uri')

        for layerdata in outfiles:
            layername = layerdata.split('/')[1].split('.')[0]
            print('Adding ' + layername + ' to geoserver...')
            cat.create_coveragestore(name = layername,
                                     data = layerdata,
                                     workspace = ws,
                                     overwrite = True)

        print('Sensor data for ' + str(self.DATE) + ' has been successfully uploaded!')
        print('Process finished')


if __name__ == "__main__":
    cmd = Command()
    cmd.main(sys.argv[1:])
