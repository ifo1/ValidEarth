from termcolor import colored
import numpy as np
import os.path

from colouredstrings import error, warning, highlight
from datachecks import read_value


def linear_interp(xi, xarr, yarr):
    # linear interpolation for numpy vectors
    # implies non-decreasing xarr
    yi = np.nan
    # extrapolate below the first value using the first slope
    if xi <= xarr[0]:
        yi = yarr[0] - (xarr[0] - xi) * (yarr[1] - yarr[0]) / (xarr[1] - xarr[0])
    # extrapolate above the last value using the last slope
    elif xi >= xarr[-1]:
        yi = yarr[-1] + (xi - xarr[-1]) * (yarr[-1] - yarr[-2]) / (xarr[-1] - xarr[-2])
    # I do not use here np.interp function, as it expects increasing sequence;
    # however, the PREM profile is non-decreasing rather than increasing
    else:
        for i in range (xarr.size-1):
            if xi <= xarr[i+1]:
                yi = yarr[i] + (xi - xarr[i]) * (yarr[i+1] - yarr[i]) / (xarr[i+1] - xarr[i])

    if not np.isfinite(yi): print (error() + "Cannot interpolate linearly for x = " + str(xi))

    return yi


def match_layers(model_ind, model_nlay, ref_ind, ref_nlay):
    # match the locations of layers in the input file and in the reference model 
    # this function is necessary because some of the layers might be missing in the input model and in the 
    # in the end, it stacks the profiles to produce a "composite cross-section"
    # Inputs
    # model_ind  - indices (golden nails) in the input array
    # model_nlay - the number of layers in the input data table
    # ref_ind    - indices (golden nails) in the reference array
    # ref_nlay   - the number of layers in the reference data table
    # Outputs
    # layernames - a list of layer names
    # layermodel - a list of layer indices for the input model
    # layerref   - a list of corresponding layer indices for the reference model 

    layernames = []
    layermodel = [0]
    layerref   = [0]

    if model_nlay <= 0:
        print (error() + "the input data file contains no records")
        exit()

    if ref_nlay <= 0:
        print (error() + "the reference file contains no records")
        exit()

    if model_ind.water > 0 and ref_ind.water > 0:
        layernames.append("Water")
        layermodel.append(model_ind.water)
        layerref.append(ref_ind.water)

    if model_ind.crust_soil > 0 and ref_ind.crust_soil > 0:
        layernames.append("Soil")
        layermodel.append(model_ind.crust_soil)
        layerref.append(ref_ind.crust_soil)

    if model_ind.crust_regolith > 0 and ref_ind.crust_regolith > 0:
        layernames.append("Regolith")
        layermodel.append(model_ind.crust_regolith)
        layerref.append(ref_ind.crust_regolith)

    if model_ind.crust_sediment > 0 and ref_ind.crust_sediment > 0:
        layernames.append("Sediments")
        layermodel.append(model_ind.crust_sediment)
        layerref.append(ref_ind.crust_sediment)

    if model_ind.crust_upper > 0 and ref_ind.crust_upper > 0:
        layernames.append("Upper Crust")
        layermodel.append(model_ind.crust_upper)
        layerref.append(ref_ind.crust_upper)

    if model_ind.crust_middle > 0 and ref_ind.crust_middle > 0:
        layernames.append("Middle Crust")
        layermodel.append(model_ind.crust_middle)
        layerref.append(ref_ind.crust_middle)

    if model_ind.crust_lower > 0 and ref_ind.crust_lower > 0:
        layernames.append("Lower Crust")
        layermodel.append(model_ind.crust_lower)
        layerref.append(ref_ind.crust_lower)

    if model_ind.mantle_litho > 0 and ref_ind.mantle_litho > 0:
        layernames.append("Lithospheric Mantle")
        layermodel.append(model_ind.mantle_litho)
        layerref.append(ref_ind.mantle_litho)

    if model_ind.mantle_sublitho > 0 and ref_ind.mantle_sublitho > 0:
        layernames.append("Sublithospheric Mantle")
        layermodel.append(model_ind.mantle_sublitho)
        layerref.append(ref_ind.mantle_sublitho)

    if model_ind.mantle_mtz > 0 and ref_ind.mantle_mtz > 0:
        layernames.append("Mantle Transition Zone")
        layermodel.append(model_ind.mantle_mtz)
        layerref.append(ref_ind.mantle_mtz)

    if model_ind.mantle_lower > 0 and ref_ind.mantle_lower > 0:
        layernames.append("Lower Mantle")
        layermodel.append(model_ind.mantle_lower)
        layerref.append(ref_ind.mantle_lower)

    # finalise the arrays if they do not have layer types assigned at the end of profile
    # one is subtracted as it is the size of an array with indexing starting from 0 
    if layermodel[-1] < model_nlay-1 and layerref[-1] < ref_nlay-1:
        layernames.append("Undifferentiated")
        layermodel.append(model_nlay-1)
        layerref.append(ref_nlay-1)
    elif layermodel[-1] < model_nlay-1:
        print ("Everything in the input model which lies below the " + layernames[-1] + " will be ignored when comparing with this model")

    return layernames, layermodel, layerref


class goldennaildata:
    def __init__ (self):
        self.water = -1
        # crustal section
        self.crust_soil = -1
        self.crust_regolith = -1
        self.crust_sediment = -1
        self.crust_upper = -1
        self.crust_middle = -1
        self.crust_lower = -1
        # lithospheric mantle section
        self.mantle_litho = -1
        # sublithospheric mantle section above 410 km (MTZ)
        self.mantle_sublitho = -1
        # Mantle Transition Zone
        self.mantle_mtz = -1
        # Lower Mantle
        self.mantle_lower = -1

    def assign_gn(self, tag, n):
        # assign the provided tag index to a corresponding variable 
        value = tag.lower()
        match value:
            case "water":
                self.water = n
            case "soil":
                self.crust_soil = n
            case "regolith":
                self.crust_regolith = n
            case "sediments":
                self.crust_sediment = n
            case "crustupper":
                self.crust_upper = n
            case "crustmiddle":
                self.crust_middle = n
            case "crustlower":
                self.crust_lower = n
            case "moho":
                self.crust_lower = n
            case "mantlelitho":
                self.mantle_litho = n
            case "lab":
                self.mantle_litho = n
            case "mantleupper":
                self.mantle_sublitho = n
            case "410km":
                self.mantle_sublitho = n
            case "mantlemtz":
                self.mantle_mtz = n
            case "670km":
                self.mantle_mtz = n
            case "mantlelower":
                self.mantle_lower = n
            case default:
                print (warning() + "type " + value + " is not known")

    def report_gn(self, depth):
        if self.water >= 0 or self.crust_soil >= 0 or self.crust_regolith >= 0 or self.crust_sediment >= 0 or \
            self.crust_upper >= 0 or self.crust_middle >= 0 or self.crust_lower >= 0 or \
            self.mantle_litho >= 0 or self.mantle_sublitho >= 0 or self.mantle_mtz >= 0 or self.mantle_lower >= 0:
            print ("The following golden nails are used")
        if self.water >= 0:           print (" - Water layer ends at depth " + str(depth[self.water]) + " (node " + str(self.water+1) + ")")
        if self.crust_soil >= 0:      print (" - Soil layer ends at depth " + str(depth[self.crust_soil]) + " (node " + str(self.crust_soil+1) + ")")
        if self.crust_regolith >= 0:  print (" - Regolith layer ends at depth " + str(depth[self.crust_regolith]) + " (node " + str(self.crust_regolith+1) + ")")
        if self.crust_sediment >= 0:  print (" - Sedimentary layer ends at depth " + str(depth[self.crust_sediment]) + " (node " + str(self.crust_sediment+1) + ")")
        if self.crust_upper >= 0:     print (" - Upper crust ends at depth " + str(depth[self.crust_upper]) + " (node " + str(self.crust_upper+1) + ")")
        if self.crust_middle >= 0:    print (" - Middle crust ends at depth " + str(depth[self.crust_middle]) + " (node " + str(self.crust_middle+1) + ")")
        if self.crust_lower >= 0:     print (" - Lower crust ends at depth " + str(depth[self.crust_lower]) + " (node " + str(self.crust_lower+1) + ")")
        if self.mantle_litho >= 0:    print (" - Lithospheric mantle ends at depth " + str(depth[self.mantle_litho]) + " (node " + str(self.mantle_litho+1) + ")")
        if self.mantle_sublitho >= 0: print (" - Sublithospheric mantle ends at depth " + str(depth[self.mantle_sublitho]) + " (node " + str(self.mantle_sublitho+1) + ")")
        if self.mantle_mtz >= 0:      print (" - Mantle Transition zone ends at depth " + str(depth[self.mantle_mtz]) + " (node " + str(self.mantle_mtz+1) + ")")
        if self.mantle_lower >= 0:    print (" - Lower mantle ends at depth " + str(depth[self.mantle_lower]) + " (node " + str(self.mantle_lower+1) + ")")


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
        self.gn     = goldennaildata()



class referencecolumn:
    def __init__ (self, keyword, filename):
        self.filename = filename
        self.parameter = keyword
        self.name = None
        self.citation = None
        # the actual reference profile expressed in terms of depth or pressure
        self.depths = []
        self.pressure = []
        # 1 sigma intervals on the left and on the right hand sides of the actual observation
        self.reference = []
        self.sigmaplus = []
        self.sigmaminus = []
        # alternatively, max and min bounds
        self.maximum = []
        self.minimum = []
        self.gn = goldennaildata()

    def refmodel_reader(self):
        # read the reference model from a supplied file
        print ("Reading " + self.filename)

        with open (self.filename, 'r') as myfile:

            header = True
            columns = []

            for line in myfile:

                # skip empty lines and comments
                if len(line.strip()) == 0: continue
                char = line.strip()[0]
                if char == "#" or char == "!" or char == "/" or char == "%": continue

                tmp = line.strip().split()

                if header:

                    if tmp[0] == "Name":
                        self.name = tmp[1]
                        print ("Using " + highlight(self.name) + " as a reference for " + self.parameter)

                    elif tmp[0] == "Citation":
                        self.citation = tmp[1]

                    elif tmp[0] == "Depth" or tmp[0] == "Presure":
                        columns = tmp
                        header = False
                        if columns[-1] != "Type":
                            columns.append("Type")

                else:
                    # pad the Type column with None
                    if len(tmp) == len(column.columns)-1:
                        tmp.append(None)

                    # read the actual data table
                    for field, value in zip (columns, tmp):
                        if field == "Depth":
                            locdepth = read_value(field,value)
                            if len(self.depths) >= 1:
                                if locdepth < self.depths[-1]:
                                    print (error(locdepth) + "the depth is not non-decreasing in the reference file!")
                                    exit()
                            column.depths.append( locdepth )
                        elif field == self.parameter:
                            self.reference.append( read_value(field,value) )
                        elif field == self.parameter+"Max":
                            self.maximum.append( read_value(field,value) )
                        elif field == self.parameter+"Min":
                            self.minimum.append( read_value(field,value) )

                        elif field == self.parameter+"Sigma":
                            self.sigmaplus.append( read_value(field,value) )
                            self.sigmaminus.append( read_value(field,value) )
                        elif field == self.parameter+"Sigma+":
                            self.sigmaplus.append( read_value(field,value) )
                        elif field == self.parameter+"Sigma-":
                            self.sigmaminus.append( read_value(field,value) )

                        elif field == self.parameter+"%":
                            if not self.reference:
                                print (error(self.depths[-1]) + " the relative uncertainty column must be after the actual parameter reference column")
                                exit()
                            self.sigmaplus.append( read_value(field,value) * self.reference[-1] / 100 )
                            self.sigmaminus.append( read_value(field,value) * self.reference[-1] / 100 )
                        elif field == self.parameter+"%+":
                            if not self.reference:
                                print (error(self.depths[-1]) + " the relative uncertainty column must be after the actual parameter reference column")
                                exit()
                            self.sigmaplus.append( read_value(field,value) * self.reference[-1] / 100 )
                        elif field == self.parameter+"%-":
                            if not self.reference:
                                print (error(self.depths[-1]) + " the relative uncertainty column must be after the actual parameter reference column")
                                exit()
                            self.sigmaminus.append( read_value(field,value) * self.reference[-1] / 100 )
                        elif field == "Type":
                            if value is not None: self.gn.assign_gn(value, len(self.depth))


        if self.name is not None: print ("Using " + highlight(self.name) + " as a pressure-depth dependency model")

        column.depths = np.asarray(column.depths)
        column.pressures  = np.asarray(column.pressures)


class pressuredepth:
    def __init__(self,filename):
        self.filename = filename
        self.name = None
        self.citation = None
        self.depths = []
        self.pressures = []

    def read_pressure_model(self):
        print ("Reading Pressure-Depth parametrisation from " + self.filename)

        if not os.path.isfile(self.filename):
            print (error() + "input file " +self.filename+" does not exist!")
            exit()

        with open (self.filename, 'r') as myfile:

            header = True
            columns = []

            for line in myfile:

                # skip empty lines and comments
                if len(line.strip()) == 0: continue
                char = line.strip()[0]
                if char == "#" or char == "!" or char == "/" or char == "%": continue

                tmp = line.strip().split()

                if header:

                    if tmp[0] == "Name":
                        self.name = tmp[1]
                        print ("Using " + highlight(self.name) + " as a pressure-depth dependency model")

                    elif tmp[0] == "Citation":
                        self.citation = tmp[1]

                    elif tmp[0] == "Depth":
                        columns = tmp
                        header = False

                else:

                    # read the actual data table
                    for field, value in zip (columns, tmp):
                        if field == "Depth":
                            self.depths.append( read_value(field,value) )
                        elif field == "Pressure":
                            self.pressures.append( read_value(field,value) )

        self.depths = np.asarray(self.depths)
        self.pressures  = np.asarray(self.pressures)


    def pressure_to_depth(self, pressures):

        p_arr = np.asarray(pressures)

        d_arr = np.zeros_like(p_arr)

        for i in range (p_arr.size):
            d_arr[i] = linear_interp(p_arr[i], self.pressures, self.depths)

        # return scalar if there is only one value
        if d_arr.size = 1: d_arr = d_arr[0]

        return d_arr


