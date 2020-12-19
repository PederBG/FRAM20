"""
Written by PederBG, 2018-08

Calling an external python script that collects sensor data layers and upload
them to geoserver.

Note that due to a dependency issue this django app is using python3.6, while the external script is using
python2.7.
"""

import os, sys, subprocess, glob
from django.core.management.base import BaseCommand
from fram.models import Position, Layer
from datetime import datetime, timedelta

class Command(BaseCommand):
    args = '<foo bar ..>'
    help = "Initiate image generating scripts from django framework"

    def add_arguments(self, parser):
        parser.add_argument("-d", "--date", type=str)

    @staticmethod
    def toDatetime(input): # format yyyy-mm-dd
        return datetime.strptime('{} 23:59:00'.format(input), '%Y-%m-%d %H:%M:%S')

    def handle(self, *args, **options):
        DATETIME = Command.toDatetime(options['date']) if options['date'] else datetime.now()

        try:
            latest = Position.objects.get(date=DATETIME.date().strftime('%Y-%m-%d'))
            print("Found an existing position")
        except Position.DoesNotExist:
            latest = Position.objects.all().order_by('-date')

            if latest:
                print("No new position added today, using last added grid")
                p = Position()
                p.grid = latest[0].grid
                p.date = DATETIME.date()
                p.save()
                latest = p
            else:
                print("No positions found")
                sys.exit(1)

        # Set paths
        scriptsPath = 'scripts/'
        scriptName = 'main.py'
        targetPath = '/root/fram19/data'
        only = ''
        date = latest.date
        grid = latest.grid

        if DATETIME < DATETIME.replace(hour=13):
            print("Early running: only generating s1 image")
            only = '-o s1c'

        # Get data
        cmd = '%s%s -d %s -g %s -t %s %s --overwrite' %(scriptsPath, scriptName,
            date, grid, targetPath, only)
        print(cmd)
        subprocess.call(cmd, shell=True)

        # Get dynamic layerinfo from layerinfo.txt
        layerinfo = {}
        with open(scriptsPath + 'tmp/layerinfo.txt') as f:
            for line in f:
                line = line.split('\n')[0]
                layerinfo[line.split('|')[0]] = line.split('|')[1]

        # Hard-coded parsing since os.getfilesize / os.stat is storage block-size dependent i.e. gives wrong values
        fileSizes = str(subprocess.check_output(["ls -sh %s/%s/  | awk '{print $2,$1}'" %(targetPath, str(date))], shell=True))

        for file in fileSizes.split('\\n')[1:-1]:
            layerinfo[file.split(' ')[0][:-4] + '_size'] = file.split(' ')[1] + 'B'

        print(layerinfo)

        # Remove old layer from same day
        if Layer.objects.all().order_by('-position__date').first().position.date == DATETIME.date():
            Layer.objects.all().order_by('-position__date').first().delete()


        l = Layer()
        l.position = latest
        try:
            l.opticclose = "<p><h5>Sentinel-2 Optical Image</h5><b>Sensing time:</b> %s<br><b>Cloud coverage assessment:</b> %s<br><b>Source:</b> ESA, Copernicus Programme<br><b>Available at:</b> https://colhub.met.no/#/home<br><b>Pixel size:</b> 10.0 x 10.0 meters<br><b>Raw size:</b> %s</p>" %(layerinfo['s2c_time'], layerinfo['s2c_clouds'], layerinfo['s2c_size'])
        except KeyError:
            l.opticclose = "<p><h5>Sentinel-2 Optical Image</h5><b>Sensing time:</b> No data<br><b>Cloud coverage assessment:</b> No data<br><b>Source:</b> ESA, Copernicus Programme<br><b>Available at:</b> https://colhub.met.no/#/home<br><b>Pixel size:</b> 10.0 x 10.0 meters<br><b>Raw size:</b> No data</p>"

        try:
            l.opticmos = "<p><h5>Terra MODIS Optical Mosaic</h5><b>Sensing time:</b> %s<br><b>Source:</b> NASA, Earth Observing System Data and Information System (EOSDIS)<br><b>Available at:</b> https://worldview.earthdata.nasa.gov<br><b>Pixel size:</b> 250.0 x 250.0 meters<br><b>Raw size:</b> %s</p>" %(date, layerinfo['terramos_size'])
        except KeyError:
            l.opticmos = "<p><h5>Terra MODIS Optical Mosaic</h5><b>Sensing time:</b> No data<br><b>Source:</b> NASA, Earth Observing System Data and Information System (EOSDIS)<br><b>Available at:</b> https://worldview.earthdata.nasa.gov<br><b>Pixel size:</b> 250.0 x 250.0 meters<br><b>Raw size:</b> No data</p>"

        try:
            l.sarclose = "<p><h5>Sentinel-1 Synthetic-Aperture Radar (SAR) Image</h5><b>Sensing time:</b> %s<br><b>Source:</b> ESA, Copernicus Programme<br><b>Available at:</b> https://colhub.met.no/#/home<br><b>Pixel size:</b> 40.0 x 40.0 meters<br><b>Raw size:</b> %s</p>" %(date, layerinfo['s1c_size'])
        except KeyError:
            l.sarclose = "<p><h5>Sentinel-1 Synthetic-Aperture Radar (SAR) Image</h5><b>Sensing time:</b> No data<br><b>Source:</b> ESA, Copernicus Programme<br><b>Available at:</b> https://colhub.met.no/#/home<br><b>Pixel size:</b> 40.0 x 40.0 meters<br><b>Raw size:</b> No data</p>"

        try:
            l.sarmos = "<p><h5>Sentinel-1 Synthetic-Aperture Radar (SAR) Mosaic</h5><b>Sensing time:</b> %s - %s<br><b>Source:</b> ESA, Copernicus Programme<br><b>Available at:</b> https://colhub.met.no/#/home<br><b>Pixel size:</b> 200.0 x 200.0 meters<br><b>Raw size:</b> %s</p>" %(date - timedelta(days=1), date, layerinfo['s1mos_size'])
        except KeyError:
            l.sarmos = "<p><h5>Sentinel-1 Synthetic-Aperture Radar (SAR) Mosaic</h5><b>Sensing time:</b> No data<br><b>Source:</b> ESA, Copernicus Programme<br><b>Available at:</b> https://colhub.met.no/#/home<br><b>Pixel size:</b> 200.0 x 200.0 meters<br><b>Raw size:</b> No data</p>"

        try:
            l.seaice = "<p><h5>AMSR-2 Global Sea Ice Concentration</h5><p>This layer show sea ice concentration in percentage from <span style='color: #6b023f'><b>100% " + "</b></span>to <span style='color: #013384'><b>1% " + "</b></span></p><b>Sensing time:</b> %s<br><b>Source:</b> University of Bremen, Sea Ice Remote Sensing<br><b>Available at:</b> https://seaice.uni-bremen.de<br><b>Pixel size:</b> 6.250 x 6.250 kilometers<br><b>Raw size:</b> %s</p>" %(date, layerinfo['seaice_size'])
        except KeyError:
            l.seaice = "<p><h5>AMSR-2 Global Sea Ice Concentration</h5><p>This layer show sea ice concentration in percentage from <span style='color: #6b023f'><b>100% " + "</b></span> to <span style='color: #013384'><b>1% " + "</b></span></p><b>Sensing time:</b> No data<br><b>Source:</b> University of Bremen, Sea Ice Remote Sensing<br><b>Available at:</b> https://seaice.uni-bremen.de<br><b>Pixel size:</b> 6.250 x 6.250 kilometers<br><b>Raw size:</b> No data</p>"

        try:
            l.icedrift = "<p><h5>Low Resolution Sea Ice Drift</h5><b>Sensing time:</b> %s<br><b>Source:</b> EUMETSAT, Ocean and Sea Ice SAF<br><b>Available at:</b> http://osisaf.met.no/<br><b>Pixel size (original product):</b> 62.5 x 62.5 kilometers<br><b>Raw size:</b> %s</p>" %(date, layerinfo['icedrift_size'])
        except KeyError:
            l.icedrift = "<p><h5>Low Resolution Sea Ice Drift</h5><b>Sensing time:</b> No data<br><b>Source:</b> EUMETSAT, Ocean and Sea Ice SAF<br><b>Available at:</b> http://osisaf.met.no/<br><b>Pixel size (original product):</b> 62.5 x 62.5 kilometers<br><b>Raw size:</b> No data</p>"
        l.save()

        print("Deleting tmp folder...")
        subprocess.call('rm -r ' + scriptsPath + 'tmp', shell=True)
        print("Process finished")
