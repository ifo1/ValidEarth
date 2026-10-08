#!/usr/bin/python3

import numpy as np
import os.path
import argparse
import matplotlib.pyplot as plt

plotcolours = ["red", "blue", "green", "orange", "violet", "brown"]

# local modules
from read_values import read_field, read_float, read_value
from colouredstrings import error, warning, highlight, green, red
from rockcompare import find_matching_rocks, plot_rock_properties

# local classes
from classes import rocktype, rockproperty

# read command line arguments

parser = argparse.ArgumentParser()
parser.add_argument("-i", dest="inputfile", default="", help="An input file with structure to verify")
parser.add_argument("-delim", dest="delimiter", default=None, help="Delimiter between all columns")
parser.add_argument("-refmodels", dest="file_refmodels", default="configrocks.txt", help="A list of reference models to compare the data with")
parser.add_argument("-printrefmodels", dest="report_file_refmodels", action="store_true", help="Print a list with all loaded reference models (mostly for testing/debugging purposes)")
parser.add_argument("-detailed", dest="detailed",action="store_true",help="Highlight rock matching criteria")
parser.add_argument("-pdf", dest="pdf",action="store_true",help="Create pdf plots")
parser.add_argument("-png", dest="png",action="store_true",help="Create png plots")
parser.add_argument("-output", dest="output",default="./",help="A directory to store images figures")
parser.add_argument('-rt', '--rock-type', action="append", default=[], dest="rocktypes", help="Compare only the supplied rock types: Igneous, Metamorphic, Volcanic, Liquids, Regolith, Sedimentary")
parser.add_argument("-minrefrockprop", dest="minrockprop",type=int,default=1,help="The minumum number of supplied physical properties for reference rocks to compare with.")
args = parser.parse_args()

# verify the input file exists
if not os.path.isfile(args.inputfile):
    print (error() + "input file "+args.inputfile+" does not exist!")
    exit()

# read the list of reference models
if not os.path.isfile(args.file_refmodels):
    print (error() + "catalog file "+args.file_refmodels+" does not exist!")
    exit()

# capitalise the rock types
args.rocktypes = [w.upper() for w in args.rocktypes]


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
                elif field == "type":
                    rock.genesis = value.upper().split("+")
                    if rock.genesis:
                        if "N" in rock.genesis:
                            rock.genesis.remove("N")
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
                    if new and (np.isfinite(target.mean) or np.isfinite(target.min) or np.isfinite(target.max) or np.isfinite(target.stdev)):
                        rock.properties.append(target)

            # append only if this rock type was requested
            if rock.genesis and args.rocktypes:
                if any(map(lambda v: v in args.rocktypes, rock.genesis)):
                    # append only if there are more than N physical properties available
                    if len(rock.properties) >= args.minrockprop:
                        rocks.append(rock)
            else:
                # append only if there are more than N physical properties available
                if len(rock.properties) >= args.minrockprop:
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
print ("Reading reference rock properties from " + highlight (args.file_refmodels))
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

    if args.report_file_refmodels:
        print ("Printing a list of reference rock models")
        for model in refrocks:
            print (str(model.lithology) + " by " + str(model.citation) + " belongs to type " + str(model.genesis[0]) + " with following properties:")
            for prop in model.properties:
                print ("    - " + str(prop.parameter) + " from " + str(prop.min) + " to " + str(prop.max) + " with mean " + str(prop.mean) + " and stdev " + str(prop.stdev))


# read data file
print ("Reading rock properties from " + highlight (args.inputfile))
inputrocks = read_rock_file(args.inputfile)

find_matching_rocks(refrocks, inputrocks, args.detailed)

for rock in inputrocks:
    if rock.matching:
        print(rock.name + green(" matches ") + " - ".join(rock.matching))
    else:
        print(rock.name + red(" does not match any reference"))

if args.pdf or args.png:
    plot_rock_properties(refrocks, inputrocks, output_dir=args.output)


