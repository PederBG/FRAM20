#! /usr/bin/env python

"""
Written by PederBG, 2018-08

Main method used by FRAM19 for image overlay generating.

It uses a DownloadManager instance to download and process raw data and then
uploads ready-to-use, georeferenced overlays to a locally running geoserver.

The geoserver will then handle feeding layer-tiles to the front-end on request.
"""

from datetime import datetime
import sys, getopt
from geoserver.catalog import Catalog

from downloadmanager import DownloadManager
import fram_functions as funcs


def main(argv):
    #  --------------------- Handler --------------------- #
    try:
        opts, args = getopt.getopt(argv,"hd:g:t:o:",["help", "test", "date=","grid=","target=","only=","overwrite"])
    except getopt.GetoptError:
        print('Invalid arguments. Add "-h" or "--help" for help.')
        sys.exit(1)

    date, grid, only, target, overwrite = None, None, None, None, False
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('Usage: ./main.py [OPTIONS...]\n\nHelp options:\n\
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
    #  ------------------- Handler end ------------------- #

    d = DownloadManager(date=date, grid=grid, target=target) # Making download instance

    functions = {
        's2c' : d.getS2,
        'terramos' : d.getTerra,
        's1c' : d.getS1,
        's1mos' : d.getS1Mos,
        'seaice' : d.getSeaIce,
        'icedrift' : d.getIceDrift
    }

    #  ------------------ Getting/processing data ------------------ #
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
    #  ---------------- Getting/processing data end ---------------- #


    # --------------------- Upload to Geoserver -------------------- #
    cat = Catalog("http://localhost:8080/geoserver/rest/", "admin", "geoserver")

    # BUG: ws is sometime cite instead of d.date
    ws = cat.get_workspace( str(d.DATE) )
    if ws is None:
        ws = cat.create_workspace(str(d.DATE), str(d.DATE) + 'uri')

    for layerdata in outfiles:
        if layerdata:
            layername = layerdata.split('/')[-1].split('.')[0]
            print('Adding ' + layername + ' to geoserver...')
            cat.create_coveragestore(name = layername,
                                     data = layerdata,
                                     workspace = ws,
                                     overwrite = overwrite)

    print('Sensor data for ' + str(d.DATE) + ' has been successfully uploaded!')
    # ------------------- Upload to Geoserver end ------------------ #
    print('Process finished')


if __name__ == "__main__":
    main(sys.argv[1:])
