use numpy as np
import time
import os.path
import argparse

# read command line arguments

parser = argparse.ArgumentParser()
parser.add_argument("-i", dest="inputfile", help="Input file to verify")
parser.add_argument("-d", dest="delimiter", default=None, help="Delimiter between all columns")
args = parser.parse_args()

# verify the input file exists

if not os.path.isfile(args.inputfile):
    print ("Fatal error: input file "+inputfile+" does not exist!")
    exit()

# initialise a data structure for the inputs

class columndata:
   def __init__ (self):
      # column location and specification
      self.name      = None
      self.coordsys  = "Geographic"
      self.longitude = None
      self.latitude  = None
      self.x = None
      self.y  = None
      # the last entry describing the crust; the mantle begins with Moho+1
      self.Moho  = 0
      # the last entry describing the lithosphere; the sublithosphere begins with LAB+1 
      self.LAB  = 0
      # column profiles
      self.columns = None
      self.depth = None
      self.Al2O3 = None
      self.MgNum = None
      self.MgO   = None
      self.FeO   = None
      self.CaO   = None
      self.temperature = None
      self.Vp      = None
      self.Vs      = None
      self.density = None

column = columndata

# read the file

# flag data section
datatable = False
# flag crustal section
crust = True
# flag lithospheric mantle section
mantle_litho = False
# flag sublithospheric mantle section above 410 km (MTZ)
mantle_sublitho = False
# flag the Mantle Transition Zone
mantle_mtz = False
# flag the Lower Mantle
mantle_lower = False

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

        # if execution reached this point, it is reading the actual data table (vertical profiles)

        # read headers
        if tmp[0] == "Depth":

            # there can be only one data section
            if datatable:
                print ("Error: there can be only one data section in file")
                exit()

            datatable = True

            self.columns = tmp

