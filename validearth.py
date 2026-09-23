use numpy as np
import time
import os.path
import argparse
from termcolor import colored

# local modules
import read_field, read_float, read_value from extract_prof
import error, warning from colouredstrings
import check_velocities from check_velocities

# local classes
import columndata from classes

# read command line arguments

parser = argparse.ArgumentParser()
parser.add_argument("-i", dest="inputfile", help="Input file to verify")
parser.add_argument("-d", dest="delimiter", default=None, help="Delimiter between all columns")
parser.add_argument("-utemp", dest="utemp", default="K", help="Temperature units: K [default] or C")
parser.add_argument("-uvp", dest="uvp", default="m/s", help="Vp units: m/s [default] or km/s")
parser.add_argument("-uvs", dest="uvs", default="m/s", help="Vs units: m/s [default] or km/s")
parser.add_argument("-udepth", dest="udepth", default="m", help="Depth units: m [default] or km")
parser.add_argument("-udens", dest="udens", default="kg/m3", help="Density units: kg/m3 [default] or g/cm3")
args = parser.parse_args()

# verify the input file exists

if not os.path.isfile(args.inputfile):
    print ("Fatal error: input file "+inputfile+" does not exist!")
    exit()

# initialise a class for the inputs
column = columndata

# read the file

# flag data section
datatable = False
# flags for crustal section
i_crust_soil = False
i_crust_regolith = False
i_crust_sediment = False
i_crust_upper = False
i_crust_middle = False
i_crust_lower = False
# flag lithospheric mantle section
i_mantle_litho = False
# flag sublithospheric mantle section above 410 km (MTZ)
i_mantle_sublitho = False
# flag the Mantle Transition Zone
i_mantle_mtz = False
# flag the Lower Mantle
i_mantle_lower = False

# read the input file

with open(args.inputfile) as myfile:

    # read each line and parse it

    for line in myfile:

        # split the line into a list of strings

        # skip empty lines and comments
        if len(line.strip()) == 0: continue
        char = line.strip()[0]
        if char == "#" or char == "!" or char == "/": continue

        # get a list of values from the line
        if args.delimiter is not None:
            tmp = line.strip().split(args.delimiter)
        else:
            tmp = line.strip().split()

        # check the header
        if not datatable:

            column.name, flag = read_field("Name", tmp)
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

        # pad the Type column with None if it exists
        if len(tmp) == len(column.columns-1):
            tmp.append(None)

        # read the actual data
        for field, value in zip (column.columns, tmp):
            if field == "Depth":
                column.depth.append( read_value(value) )
            elif field == "Temperature":
                column.temperature.append( read_value(value) )
            elif field == "Vp":
                column.Vp.append( read_value(value) )
            elif field == "Vs":
                column.Vs.append( read_value(value) )
            elif field == "Density":
                column.density.append( read_value(value) )
            elif field == "VpVs":
                column.VpVs.append( read_value(value) )
            elif field == "SiO2":
                column.SiO2.append( read_value(value) )
            elif field == "Al2O3":
                column.Al2O3.append( read_value(value) )
            elif field == "MgO":
                column.MgO.append( read_value(value) )
            elif field == "FeO":
                column.FeO.append( read_value(value) )
            elif field == "CaO":
                column.CaO.append( read_value(value) )
            elif field == "MgNum" or field == "Mg#":
                column.MgNum.append( read_value(value) )
            elif field == "Type":
                if value is not None:
                    # assign the provided tag index to a corresponding variable 
                    value = value.lower()
                    n = len(column.depth)
                    match value:
                        case "soil":
                            i_crust_soil = n
                        case "regolith":
                            i_crust_regolith = n
                        case "sediments":
                            i_crust_sediment = n
                        case "crustupper":
                            i_crust_upper = n
                        case "crustmiddle":
                            i_crust_middle = n
                        case "crustlower":
                            i_crust_lower = n
                        case "Moho":
                            i_crust_lower = n
                        case "mantlelitho":
                            i_mantle_litho = n
                        case "LAB":
                            i_mantle_litho = n
                        case "mantleupper":
                            i_mantle_sublitho = n
                        case "410km":
                            i_mantle_sublitho = n
                        case "mantlemtz":
                            i_mantle_mtz = n
                        case "670km":
                            i_mantle_mtz = n
                        case "mantlelower":
                            i_mantle_lower = n


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
        if args.udepth = "km":   column.depth *= 1000
        if args.utemp = "C":     column.temperature += 273.15
        if args.uvp = "km/s":    column.Vp *= 1000
        if args.uvs = "km/s":    column.Vs *= 1000
        if args.udens = "g/cm3": column.density *= 1000

# print information about the column

print ("Checking file " + colored (args.inputfile, 'cyan') + " column " + colored (column.Name, 'cyan'), end='')

if column.coordsys == "Geographic":
    if column.longitude is None:
        print (error() + "a value for longitude was not provided")
        exit()
    if column.latitude is None:
        print (error() + "a value for latitude was not provided")
        exit()
    print (" with longitude " + colored (str(column.longitude), 'cyan') + " and latitude " + colored (str(column.latitude), 'cyan') )

elif column.coordsys == "Cartesian":
    if column.x is None:
        print (error() + "a value for x coordinate was not provided")
        exit()
    if column.y is None:
        print (error() + "a value for y coordinate was not provided")
        exit()
    print (" with X " + colored (str(column.longitude), 'cyan') + " and Y " + colored (str(column.latitude), 'cyan') )

else:
    print ("")

print ("Checking the following properties:")
print (" - ".join(column.columns)

# actual data checks

# this function computes missing fields from those present
column.Vp, column.Vs, column.VpVs = check_velocities( column.Depth, column.Vp, column.Vs, column.VpVs, Crust, Mantle )





