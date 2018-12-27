"""
Calling an external python script that collects sensor data layers and upload
them to geoserver.

Note that this django app is using python3.6, while the external script is using
python2.7.
"""

import os, sys, subprocess, glob
from django.core.management.base import BaseCommand
from fram.models import Position, Layer

class Command(BaseCommand):
    args = '<foo bar ..>'
    help = "No options needed"

    def handle(self, *args, **options):
        latest = Position.objects.all().order_by('-date')
        # If no positions added
        if latest:
            latest = latest[0]
        else:
            latest = Position()
            latest.grid = '-17,82'
            latest.date = '2018-06-22' # Default day (a day with clear weather)
            latest.save()

        # Set paths
        scriptsPath = 'scripts/'
        scriptName = 'main.py'
        targetPath = 'data'
        date = latest.date
        grid = latest.grid

        # Get data
        cmd = '%s%s -d %s -g %s -t %s --overwrite' %(scriptsPath, scriptName,
            date, grid, targetPath)
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

        l = Layer()
        l.position = latest
        try:
            l.opticclose = "<p><h5>Sentinel-2 Optical Image</h5><b>Sensing time:</b> %s<br><b>Cloud coverage assessment:</b> %s<br><b>Source:</b> ESA, Copernicus Programme<br><b>Available at:</b> https://colhub.met.no/#/home<br><b>Pixel size:</b> 10.0 x 10.0 meters<br><b>Raw size:</b> %s</p>" %(layerinfo['s2c_time'], layerinfo['s2c_clouds'], layerinfo['s2c_size'])
        except KeyError:
            l.opticclose = "<p>No data</p>"
        try:
            l.opticmos = "<p><h5>Terra MODIS Optical Mosaic</h5><b>Sensing time:</b> %s<br><b>Source:</b> NASA, Earth Observing System Data and Information System (EOSDIS)<br><b>Available at:</b> https://worldview.earthdata.nasa.gov<br><b>Pixel size:</b> 250.0 x 250.0 meters<br><b>Raw size:</b> %s</p>" %(date, layerinfo['terramos_size'])
        except KeyError:
            l.opticmos = "<p>No data</p>"
        try:
            l.sarclose = "<p><h5>Sentinel-1 Synthetic-Aperture Radar (SAR) Image</h5><b>Sensing time:</b> %s<br><b>Source:</b> ESA, Copernicus Programme<br><b>Available at:</b> https://colhub.met.no/#/home<br><b>Pixel size:</b> 40.0 x 40.0 meters<br><b>Raw size:</b> %s</p>" %(date, layerinfo['s1c_size'])
        except KeyError:
            l.sarclose = "<p>No data</p>"
        try:
            l.sarmos = "<p><h5>Sentinel-1 Synthetic-Aperture Radar (SAR) Mosaic</h5><b>Sensing time:</b> %s<br><b>Source:</b> ESA, Copernicus Programme<br><b>Available at:</b> https://colhub.met.no/#/home<br><b>Pixel size:</b> 200.0 x 200.0 meters<br><b>Raw size:</b> %s</p>" %(date, layerinfo['s1mos_size'])
        except KeyError:
            l.sarmos = "<p>No data</p>"
        try:
            l.seaice = "<p><h5>AMSR-2 Global Sea Ice Concentration</h5><b>Sensing time:</b> %s<br><b>Source:</b> EUMETSAT, Ocean and Sea Ice SAF<br><b>Available at:</b> http://osisaf.met.no/<br><b>Pixel size:</b> 6.250 x 6.250 kilometers<br><b>Raw size:</b> %s</p>" %(date, layerinfo['seaice_size'])
        except KeyError:
            l.seaice = "<p>No data</p>"
        try:
            l.icedrift = "<p><h5>Low Resolution Sea Ice Drift</h5><b>Sensing time:</b> %s<br><b>Source:</b> EUMETSAT, Ocean and Sea Ice SAF<br><b>Available at:</b> http://osisaf.met.no/<br><b>Pixel size:</b> 6.250 x 6.250 kilometers<br><b>Raw size:</b> %s</p>" %(date, layerinfo['icedrift_size'])
        except KeyError:
            l.icedrift = "<p>No data</p>"
        l.save()
