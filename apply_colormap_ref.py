#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Apply a color table using the GDAL method of converting the input raster
to a VRT, inserting the color table into the VRT, and finally writing it
back to a new .tif raster.  For Trends/NLCD clipped data.
Author: Dan Zelenak
Last Updated: 5/5/2017 by Dan Zelenak
"""

#%%
import os
import sys
import datetime
import glob
import subprocess
import argparse

from osgeo import gdal

print (sys.version)

t1 = datetime.datetime.now()
print ("\n", t1.strftime("%Y-%m-%d %H:%M:%S"))

# gdal.UseExceptions()
# gdal.AllRegister()


def add_color_table(in_file, clr_table, dtype):

    """Open the .txt file which contains the color table information and
    insert it into the xml code of the .vrt file

    Args:
        in_file = the vrt file produced from the original raster file
        clr_table = the color table .txt file
        dtype = the data type of the original raster file (e.g. Byte)
    Returns:
        out_vrt = the edited vrt file containing color table information
    """

    color_table = open(clr_table, "r")

    # split the path and file name
    (dirname, filename) = os.path.split(in_file)
    (filebase, fileext) = os.path.splitext(filename)

    out_vrt = r"%s%szzzzz%s_temp.vrt" % (dirname, os.sep, filebase)

    # open the input vrt file as read-only
    txt = open(in_file, "r+")

    # get lines in a list
    txt_read = txt.readlines()

    # check text for keywords
    key = '<VRTRasterBand dataType="%s" band="1">' % (dtype)

    # create and open the output vrt file for writing
    out_txt = open(out_vrt, "w")

    for line in txt_read:

        write = r"%s" % line
                 
        out_txt.write(write)

        # insert color table following keywords
        if key in line:

            color_read = color_table.readlines()

            for ln in color_read:

                out_txt.write(ln)

    out_txt.close()

    return out_vrt


def allCalc(infile, outputdir, outfile, clrtable, dtype):

    """Primary function that runs gdal executables.  Takes in a single input
    raster file, a specified output directory including the full path, output 
    file name with full path, as well as the appropriate color table and data 
    type of the output raster.
    
    Args:
        infile = the full path to the current input raster
        outputdir = the full path to the output folder
        outfile = the full path and name of the output raster
        clrtable = the color table to be used
        dtype = the data type of the output raster (e.g. Byte)
    Returns:
        None
    """

    outcsv_file = r"%s%szzzz_%s_list.csv" \
                    % (outputdir, os.sep, os.path.basename(infile))

    if os.path.isfile(outcsv_file):

        os.remove(outcsv_file)

    open_csv = open(outcsv_file, "wb")

    #-----------------------------------------------------------------------
    #Generate a temporary output raster file--------------------------------
    tempoutfile = outputdir + os.sep + "zzzz_" + \
                   os.path.basename(infile) + ".tif"
    
    runsubset   = "gdal_translate -of %s -b %s -q %s %s"\
                   % ("GTiff", "1", infile, tempoutfile)
    
    subprocess.call(runsubset, shell=True)

    #write temporary raster file path to this .csv file (required for VRT)
    
    if sys.version[0] == '3':
    
        open_csv.write(tempoutfile.encode("utf-8") + ("\r\n").encode("utf-8"))
        
    else:
        
        open_csv.write(tempoutfile + "\r\n")

    open_csv.close()

    #-----------------------------------------------------------------------
    #Genereate temporary VRT file based on temp raster listed in .csv file
    temp_VRT =  outputdir + os.sep +  "zzzz_" + \
                os.path.basename(infile) + ".vrt"
    
    com      = "gdalbuildvrt -q -input_file_list %s %s"\
                % (outcsv_file, temp_VRT)
    
    subprocess.call(com, shell=True)

    #subprocess.call(com, shell=True)

    color_VRT = add_color_table(temp_VRT, clrtable, dtype)

    #-----------------------------------------------------------------------
    #Write the VRT w/ color table added to the output raster file
    runCom  = "gdal_translate -of {of} -q {vrt} {out}".format(of="GTiff", vrt=color_VRT, out=outfile)
    
    subprocess.call(runCom, shell=True)

    get_srs(infile, outfile)
    
    #Remove temporary files (1 each of a .csv, .vrt, and .tif)
    for v in glob.glob(outputdir + os.sep + "zzz*"):

        os.remove(v)

    return None


def get_srs(inraster, outraster):
    
    """Apply a spatial reference system to the new raster file based on the
    SRS of the original raster
    
    Args:
        inraster = the original input raster file
        outraster = the newly created raster file that contains a color map
    Returns:
        None
    """
    
    in_src = gdal.Open(inraster, gdal.GA_ReadOnly)
    out_src = gdal.Open(outraster, gdal.GA_Update)
    
    out_src.SetGeoTransform( in_src.GetGeoTransform() )
    out_src.SetProjection( in_src.GetProjection() )
    
    in_src = None
    out_src = None
    
    return None
    

def housekeeping(infolder, colorfolder):
    
    """Remove original recoded rasters, replacing them with the colorized outputs
    """
    
    old_files = glob.glob(infolder + os.sep + "*.tif")
    
    for old in old_files:
        
        os.remove(old)
        
    new_files = glob.glob(colorfolder + os.sep + "*.tif")
    
    for new in new_files:
        
        mv_name = os.path.basename(new)
        
        os.rename(new, infolder + os.sep + mv_name)
        
    os.removedirs(colorfolder)
    
    return None


def main():

    parser = argparse.ArgumentParser()
    
    parser.add_argument("-i", "--input", required=True,
                        help="Full path to the root input director")
    
    parser.add_argument("-n", "--name", required=True,
                        help="Name of the input Land Cover source", choices=["nlcd", "trends"])
    
    args = parser.parse_args()
    
    name = args.name
    
    indir = args.input
    
    if name == "trends":
        
        name = "Trends"
    
    names = ["nlcd", "Trends"]

    colortables = ["color_covermap_nlcd.txt", "color_covermap.txt"]

    dtypes = ["Byte", "Byte"]

    lookupcolor = dict(zip(names, colortables))

    lookuptype = dict(zip(names, dtypes))

    clrtable = lookupcolor[name]

    dtype = lookuptype[name]
    
    for root, folders, files in os.walk(indir):
    
        for folder in folders:
        
            infolder = os.path.join(root, folder)
            
            outputdir = "{}{}{}_color".format(infolder, os.sep, name)

            filelist = sorted(glob.glob("{}{}{}*.tif".format(infolder, os.sep, name) ) )
    
            print (filelist)
    
            if not os.path.exists(outputdir):
        
                os.makedirs(outputdir)

            print ("\nFiles are saving in", outputdir, "\n")

            for r in filelist:
        
                outfile = outputdir + os.sep + os.path.basename(r)
        
                if not os.path.exists(outfile):
        
                    print ("Processing file ", r, "\n")
                    
                    # Call the primary function
                    allCalc(r, outputdir, outfile, clrtable, dtype)
                    
            housekeeping(infolder, outputdir)

    return None

#%%
if __name__ == "__main__":

    main()

#%%
t2 = datetime.datetime.now()
print (t2.strftime("%Y-%m-%d %H:%M:%S"))
tt = t2 - t1
print ("\nProcessing time: " + str(tt))
