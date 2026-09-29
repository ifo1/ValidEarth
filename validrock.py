import numpy as np
import os.path
import argparse
import matplotlib.pyplot as plt

plotcolours = ["red", "blue", "green", "orange", "violet", "brown"]

# local modules
from read_values import read_field, read_float, read_value
from colouredstrings import error, warning, highlight
from check_data import check_velocities
from rockcompare import find_matching_rocks, plot_rock_properties

# local classes
from classes import rocktype, rockproperty

# read command line arguments

parser = argparse.ArgumentParser()
parser.add_argument("-i", dest="inputfile", default="", help="An input file with structure to verify")
parser.add_argument("-delim", dest="delimiter", default=None, help="Delimiter between all columns")
parser.add_argument("-utemp", dest="utemp", default="K", help="Temperature units: K [default] or C")
parser.add_argument("-uvp", dest="uvp", default="m/s", help="Vp units: m/s [default] or km/s")
parser.add_argument("-uvs", dest="uvs", default="m/s", help="Vs units: m/s [default] or km/s")
parser.add_argument("-udepth", dest="udepth", default="m", help="Depth units: m [default] or km")
parser.add_argument("-udens", dest="udens", default="kg/m3", help="Density units: kg/m3 [default] or g/cm3")
parser.add_argument("-refmodels", dest="file_refmodels", default="configrocks.txt", help="A list of reference models to compare the data with")
parser.add_argument("-detailed", dest="d",action="store_true",help="Print out a detailed layer-by-layer comparison")
parser.add_argument("-pdf", dest="pdf",action="store_true",help="Create pdf plots")
parser.add_argument("-png", dest="png",action="store_true",help="Create png plots")
args = parser.parse_args()

# verify the input file exists
if not os.path.isfile(args.inputfile):
    print (error() + "input file "+args.inputfile+" does not exist!")
    exit()

# read the list of reference models
if not os.path.isfile(args.file_refmodels):
    print (error() + "catalog file "+args.file_refmodels+" does not exist!")
    exit()

print ("Reading a list of rock properties from " + highlight (args.file_refmodels))


def read_rock_file(inputfile):

    rocks = []

    with open(inputfile) as myfile:
        print (" - " + inputfile)
        iline = 0
        for line in myfile:
            iline += 1

            # skip empty lines and comments
            if len(line.strip()) == 0: continue
            char = line.strip()[0]
            if char == "#" or char == "!" or char == "/" or char == "%": continue

            tmp = line.lower().strip().split()
            if tmp[0] == "name" or tmp[0] == "lithology":
                # must be the first valid entry
                columns = tmp
                continue

            rock = rocktype(inputfile)
            for value, field in zip(tmp, columns):

                if field == "name":
                    rock.name = value
                elif field == "citation":
                    rock.citation = value
                elif field == "lithology":
                    rock.lithology = value
                elif field == "temperature":
                    rock.temperature = value
                elif field == "pressure":
                    rock.pressure = value
                else:
                    # add a data field
                    fieldn = field
                    #fieldn = ""
                    fieldtype = ""
                    for suffix in ["stdev","min","max"]:
                        if field.endswith(suffix):                  
                            fieldn = fieldn.removesuffix(suffix)
                            fieldtype = suffix

                    # update an existing class or create a new one
                    target = next((d for d in rock.properties if d.parameter == fieldn), None)
                    new = target is None
                    if new:
                        new = True
                        target = rockproperty(fieldn)

                    # assign the value
                    match fieldtype:
                        case "stdev":
                            target.stdev = read_value(field,value)
                        case "min":
                            target.min = read_value(field,value)
                        case "max":
                            target.max = read_value(field,value)
                        case default:
                            target.mean = read_value(field,value)
                    attrs = vars(target)
                    if new:
                        rock.properties.append(target)
            rocks.append(rock)

    # for debugging
    if False:
        for rock in rocks:
            attrs = vars(rock)
            print(', '.join("%s: %s" % item for item in attrs.items()))
            for item in rock.properties:
                attrs2 = vars(item)
                print(', '.join("%s: %s" % item for item in attrs2.items()))
            print (rock)

    return rocks


# read reference models
refrocks = []

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

        # concatenate lists of rocks
        refrocks += read_rock_file(line.strip())


# read data file
inputrocks = read_rock_file(args.inputfile)

find_matching_rocks(refrocks, inputrocks)

for rock in inputrocks:
    print(rock.name + " matches " + " - ".join(rock.matching))

plot_rock_properties(
    refrocks,
    inputrocks,
    output_dir="rock_plots",
)


