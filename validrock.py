#!/usr/bin/python3

import numpy as np
import os.path
import argparse
import matplotlib.pyplot as plt

plotcolours = ["red", "blue", "green", "orange", "violet", "brown"]

# local modules
from read_values import read_field, read_float, read_value
from colouredstrings import error, warning, highlight, green, red, yellow
from rockcompare import find_matching_rocks, plot_rock_properties, scatterplot_matrix

# local classes
from classes import rocktype, rockproperty

# read command line arguments

parser = argparse.ArgumentParser()
parser.add_argument("-i", dest="inputfile", default="", help="An input file with structure to verify")
parser.add_argument("-delim", dest="delimiter", default=None, help="Delimiter between all columns")
parser.add_argument("-refmodels", dest="file_refmodels", default="configrocks.txt", help="A list of reference models to compare the data with")
parser.add_argument("-printrefmodels", dest="report_file_refmodels", action="store_true", help="Print a list with all loaded reference models (mostly for testing/debugging purposes)")
parser.add_argument("-detailed", dest="detailed",action="store_true",help="Highlight rock matching criteria")
parser.add_argument("-pdf", dest="pdf",action="store_true",help="Save plots as PDF documents")
parser.add_argument("-png", dest="png",action="store_true",help="Save plots as PNG images")
parser.add_argument("-pngdpi", dest="pngdpi",type=int,default=300,help="The resolution (DPI) of PNG images; the default value is 300")
parser.add_argument("-output", dest="output",default="./",help="A directory to store images figures")
parser.add_argument('-rt', '--rock-type', action="append", default=[], dest="rocktypes", help="Compare only the supplied rock types: Igneous, Metamorphic, Volcanic, Liquids, Regolith, Sedimentary")
parser.add_argument("-minrefrockprop", dest="minrockprop",type=int,default=1,help="The minumum number of supplied physical properties for reference rocks to compare with.")
parser.add_argument("-histogram", dest="histograms",action="store_true",help="Create histograms for all properties for all rock samples with the same name")
parser.add_argument("-scatterplot", dest="scatterplots",action="store_true",help="Create Scatterplot Matrices for all properties for all rock samples with the same name")
parser.add_argument("-hist2d", dest="hist2d",action="store_true",help="Use 2D histogram (square tiles) for Scatterplot Matrices instead of a scatter plot (for big datasets)")
parser.add_argument("-hexbin", dest="hexbin",action="store_true",help="Use 2D HexBin histogram (hexagon tiles) for Scatterplot Matrices instead of a scatter plot (for big datasets)")
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


def read_rock_file(inputfile, getname = None):

    rocks = []

    if getname is not None: rock = rocktype(inputfile)
    with open(inputfile) as myfile:
        if getname is None: print (" - " + inputfile)
        for line in myfile:

            # skip empty lines and comments
            myline = line.strip()
            if len(myline) == 0: continue
            char = myline[0]
            if char == "#" or char == "!" or char == "/" or char == "%": continue

            tmp = myline.split()
            if tmp[0].lower() == "name" or tmp[0].lower() == "lithology":
                # must be the first valid entry
                columns = [x.lower() for x in tmp]
                continue

            if getname is None: rock = rocktype(inputfile)
            for value, field in zip(tmp, columns):

                if field == "name":
                    if getname is not None:
                        if value != getname: break
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
                    fieldtype = ""
                    for suffix in ["stdev","min","max"]:
                        if field.endswith(suffix):                  
                            fieldn = fieldn.removesuffix(suffix)
                            fieldtype = suffix

                    # update an existing class or create a new one
                    target = next((d for d in rock.properties if d.parameter == fieldn), None)
                    new = target is None
                    if new:
                        target = rockproperty(fieldn)

                    if getname is not None:
                        target.values.append(read_value(fieldn,value))
                    else:
                        # assign the value according to existing suffix
                        match fieldtype:
                            case "stdev":
                                target.stdev = read_value(field,value)
                            case "min":
                                target.min = read_value(field,value)
                            case "max":
                                target.max = read_value(field,value)
                            case default:
                                target.mean = read_value(field,value)

                    if new and (np.isfinite(target.mean) or np.isfinite(target.min) or np.isfinite(target.max) or np.isfinite(target.stdev) or len(target.values) > 0):
                        rock.properties.append(target)

            if getname is None: 
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

    if getname is None: 
        return rocks
    else:
        return rock

inputrocks = []

# if create histograms, run a simpler version 
if args.histograms or args.scatterplots:
    print("Reading unique files types from " + highlight (args.inputfile))
    uniqrocktypes = []
    with open(args.inputfile) as myfile:
        for line in myfile:
            # skip empty lines and comments
            myline = line.strip()
            if len(myline) == 0: continue
            char = myline[0]
            if char == "#" or char == "!" or char == "/" or char == "%": continue

            tmp = myline.split()
            if tmp[0].lower() == "name":
                # skip the header
                continue
            else:
                # append rock name if new
                if not tmp[0] in uniqrocktypes: uniqrocktypes.append(tmp[0])

    print ("The following rock types were detected: " + " ".join(uniqrocktypes))


    for uniqrocktype in uniqrocktypes:
        print ("Gathering statistics for: " + highlight(uniqrocktype))
        rocks = read_rock_file(args.inputfile, uniqrocktype)
        print ("Lithology       - parameter  -        min -        max -       mean -      stdev")

        # a separate plot for each parameter
        for quantity in rocks.properties:
            data = np.asarray(quantity.values)

            # filter the data
            data = data[np.isfinite(data)]
            quantity.min = np.min(data)
            quantity.max = np.max(data)
            quantity.mean = np.mean(data)
            quantity.stdev = np.std(data)
            print (highlight(uniqrocktype.ljust(15)) + " - " + highlight(quantity.parameter.ljust(10)) + " - " + \
                str(round(quantity.min,2)).rjust(10) + " - " + str(round(quantity.max,2)).rjust(10) + " - " + \
                str(round(quantity.mean,2)).rjust(10) + " - " + str(round(quantity.stdev,2)).rjust(10))

            if (args.png or args.pdf) and args.histograms:
                fig, ax = plt.subplots()

                ax.hist(data, bins=30, alpha=0.7)

                ax.axvline(mean, color="red", linestyle="-", label="Mean " + uniqrocktype + " " + quantity.parameter)

                if stdev > 0:
                    for n in range(1,4):
                        ax.axvline(mean + n * stdev, color="black", linestyle="--", alpha=0.6)
                        ax.axvline(mean - n * stdev, color="black", linestyle="--", alpha=0.6)

                ax.set_xlabel(uniqrocktype + " - " + quantity.parameter)
                plt.ticklabel_format(style="plain", axis="x", useOffset=False)
                ax.set_ylabel("Number of Values (Frequency)")
                ax.legend()

                plt.tight_layout()
                if args.png:
                    fig.savefig( os.path.join(args.output, uniqrocktype + "-" + quantity.parameter + ".png" ), bbox_inches="tight", dpi=args.pngdpi )
                if args.pdf:
                    fig.savefig( os.path.join(args.output, uniqrocktype + "-" + quantity.parameter + ".pdf" ), bbox_inches="tight" )
                plt.close()
                

        if (args.png or args.pdf) and args.scatterplots:
            scatterplot_matrix(args.output, rocks, args.png, args.pngdpi, args.pdf, args.hist2d, args.hexbin)

        inputrocks.append(rocks)

    if not (args.png or args.pdf):
        if args.histograms:
            print (yellow("Attention! ValidRock does not produce any histograms as no output format was specified"))
        if args.scatterplots:
            print (yellow("Attention! ValidRock does not produce any scatterplot matrices as no output format was specified"))



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
print ("Reading rock properties from the input file")
if not inputrocks: inputrocks = read_rock_file(args.inputfile)

find_matching_rocks(refrocks, inputrocks, args.detailed)


for rock in inputrocks:
    if rock.matching:
        print(rock.name + green(" matches ") + " - ".join(rock.matching))
    else:
        print(rock.name + red(" does not match any reference"))

if args.pdf or args.png:
    plot_rock_properties(refrocks, inputrocks, output_dir=args.output)


