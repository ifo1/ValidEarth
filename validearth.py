import numpy as np
import os.path
import argparse
import matplotlib.pyplot as plt

plotcolours = ["red", "blue", "green", "orange", "violet", "brown"]

# local modules
from datachecks import read_field, read_float, read_value
from colouredstrings import error, warning, highlight
from check_velocities import check_velocities

# local classes
from classes import columndata, pressuredepth, match_layers, print_stacked_models, referencecolumn, validate_profile_stdev, validate_profile_minmax, haversine

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
parser.add_argument("-refmodels", dest="file_refmodels", default="config.txt", help="A list of reference models to compare the data with")
parser.add_argument("-detailed", dest="d",action="store_true",help="Print out a detailed layer-by-layer comparison")
parser.add_argument("-pdf", dest="pdf",action="store_true",help="Create pdf plots")
parser.add_argument("-png", dest="png",action="store_true",help="Create png plots")
parser.add_argument("-dist", dest="dist", default=0.0,type=float,help="The maximum distance (m) from the reference model to the input column")
args = parser.parse_args()

# verify the input file exists
if not os.path.isfile(args.inputfile):
    print (error() + "input file "+args.inputfile+" does not exist!")
    exit()

# read the list of reference models
if not os.path.isfile(args.file_refmodels):
    print (error() + "catalog file "+args.file_refmodels+" does not exist!")
    exit()

print ("Reading the list of reference models from " + highlight (args.file_refmodels))
refmodelfiles = []
with open(args.file_refmodels) as myfile:

    # read each line and parse it
    datatable = False

    for line in myfile:

        # skip empty lines and comments
        if len(line.strip()) == 0: continue
        char = line.strip()[0]
        if char == "#" or char == "!" or char == "/" or char == "%": continue

        #check whether the reference model exists
        if not os.path.isfile(line.strip()):
            print (error() + "the reference model file "+line.strip()+" does not exist!")
            exit()

        refmodelfiles.append(line.strip())


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

            column.name, flag = read_field("Name", tmp, column.name)
            if flag: continue

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

        # read the actual data
        for field, value in zip (column.columns, tmp):
            if field == "Depth":
                locdepth = read_value(field,value)
                if len(column.depth) > 1:
                    if locdepth < column.depth[-1]:
                        print (error(locdepth) + "the depth is not non-decreasing in the input file!")
                        exit()
                column.depth.append( locdepth )
            elif field == "Temperature":
                column.temperature.append( read_value(field,value) )
            elif field == "Vp":
                column.Vp.append( read_value(field,value) )
            elif field == "Vs":
                column.Vs.append( read_value(field,value) )
            elif field == "Density":
                column.density.append( read_value(field,value) )
            elif field == "VpVs":
                column.VpVs.append( read_value(field,value) )
            elif field == "SiO2":
                column.SiO2.append( read_value(field,value) )
            elif field == "Al2O3":
                column.Al2O3.append( read_value(field,value) )
            elif field == "MgO":
                column.MgO.append( read_value(field,value) )
            elif field == "FeO":
                column.FeO.append( read_value(field,value) )
            elif field == "CaO":
                column.CaO.append( read_value(field,value) )
            elif field == "MgNum" or field == "Mg#":
                column.MgNum.append( read_value(field,value) )
            elif field == "Type":
                if value is not None: column.gn.assign_gn(value, len(column.depth)-1)



# convert data to numpy arrays
column.depth = np.asarray(column.depth)
column.SiO2  = np.asarray(column.SiO2)
column.Al2O3 = np.asarray(column.Al2O3)
column.MgNum = np.asarray(column.MgNum)
column.MgO   = np.asarray(column.MgO)
column.FeO   = np.asarray(column.FeO)
column.CaO   = np.asarray(column.CaO)
column.temperature = np.asarray(column.temperature)
column.Vp      = np.asarray(column.Vp)
column.Vs      = np.asarray(column.Vs)
column.VpVs    = np.asarray(column.VpVs)
column.density = np.asarray(column.density)

# convert to SI units
if args.udepth == "km":   column.depth *= 1000
if args.utemp == "C":     column.temperature += 273.15
if args.uvp == "km/s":    column.Vp *= 1000
if args.uvs == "km/s":    column.Vs *= 1000
if args.udens == "g/cm3": column.density *= 1000

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

column.gn.report_gn(column.depth)

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
        plt.plot(column.depth, data, "o-", color='black', label='Data')
        plt.title(column.name + ": " + field + " v depth")

    # trying to validate using PREM
    for imodel, refmodelfile in enumerate(refmodelfiles):
        refcol = referencecolumn(field, refmodelfile)

        # check that the distance between the reference column and the input one does not exceed the threshold
        if args.dist > 0:
            actdist = haversine (column.longitude, column.latitude, refcol.longitude, refcol.latitude)
            if actdist is None:
                print ("Skipping the reference model as the distance cannot be evaluated")
                continue
            if actdist > args.dist:
                print ("Skipping the reference model as its not within the prescribed radius: " + str(actdist))
                continue

        found = refcol.refmodel_reader()
        if not found: continue

        if args.pdf or args.png:
            if refcol.reference is not None:
                jmodel = imodel%len(plotcolours)
                plt.plot(refcol.depths, refcol.reference, "o-", color=plotcolours[jmodel], label=refcol.name)
            else:
                plt.plot(0, 0, "o", color=plotcolours[jmodel], label=refcol.name)
                plt.fill_between(refcol.depths, refcol.minimum, refcol.maximum, color = plotcolours[jmodel], alpha=0.2)

        layernames, layermodel, layerref = match_layers(column.gn, column.depth.size, refcol.gn, refcol.depths.size)
        # two main validation options
        use_stdev = refcol.reference is not None
        if use_stdev:
            # checking the mean and stdevs
            mindifabs, mindifrel, maxdifrel, maxdifabs = validate_profile_stdev(refcol, layerref, data, column.depth, layermodel, args.d)
        else:
            # checking the value is between min and max
            mindifabs, mindifrel, maxdifrel, maxdifabs = validate_profile_minmax(refcol, layerref, data, column.depth, layermodel)

        print_stacked_models(layernames, layermodel, layerref, column.depth, refcol.depths, mindifabs, mindifrel, maxdifrel, maxdifabs, use_stdev)

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





