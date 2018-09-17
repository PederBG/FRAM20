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
