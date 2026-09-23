use numpy as np
import time
import os.path
import argparse

# local modules
import read_field, read_float, read_value from extract_prof
import check_velocities from check_velocities

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

# initialise a data structure for the inputs

class columndata:
   def __init__ (self):
      # column location and specification
      self.name      = None
      self.coordsys  = "Geographic"
      self.longitude = None
      self.latitude  = None
      self.x = None
      self.y = None
      # the last entry describing the crust; the mantle begins with Moho+1
      self.Moho  = 0
      # the last entry describing the lithosphere; the sublithosphere begins with LAB+1 
      self.LAB  = 0
      # column profiles
      self.columns = []
      self.depth = []
      self.SiO2  = []
      self.Al2O3 = []
      self.MgNum = []
      self.MgO   = []
      self.FeO   = []
      self.CaO   = []
      self.temperature = []
      self.Vp      = []
      self.Vs      = []
      self.VpVs    = []
      self.density = []

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

            column.columns = tmp

        # read the actual data
        for field, value in zip (column.columns, tmp):
            if field == "Depth":
                column.depth.append( read_value(value) )
            elif field == "Temperature"
                column.temperature.append( read_value(value) )
            elif field == "Vp"
                column.Vp.append( read_value(value) )
            elif field == "Vs"
                column.Vs.append( read_value(value) )
            elif field == "Density"
                column.density.append( read_value(value) )
            elif field == "VpVs"
                column.VpVs.append( read_value(value) )
            elif field == "SiO2"
                column.SiO2.append( read_value(value) )
            elif field == "Al2O3"
                column.Al2O3.append( read_value(value) )
            elif field == "MgO"
                column.MgO.append( read_value(value) )
            elif field == "FeO"
                column.FeO.append( read_value(value) )
            elif field == "CaO"
                column.CaO.append( read_value(value) )
            elif field == "MgNum"
                column.MgNum.append( read_value(value) )

        # convert to numpy arrays
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

        # add missing fields

        if not column.VpVs and column.Vp and column.Vs:
            column.VpVs = np.divide(column.Vp, column.Vs, out=np.full_like(column.Vp, np.nan), where=np.isfinite(column.Vs) & (column.Vs != 0))
        elif column.VpVs and not column.Vp and column.Vs:
            column.Vp = column.VpVs * column.Vs
        elif column.VpVs and column.Vp and not column.Vs:
            column.Vs = np.divide(column.Vp, column.VpVs, out=np.full_like(column.Vp, np.nan), where=np.isfinite(column.VpVs) & (column.VpVs != 0))
        else:
            for vpvs, vp, vs in zip (column.VpVs , column.Vp , column.Vs)
                if not np.isfinite(vpvs):
                    if vs != 0.0: 
                        print ("The following Vp, Vs, Vp/Vs values are inconsistent: " + str(Vp) + ", " + str(Vs) + ", " + str(Vp/Vs))
                    continue
                if vpvs - vp/vs > 1.e-3:
                    print ("The following Vp, Vs, Vp/Vs values are inconsistent: " + str(Vp) + ", " + str(Vs) + ", " + str(Vp/Vs))




