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
        latest = Position.objects.all().last()
        # If no positions added
        if not latest:
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

        l = Layer()
        l.position = latest
        l.save()
        # Creating layer info
        # TODO
