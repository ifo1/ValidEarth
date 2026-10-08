#!/usr/bin/python3

import numpy as np
import os.path
import argparse
import matplotlib.pyplot as plt

plotcolours = ["red", "blue", "green", "orange", "violet", "brown"]

# local modules
from read_values import read_field, read_float, read_value
from colouredstrings import error, warning, highlight
from check_data import recompute_vp_vs, recompute_mgnum, check_layers, check_layer_depth

# local classes
from classes import columndata, pressuredepth, match_layers, print_stacked_models, referencecolumn, \
    validate_profile_stdev, validate_profile_minmax, haversine, referencemodel, validate_profile_melting

# read command line arguments

parser = argparse.ArgumentParser()
parser.add_argument("-i", dest="inputfile", default="", help="An input file with structure to verify")
parser.add_argument("-delim", dest="delimiter", default=None, help="Delimiter between all columns")
parser.add_argument("-utemp", dest="utemp", default="K", help="Temperature units: K [default] or C")
parser.add_argument("-uvp", dest="uvp", default="m/s", help="Vp units: m/s [default] or km/s")
parser.add_argument("-uvs", dest="uvs", default="m/s", help="Vs units: m/s [default] or km/s")
parser.add_argument("-udepth", dest="udepth", default="m", help="Depth units: m [default] or km")
parser.add_argument("-udens", dest="udens", default="kg/m3", help="Density units: kg/m3 [default] or g/cm3")
parser.add_argument("-pressuremodel", dest="file_pressure", default="models/PREM.dat", help="A file with columns Pressure and Depth that will be used to calculate depths from pressures for those reference models calibrated for pressure")
parser.add_argument("-refmodels", dest="file_refmodels", default="config.txt", help="A list of reference models to compare the data with (use -refmodels noref to run without references")
parser.add_argument("-detailed", dest="d",action="store_true",help="Print out a detailed layer-by-layer comparison")
parser.add_argument("-pdf", dest="pdf",action="store_true",help="Create pdf plots")
parser.add_argument("-png", dest="png",action="store_true",help="Create png plots")
parser.add_argument("-dist", dest="dist", default=0.0,type=float,help="The maximum distance (m) from the reference model to the input column")
parser.add_argument("-depthneg", dest="depthneg",action="store_true",help="The depths below sea level are negative")
parser.add_argument("-depthrev", dest="depthrev",action="store_true",help="The depth is decreasing towards the end of the file (e.g. mantle first, crust second)")
parser.add_argument("-allowqtz", dest="allowquartz",action="store_true",help="Allow low Vp/Vs ratios down to 1.4 associated with quartzites (check Christensen 1996 paper)")
parser.add_argument("-allowthicksed", dest="maxsedthick", default=0.0,type=float,help="The maximum thickness (m) of sediments (Vp/Vs > 2)")
parser.add_argument("-allowsalt", dest="allowsalt", action="store_true",help="Allow low-density rock salt layers within the profile (with density >= 2000 kg/m3 and depth up to the maximum depth of sediments)")
parser.add_argument("-allowuhp", dest="allowuhp", action="store_true",help="Allow low-density rocks (with density contrast less than 200 kg/m3); the option is designed for exhumating ultra-high pressure complexes and works below the maximum possible depth of sediments")
args = parser.parse_args()

args.allowuhp, args.allowsalt

# verify the input file exists
if not os.path.isfile(args.inputfile):
    print (error() + "input file "+args.inputfile+" does not exist!")
    exit()

if args.file_refmodels != "noref":

    # read the list of reference models
    if not os.path.isfile(args.file_refmodels):
        print (error() + "catalog file "+args.file_refmodels+" does not exist!")
        exit()

    print ("Reading a list of reference models from " + highlight (args.file_refmodels))
    referencemodels = []

    with open(args.file_refmodels) as myfile:

        for line in myfile:

            # skip empty lines and comments
            if len(line.strip()) == 0: continue
            char = line.strip()[0]
            if char == "#" or char == "!" or char == "%": continue

            # check whether the reference model exists
            if not os.path.isfile(line.strip()):
                print (error() + "the reference model file " + line.strip() + " does not exist!")
                exit()

            # create new class instance and load data
            refmodel = referencemodel(line.strip())
            with open(refmodel.filename) as mymodel:
                print (" - " + refmodel.filename)
                iline = 0
                for line in mymodel:
                    iline += 1

                    # skip empty lines and comments
                    if len(line.strip()) == 0: continue
                    char = line.strip()[0]
                    if char == "#" or char == "!" or char == "/" or char == "%": continue

                    tmp = line.strip().split()
                    
                    if tmp[0] == "Name":
                        refmodel.name = line.partition(' ')[2].strip()

                    elif tmp[0] == "Citation":
                        refmodel.citation.append(line.partition(' ')[2].strip())

                    elif tmp[0] == "Depth" or tmp[0] == "Pressure":
                        # the number of line (starting from zero) where the datatable begins
                        refmodel.lineindex.append(iline-1)

                    elif tmp[0] == "CoordinateSystem":
                        refmodel.coordsys = tmp[1]

                    elif tmp[0] == "Longitude":
                        refmodel.arraylongitude.append(float(tmp[1]))
                    elif tmp[0] == "Latitude":
                        refmodel.arraylatitude.append(float(tmp[1]))

                    elif tmp[0] == "X":
                        refmodel.arrayx.append(float(tmp[1]))
                    elif tmp[0] == "Y":
                        refmodel.arrayy.append(float(tmp[1]))

            # verify that the coordinate lists are aligned
            if len(refmodel.arraylongitude) != len(refmodel.arraylatitude):
                print (error() + " the number of longitude data entries does not match the number of latitude data entries")
                exit()

            if len(refmodel.arrayx) != len(refmodel.arrayy):
                print (error() + " the number of X data entries does not match the number of Y data entries")
                exit()

            if args.dist > 0:
                # append 3D models if -dist is provided
                if len (refmodel.arraylongitude) > 1:
                    referencemodels.append(refmodel)
            else:
                # append 1D models if -dist is NOT provided
                if len (refmodel.arraylongitude) <= 1:
                    referencemodels.append(refmodel)


# initialise a class for the inputs ad for the golden nails
column = columndata()

# read the input file
print ("Reading file " + highlight (args.inputfile))
with open(args.inputfile) as myfile:

    # read each line and parse it
    datatable = False

    for line in myfile:

        # skip empty lines and comments
        if len(line.strip()) == 0: continue
        char = line.strip()[0]
        if char == "#" or char == "!" or char == "/" or char == "%": continue

        # split the line into a list of strings
        if args.delimiter is not None:
            tmp = line.strip().split(args.delimiter)
        else:
            tmp = line.strip().split()

        # check the header
        if not datatable:

            column.name = line.partition(' ')[2].strip()

            column.coordsys, flag = read_field("CoordinateSystem", tmp, column.coordsys)
            if flag: continue

            # read column coordinates, if any
            if column.coordsys == "Geographic":
                column.longitude, flag = read_float("Longitude", tmp, -180.0, 180.0, column.longitude)
                if flag: continue
                column.latitude, flag  = read_float("Latitude", tmp, -90.0, 90.0, column.latitude)
                if flag: continue
            elif column.coordsys == "Cartesian":
                column.x, flag = read_field("X", tmp)
                if flag: continue
                column.y, flag = read_field("Y", tmp)
                if flag: continue
            else:
                print ("The coordinate system was not recognised: " + column.coordsys)
                exit()

            # read headers
            if tmp[0] == "Depth":

                # there can be only one data section
                if datatable:
                    print (error() + "there can be only one data section in file")
                    exit()

                datatable = True

                column.columns = tmp

                if column.columns[-1] != "Type":
                    column.columns.append("Type")

            # skip data table section
            continue

        # if execution reached this point, it is reading the actual data table (vertical profiles)

        # pad the Type column with None
        if len(tmp) == len(column.columns)-1:
            tmp.append(None)

        if len(tmp) != len(column.columns):
            print (error() + "the number of columns in the input data file is not uniform!")
            exit()

        # append to the beginning (0) or to the end (N+1) of the list
        appendindex = 0 if args.depthrev else len(column.depth)+1

        # read the actual data
        for field, value in zip (column.columns, tmp):
            if field == "Depth":
                locdepth = read_value(field,value)
                if args.depthneg: locdepth = -locdepth
                if len(column.depth) > 1:
                    if args.depthrev:
                        if locdepth > column.depth[-1]:
                            print (error() + "the depth is not non-decreasing in the input file: " + str (column.depth[-1]) + " vs "  + str (locdepth)+ "; probably, -depthrev flag might help")
                            exit()
                    else:
                        if locdepth < column.depth[-1]:
                            print (error() + "the depth is not non-increasing in the input file: " + str (column.depth[-1]) + " vs "  + str (locdepth) + "; probably, -depthrev flag might help")
                            exit()
                column.depth.insert( appendindex , locdepth )
            elif field == "Temperature":
                column.temperature.insert( appendindex , read_value(field,value) )
            elif field == "Vp":
                column.Vp.insert( appendindex , read_value(field,value) )
            elif field == "Vs":
                column.Vs.insert( appendindex , read_value(field,value) )
            elif field == "Density":
                column.density.insert( appendindex , read_value(field,value) )
            elif field == "VpVs":
                column.VpVs.insert( appendindex , read_value(field,value) )
            elif field == "SiO2":
                column.SiO2.insert( appendindex , read_value(field,value) )
            elif field == "Al2O3":
                column.Al2O3.insert( appendindex , read_value(field,value) )
            elif field == "MgO":
                column.MgO.insert( appendindex , read_value(field,value) )
            elif field == "FeO":
                column.FeO.insert( appendindex , read_value(field,value) )
            elif field == "CaO":
                column.CaO.insert( appendindex , read_value(field,value) )
            elif field == "MgNum" or field == "Mg#":
                column.MgNum.insert( appendindex , read_value(field,value) )
            elif field == "Type":
                if value is not None: column.gn.assign_gn(value, len(column.depth)-1)

# check the layer boundaries
if args.depthrev: column.gn.reverse_gn(len(column.depth)-1)
column.gn.report_gn(column.depth)

# convert data to numpy arrays
column.depth = np.asarray(column.depth,dtype=float)
column.SiO2  = np.asarray(column.SiO2,dtype=float)
column.Al2O3 = np.asarray(column.Al2O3,dtype=float)
column.MgNum = np.asarray(column.MgNum,dtype=float)
column.MgO   = np.asarray(column.MgO,dtype=float)
column.FeO   = np.asarray(column.FeO,dtype=float)
column.CaO   = np.asarray(column.CaO,dtype=float)
column.temperature = np.asarray(column.temperature,dtype=float)
column.Vp      = np.asarray(column.Vp,dtype=float)
column.Vs      = np.asarray(column.Vs,dtype=float)
column.VpVs    = np.asarray(column.VpVs,dtype=float)
column.density = np.asarray(column.density,dtype=float)

# convert to SI units
if args.udepth == "km":    column.depth   *= 1000
if args.uvp    == "km/s":  column.Vp      *= 1000
if args.uvs    == "km/s":  column.Vs      *= 1000
if args.udens  == "g/cm3": column.density *= 1000
if args.utemp  == "C":     column.temperature += 273.15

# compute or verify derived fields
recompute_vp_vs(column)
recompute_mgnum(column)

# discard absent data arrays
if column.density.size == 0: column.density = None
if column.SiO2.size == 0: column.SiO2 = None
if column.Al2O3.size == 0: column.Al2O3 = None
if column.MgNum is not None and column.MgNum.size == 0: column.MgNum = None
if column.MgO is not None and column.MgO.size == 0: column.MgO = None
if column.FeO is not None and column.FeO.size == 0: column.FeO = None
if column.CaO.size == 0: column.CaO = None
if column.temperature.size == 0: column.temperature = None


# check geological layers
check_layers(column, args.allowquartz, args.maxsedthick, args.allowuhp, args.allowsalt)
check_layer_depth(column)


# check the datum

if column.coordsys == "Geographic":
    if column.longitude is None and column.latitude is not None:
        print (error() + "a value for longitude was not provided")
        exit()
    if column.latitude is None and column.longitude is not None:
        print (error() + "a value for latitude was not provided")
        exit()

elif column.coordsys == "Cartesian":
    if column.x is None and column.y is not None:
        print (error() + "a value for x coordinate was not provided")
        exit()
    if column.y is None and column.x is not None:
        print (error() + "a value for y coordinate was not provided")
        exit()


# stop script execution if the comparison with reference models was not requested 
if args.file_refmodels == "noref": exit()


# read pressure model

pressuremodel = pressuredepth(args.file_pressure)
pressuremodel.read_pressure_model()

# actual data checks

# for each of the assesable physical quantities in the input file, try to find a match in the available reference models

print ("Assessing the following input model physical quantities: ")
print (highlight(" - ".join(column.columns[1:-1])))
for field in column.columns:

    if field == "Depth" or field == "Type": continue

    print ("Assessing " + highlight(field))

    # extract the data from class
    if field == "Temperature":
        data = column.temperature
    elif field == "Vp":
        data = column.Vp
    elif field == "Vs":
        data = column.Vs
    elif field == "Density":
        data = column.density
    elif field == "VpVs":
        data = column.VpVs
    elif field == "SiO2":
        data = column.SiO2
    elif field == "Al2O3":
        data = column.Al2O3
    elif field == "MgO":
        data = column.MgO
    elif field == "FeO":
        data = column.FeO
    elif field == "CaO":
        data = column.CaO
    elif field == "MgNum" or field == "Mg#":
        data = column.MgNum

    if args.pdf or args.png:
        fig = plt.figure()
        amin = min(column.depth)
        amin = amin - 0.1*abs(amin) #always going to the left
        amax = max(column.depth)
        amax = amax + 0.1*abs(amax) #always going to the right
        plt.xlim( [amin, amax] )
        amin = min(data[np.isfinite(data)])
        amin = amin - 0.1*abs(amin) #always going down
        amax = max(data[np.isfinite(data)])
        amax = amax + 0.1*abs(amax) #always going up
        plt.ylim( [amin, amax] )
        plt.title(column.name + ": " + field + " v depth")
        # plot the actual data
        plt.plot(column.depth, data, "o-", color='black', label='Data')

    # validate model using available references
    for imodel, refmodel in enumerate(referencemodels):

        # check the distance if necessary
        irecord = -1 # the number of line in the file to read
        mindist = args.dist
        if args.dist > 0.0:
            if refmodel.arraylongitude and refmodel.arraylatitude:
                for i, (lon, lat) in enumerate (zip(refmodel.arraylongitude, refmodel.arraylatitude)):
                    actdist = haversine (lon, lat, column.longitude, column.latitude)
                    if actdist is None:
                        print (error() + "haversine distance cannot be computed. Highly likely, the coordinates of an input data column were not provided.")
                        exit()
                    # within given radius
                    if args.dist > actdist:
                        # the fit is better
                        if mindist > actdist:
                            mindist = actdist
                            irecord = i
            else:
                continue

        refcol = referencecolumn(field, refmodel, irecord)


        # found indicates whether the field is actually available for the selected record
        found = refcol.refmodel_reader(pressuremodel)

        if not found:
            print ("Field not found; skipping")
            continue

        if refcol.solidus is not None or refcol.liquidus is not None:
            # if solidus or liduidus, do special thing
            validate_profile_melting(refcol, data, column.depth, args.d)
            # plotting
            if args.pdf or args.png:
                jmodel = imodel%len(plotcolours)
                if refcol.solidus is not None:
                    plt.plot(refcol.depths, refcol.solidus,  "o-", color=plotcolours[jmodel], label=refcol.name + " - solidus")
                if refcol.liquidus is not None:
                    plt.plot(refcol.depths, refcol.liquidus, "o-", color=plotcolours[jmodel], label=refcol.name + " - liquidus")

        else:
            # stack and match vertical profiles
            layernames, layermodel, layerref = match_layers(column.gn, column.depth.size, refcol.gn, refcol.depths.size)
            # two main validation options
            use_stdev = refcol.reference is not None
            if use_stdev:
                # checking the mean and stdevs
                mindifabs, mindifrel, maxdifrel, maxdifabs = validate_profile_stdev(refcol, layerref, data, column.depth, layermodel, args.d)
            else:
                # checking the value is between min and max
                mindifabs, mindifrel, maxdifrel, maxdifabs = validate_profile_minmax(refcol, layerref, data, column.depth, layermodel)

            # plotting
            if args.pdf or args.png:
                jmodel = imodel%len(plotcolours)
                if refcol.reference is not None:
                    plt.fill_between(refcol.depths, refcol.reference-refcol.sigmaminus, refcol.reference+refcol.sigmaplus, color = plotcolours[jmodel], alpha=0.2)
                    plt.plot(refcol.depths, refcol.reference, "o-", color=plotcolours[jmodel], label=refcol.name)
                else:
                    plt.plot(0, 0, "o", color=plotcolours[jmodel], label=refcol.name)
                    plt.fill_between(refcol.depths, refcol.minimum, refcol.maximum, color = plotcolours[jmodel], alpha=0.2)

            # print a short summary
            print_stacked_models(layernames, layermodel, layerref, column.depth, refcol.depths, mindifabs, mindifrel, maxdifrel, maxdifabs, use_stdev)

    # end of assessment for the selected thermodynamic property

    # save graphics is required
    if args.pdf or args.png:
        plt.legend()
        if args.pdf:
            filename = column.name + "-" + field + ".pdf"
        if args.png:
            filename = column.name + "-" + field + ".png"

        plt.savefig(filename)
        plt.close(fig)

# this function computes missing fields from those present
#column.Vp, column.Vs, column.VpVs = check_velocities( column.depth, column.Vp, column.Vs, column.VpVs )





