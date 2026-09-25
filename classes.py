from termcolor import colored
import numpy as np
import os.path
import math

from colouredstrings import error, warning, highlight, red, yellow, green
from datachecks import read_value


def linear_interp(xi, xarrin, yarrin):
    # linear interpolation for numpy vectors
    # implies non-decreasing xarr

    # remove all non-finite vales
    xarr = xarrin[np.isfinite(yarrin)]
    yarr = yarrin[np.isfinite(xarrin)]

    #if there are no values left, leave
    if xarr.size == 0: return np.nan

    #if there is only one value for this layer, return it
    if xarr.size == 1: return yarr[0]

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
                break

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
    # negative indices as the first layer starts immediately, and it is the bottom of non-existent layer
    layermodel = [-1]
    layerref   = [-1]

    if model_nlay <= 0:
        print (error() + "the input data file contains no records")
        exit()

    if ref_nlay <= 0:
        print (error() + "the reference file contains no records")
        exit()

    if model_ind.water >= 0 and ref_ind.water >= 0:
        layernames.append("Water")
        layermodel.append(model_ind.water)
        layerref.append(ref_ind.water)

    if model_ind.crust_soil >= 0 and ref_ind.crust_soil >= 0:
        layernames.append("Soil")
        layermodel.append(model_ind.crust_soil)
        layerref.append(ref_ind.crust_soil)

    if model_ind.crust_regolith >= 0 and ref_ind.crust_regolith >= 0:
        layernames.append("Regolith")
        layermodel.append(model_ind.crust_regolith)
        layerref.append(ref_ind.crust_regolith)

    if model_ind.crust_sediment >= 0 and ref_ind.crust_sediment >= 0:
        layernames.append("Sediments")
        layermodel.append(model_ind.crust_sediment)
        layerref.append(ref_ind.crust_sediment)

    if model_ind.crust_upper >= 0 and ref_ind.crust_upper >= 0:
        layernames.append("Upper Crust")
        layermodel.append(model_ind.crust_upper)
        layerref.append(ref_ind.crust_upper)

    if model_ind.crust_middle >= 0 and ref_ind.crust_middle >= 0:
        layernames.append("Middle Crust")
        layermodel.append(model_ind.crust_middle)
        layerref.append(ref_ind.crust_middle)

    if model_ind.crust_lower >= 0 and ref_ind.crust_lower >= 0:
        layernames.append("Lower Crust")
        layermodel.append(model_ind.crust_lower)
        layerref.append(ref_ind.crust_lower)

    if model_ind.mantle_litho >= 0 and ref_ind.mantle_litho >= 0:
        layernames.append("Lithospheric Mantle")
        layermodel.append(model_ind.mantle_litho)
        layerref.append(ref_ind.mantle_litho)

    if model_ind.mantle_sublitho >= 0 and ref_ind.mantle_sublitho >= 0:
        layernames.append("Sublithospheric Mantle")
        layermodel.append(model_ind.mantle_sublitho)
        layerref.append(ref_ind.mantle_sublitho)

    if model_ind.mantle_mtz >= 0 and ref_ind.mantle_mtz >= 0:
        layernames.append("Mantle Transition Zone")
        layermodel.append(model_ind.mantle_mtz)
        layerref.append(ref_ind.mantle_mtz)

    if model_ind.mantle_lower >= 0 and ref_ind.mantle_lower >= 0:
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


def print_stacked_models(layernames, layermodel, layerref, depthmodel, depthref, mindifabs, mindifrel, maxdifrel, maxdifabs, use_stdev):
    # a function to print out a "composite cross-section" from the reference and the input models being stacked
    # Inputs
    # layernames - a list of layer names in the composite cross-section
    # layermodel - a list of matching layer indices for the input model
    # layerref   - a list of matching layer indices for the reference model 
    # depthmodel - a list of matching layer depths for the input model
    # depthref   - a list of matching layer depths for the reference model 

    if use_stdev:
        print ("       Input Model          -      Layer Name      -       Reference model       - Below Reference - Above Reference")
        print ("Layer index - Bedding depth -                      - Bedding depth - Layer index -  StDev  -  Abs  -  StDev  -  Abs")
        yellowlevel = 3 # 3 sigma
        redlevel    = 4 # 4 sigma
    else:
        print ("       Input Model          -      Layer Name      -       Reference model       -  Below Minimum  -  Above Maximum")
        print ("Layer index - Bedding depth -                      - Bedding depth - Layer index -   Rel   -  Abs  -   Rel   -  Abs")
        yellowlevel = 0.05 #  5% of the range 
        redlevel    = 0.1  # 10% of the range
    im1 = 0
    ir1 = 0
    for name, im, ir, minabs, minrel, maxrel, maxabs in zip (layernames, layermodel[1:], layerref[1:], mindifabs, mindifrel, maxdifrel, maxdifabs):
        text = '       {:4d}'.format(im) + ' - {:11.2f} m'.format(depthmodel[im]) + " - " 
        text += name.center(20)
        text += (' - {:11.2f} m'.format(depthref[ir]) + ' - {:4d}'.format(ir)).rjust(20)
        if minrel > redlevel:
            text += '        - ' +    red('{:6.2f}'.format(minrel)) + ' - ' +    red('{:6.1f}'.format(minabs))
        elif minrel > yellowlevel:
            text += '        - ' + yellow('{:6.2f}'.format(minrel)) + ' - ' + yellow('{:6.1f}'.format(minabs))
        else:
            text += '        - ' +  green('{:6.2f}'.format(minrel)) + ' - ' +  green('{:6.1f}'.format(minabs))
        if maxrel > redlevel:
            text += ' -  ' +    red('{:6.2f}'.format(maxrel)) + ' -' +    red('{:7.1f}'.format(maxabs))
        elif maxrel > yellowlevel:
            text += ' -  ' + yellow('{:6.2f}'.format(maxrel)) + ' -' + yellow('{:7.1f}'.format(maxabs))
        else:
            text += ' -  ' +  green('{:6.2f}'.format(maxrel)) + ' -' +  green('{:7.1f}'.format(maxabs))

        print (text)


def validate_profile_stdev(refmodel, layerref, dataval, datadepths, layermodel, verbose = False):
    # a function to print out a "composite cross-section" from the reference and the input models being stacked
    # Inputs
    # refmodel   - the reference model
    # layerref   - indices of layers in the reference model
    # dataval    - the input model data
    # datadepths - the input model layer bedding depths
    # layermodel - indices of layers in the input model data
    # verbose    - whether to print out a detailed comparison
    # Outputs (lists, one entry per each layer)
    # negdifabs - the maximum negative difference (absolute) between the reference and the model
    # mindifrel - the maximum negative difference (relative) between the reference and the model
    # maxdifrel - the maximum positive difference (relative) between the reference and the model
    # maxdifabs - the maximum positive difference (absolute) between the reference and the model

    mindifabs = []
    mindifrel = []
    maxdifrel = []
    maxdifabs = []

    if len(layerref) != len(layermodel):
        print (error() + "the number of matched layers in the reference and input models are not equal")
        exit()

    im1 = layermodel[0]
    ir1 = layerref[0]
    if verbose:
        print ("Printing full comparison for " + refmodel.parameter + " using " + refmodel.name + " as reference")
        print ("Layer#   -   Depth  -  Value    - Reference -   StDev   - Difference")

    for im, ir in zip (layermodel[1:], layerref[1:]):
        # inspecting every single layer from the stacked model

        datadepthsubset = datadepths[im1+1:im+1]
        datavalsubset   = dataval[im1+1:im+1]

        refdepthsubset  = refmodel.depths[ir1+1:ir+1]
        refvalsubset    = refmodel.reference[ir1+1:ir+1]
        sminussubset    = refmodel.sigmaminus[ir1+1:ir+1]
        splussubset     = refmodel.sigmaplus[ir1+1:ir+1]

        mindifabsloc = 0.0
        mindifrelloc = 0.0
        maxdifrelloc = 0.0
        maxdifabsloc = 0.0

        for i in range(datavalsubset.size):
            # inspecting data points within a single layer of the input model

            refinterp = linear_interp(datadepthsubset[i], refdepthsubset, refvalsubset)
            if not np.isfinite(refinterp): continue
            # reference - input model
            diff = refinterp - datavalsubset[i]

            if diff < 0:
                sigma = linear_interp(datadepthsubset[i], refdepthsubset, sminussubset)
                if not np.isfinite(sigma): continue
                mindifabsloc = max(mindifabsloc, -diff)
                mindifrelloc = max(mindifrelloc, -diff / sigma)
            else:
                sigma = linear_interp(datadepthsubset[i], refdepthsubset, splussubset)
                if not np.isfinite(sigma): continue
                maxdifabsloc = max(maxdifabsloc, diff)
                maxdifrelloc = max(maxdifrelloc, diff / sigma)

            if verbose: 
                print ('{:4d}'.format(im1+1+i) + ' - {:11.2f} '.format(datadepthsubset[i]) + \
                    ' - {:8.2f} '.format(datavalsubset[i]) + ' - {:8.2f} '.format(refinterp) + \
                    ' - {:8.2f} '.format(sigma) + ' - {:8.2f} '.format(diff))


        mindifabs.append(mindifabsloc)
        mindifrel.append(mindifrelloc)
        maxdifabs.append(maxdifabsloc)
        maxdifrel.append(maxdifrelloc)

        im1 = im
        ir1 = ir

    return mindifabs, mindifrel, maxdifrel, maxdifabs


def validate_profile_minmax(refmodel, layerref, dataval, datadepths, layermodel):
    # a function to print out a "composite cross-section" from the reference and the input models being stacked
    # Inputs
    # refmodel   - the reference model
    # layerref   - indices of layers in the reference model
    # dataval    - the input model data
    # datadepths - the input model layer bedding depths
    # layermodel - indices of layers in the input model data
    # Outputs (lists, one entry per each layer)
    # negdifabs - the maximum negative difference (absolute) between the reference and the model
    # mindifrel - the maximum negative difference (relative) between the reference and the model
    # maxdifrel - the maximum positive difference (relative) between the reference and the model
    # maxdifabs - the maximum positive difference (absolute) between the reference and the model

    mindifabs = []
    mindifrel = []
    maxdifrel = []
    maxdifabs = []

    if len(layerref) != len(layermodel):
        print (error() + "the number of matched layers in the reference and input models are not equal")
        exit()

    im1 = layermodel[0]
    ir1 = layerref[0]
    for im, ir in zip (layermodel[1:], layerref[1:]):
        # inspecting every single layer from the stacked model

        datadepthsubset = datadepths[im1+1:im+1]
        datavalsubset   = dataval[im1+1:im+1]

        refdepthsubset  = refmodel.depths[ir1+1:ir+1]
        minimumsubset   = refmodel.minimum[ir1+1:ir+1]
        maximumsubset   = refmodel.maximum[ir1+1:ir+1]

        mindifabsloc = 0.0
        mindifrelloc = 0.0
        maxdifrelloc = 0.0
        maxdifabsloc = 0.0

        for i in range(datavalsubset.size):
            # inspecting data points within a single layer of the input model

            minloc = linear_interp(datadepthsubset[i], refdepthsubset, minimumsubset)
            maxloc = linear_interp(datadepthsubset[i], refdepthsubset, maximumsubset)
            if not np.isfinite(minloc) or not np.isfinite(maxloc): continue
            sigma = maxloc - minloc
            # reference minimum - input model
            diff = minloc - datavalsubset[i]
            if diff > 0:
                mindifabsloc = max(mindifabsloc, diff)
                mindifrelloc = max(mindifrelloc, diff / sigma)

            # input model - reference maximum
            diff = datavalsubset[i] - maxloc
            if diff > 0:
                maxdifabsloc = max(maxdifabsloc, diff)
                maxdifrelloc = max(maxdifrelloc, diff / sigma)

        mindifabs.append(mindifabsloc)
        mindifrel.append(mindifrelloc)
        maxdifabs.append(maxdifabsloc)
        maxdifrel.append(maxdifrelloc)

        im1 = im
        ir1 = ir

    return mindifabs, mindifrel, maxdifrel, maxdifabs


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

    def assign_gn(self, tag, ni):
        # assign the provided tag index to a corresponding variable 
        value = tag.lower()
        n = ni
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
            case "cmb":
                self.mantle_lower = n
            case default:
                print (warning() + "type " + value + " is not known")

    def report_gn(self, depth):
        if self.water >= 0 or self.crust_soil >= 0 or self.crust_regolith >= 0 or self.crust_sediment >= 0 or \
            self.crust_upper >= 0 or self.crust_middle >= 0 or self.crust_lower >= 0 or \
            self.mantle_litho >= 0 or self.mantle_sublitho >= 0 or self.mantle_mtz >= 0 or self.mantle_lower >= 0:
            print ("The following golden nails are used")
        if self.water >= 0:           print (" - Water layer ends at depth " + str(depth[self.water]) + " (record #" + str(self.water+1) + ")")
        if self.crust_soil >= 0:      print (" - Soil layer ends at depth " + str(depth[self.crust_soil]) + " (record #" + str(self.crust_soil+1) + ")")
        if self.crust_regolith >= 0:  print (" - Regolith layer ends at depth " + str(depth[self.crust_regolith]) + " (record #" + str(self.crust_regolith+1) + ")")
        if self.crust_sediment >= 0:  print (" - Sedimentary layer ends at depth " + str(depth[self.crust_sediment]) + " (record #" + str(self.crust_sediment+1) + ")")
        if self.crust_upper >= 0:     print (" - Upper crust ends at depth " + str(depth[self.crust_upper]) + " (record #" + str(self.crust_upper+1) + ")")
        if self.crust_middle >= 0:    print (" - Middle crust ends at depth " + str(depth[self.crust_middle]) + " (record #" + str(self.crust_middle+1) + ")")
        if self.crust_lower >= 0:     print (" - Lower crust ends at depth " + str(depth[self.crust_lower]) + " (record #" + str(self.crust_lower+1) + ")")
        if self.mantle_litho >= 0:    print (" - Lithospheric mantle ends at depth " + str(depth[self.mantle_litho]) + " (record #" + str(self.mantle_litho+1) + ")")
        if self.mantle_sublitho >= 0: print (" - Sublithospheric mantle ends at depth " + str(depth[self.mantle_sublitho]) + " (record #" + str(self.mantle_sublitho+1) + ")")
        if self.mantle_mtz >= 0:      print (" - Mantle Transition zone ends at depth " + str(depth[self.mantle_mtz]) + " (record #" + str(self.mantle_mtz+1) + ")")
        if self.mantle_lower >= 0:    print (" - Lower mantle ends at depth " + str(depth[self.mantle_lower]) + " (record #" + str(self.mantle_lower+1) + ")")


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
        self.coordsys  = "Geographic"
        self.longitude = None
        self.latitude  = None
        self.x = None
        self.y  = None
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
                        print ("Using " + highlight(self.name) + " as a reference model for " + self.parameter)

                    elif tmp[0] == "Citation":
                        self.citation = tmp[1]

                    elif tmp[0] == "Depth" or tmp[0] == "Presure":
                        columns = tmp
                        header = False
                        if columns[-1] != "Type":
                            columns.append("Type")

                    elif tmp[0] == "CoordinateSystem":
                        self.coordsys = tmp[1]

                    elif tmp[0] == "Longitude":
                        self.longitude = float(tmp[1])
                    elif tmp[0] == "Latitude":
                        self.latitude = float(tmp[1])

                    elif tmp[0] == "X":
                        self.x = float(tmp[1])
                    elif tmp[0] == "Y":
                        self.y = float(tmp[1])

                else:
                    # pad the Type column with None
                    if len(tmp) == len(columns)-1:
                        tmp.append(None)

                    if len(tmp) != len(columns):
                        print (error() + "the number of columns in the reference model file is not uniform!")
                        exit()

                    # read the actual data table
                    for field, value in zip (columns, tmp):
                        if field == "Depth":
                            locdepth = read_value(field,value)
                            if len(self.depths) >= 1:
                                if locdepth < self.depths[-1]:
                                    print (error(locdepth) + "the depth is not non-decreasing in the reference file!")
                                    exit()
                            self.depths.append( locdepth )
                        elif field == self.parameter:
                            self.reference.append( read_value(field,value) )
                        elif field == self.parameter+"Max":
                            self.maximum.append( read_value(field,value) )
                        elif field == self.parameter+"Min":
                            self.minimum.append( read_value(field,value) )

                        elif field == self.parameter+"Stdev":
                            self.sigmaplus.append( read_value(field,value) )
                            self.sigmaminus.append( read_value(field,value) )
                        elif field == self.parameter+"Stdev+":
                            self.sigmaplus.append( read_value(field,value) )
                        elif field == self.parameter+"Stdev-":
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
                            if value is not None:
                                self.gn.assign_gn(value, len(self.depths)-1)

        self.depths = np.asarray(self.depths)

        if not self.reference:
            if not self.maximum and not self.minimum:
                print ("The field was not found; skipping")
                return False
            # min and max values
            self.maximum = np.asarray(self.maximum)
            self.minimum = np.asarray(self.minimum)
            self.sigmaplus = None
            self.sigmaminus = None
            self.reference = None
        else:
            # mean and stdevs
            self.reference = np.asarray(self.reference)
            if not self.sigmaplus and not self.sigmaminus:
                # sigma = 1%, but not less than unity to avoid division by zero
                self.sigmaplus = np.maximum(100., self.reference) / 100.0
                self.sigmaminus = self.sigmaplus
            else:            
                self.sigmaplus = np.asarray(self.sigmaplus)
                self.sigmaminus = np.asarray(self.sigmaminus)
            self.maximum = None
            self.minimum = None

        return True



class pressuredepth:
    def __init__(self,filename):
        self.filename = filename
        self.name = None
        self.citation = []
        self.depths = []
        self.pressures = []

    def read_pressure_model(self):
        print ("Reading Pressure-Depth parameterisation from " + self.filename)

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
                        self.citation.append(tmp[1])

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
        if d_arr.size == 1: d_arr = d_arr[0]

        return d_arr


