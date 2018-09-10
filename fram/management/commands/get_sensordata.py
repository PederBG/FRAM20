"""
Calling an external python script that collects sensor data layers and upload
them to geoserver.

Note that this django app is using python3.6, while the external script is using
python2.7.
"""

import os, sys, subprocess, glob
from django.core.management.base import BaseCommand
from fram.models import Position

class Command(BaseCommand):
    args = '<foo bar ..>'
    help = "No options needed"

    def handle(self, *args, **options):
        latest = Position.objects.all().last()

        # Set paths
        scriptsPath = '/home/pederbg/sommer18/app/v2fram/scripts/'
        scriptName = 'getdata.py'
        targetPath = '/home/pederbg/sommer18/app/v2fram/data'

        # Get data
        cmd = '%s%s -d %s -g %s %s --overwrite' %(scriptsPath, scriptName,
            '20180728', '-18,82.4', targetPath)
        print(cmd)
        subprocess.call(cmd, shell=True)

        # Creating layer info
        # TODO
