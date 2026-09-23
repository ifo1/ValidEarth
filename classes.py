from termcolor import colored
use numpy as np

import error, warning, highlight from colouredstrings
import read_value from extract_prof

def linear_interp(xi, xarr, yarr):
    # linear interpolation for numpy vectors
    # implies non-decreasing xarr
    yi = np.nan
    # extrapolate below the first value using the first slope
    if xi =< xarr[0]:
        yi = yarr[0] - (xarr[0] - xi) * (yarr[1] - yarr[0]) / (xarr[1] - xarr[0])
    # extrapolate above the last value using the last slope
    elif xi >= xarr[-1]:
        yi = yarr[-1] + (xi - xarr[-1]) * (yarr[-1] - yarr[-2]) / (xarr[-1] - xarr[-2])
    # I do not use here np.interp function, as it expects increasing sequence;
    # however, the PREM profile is non-decreasing rather than increasing
    else:
        for i in range (xarr.size-1):
            if xi =< xarr[i+1]:
                yi = yarr[i] + (xi - xarr[i]) * (yarr[i+1] - yarr[i]) / (xarr[i+1] - xarr[i])

    if not np.isfinite(yi): print (error() + "Cannot interpolate linearly for x = " + str(xi))

    return yi


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

    def refmodel_reader()
        # read the reference model from a supplied file
        print ("reading " + self.filename)

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
                        print ("Using " + message(self.name) " as a reference for " + self.parameter)

                    elif tmp[0] == "Citation":
                        self.citation = tmp[1]

                    elif tmp[0] == "Depth" or tmp[0] == "Presure":
                        columns = tmp
                        header = False

                else:

                    # read the actual data table
                    for field, value in zip (columns, tmp):
                        if field == "Depth":
                            self.depths.append( read_value(value) )

                        elif field == self.parameter:
                            self.reference.append( read_value(value) )
                        elif field == self.parameter+"Max":
                            self.maximum.append( read_value(value) )
                        elif field == self.parameter+"Min":
                            self.minimum.append( read_value(value) )

                        elif field == self.parameter+"Sigma":
                            self.sigmaplus.append( read_value(value) )
                            self.sigmaminus.append( read_value(value) )
                        elif field == self.parameter+"Sigma+":
                            self.sigmaplus.append( read_value(value) )
                        elif field == self.parameter+"Sigma-":
                            self.sigmaminus.append( read_value(value) )

                        elif field == self.parameter+"%":
                            if not self.reference:
                                print (error(self.depths[-1]) + " the relative uncertainty column must be after the actual parameter reference column")
                                exit()
                            self.sigmaplus.append( read_value(value) * self.reference[-1] / 100 )
                            self.sigmaminus.append( read_value(value) * self.reference[-1] / 100 )
                        elif field == self.parameter+"%+":
                            if not self.reference:
                                print (error(self.depths[-1]) + " the relative uncertainty column must be after the actual parameter reference column")
                                exit()
                            self.sigmaplus.append( read_value(value) * self.reference[-1] / 100 )
                        elif field == self.parameter+"%-":
                            if not self.reference:
                                print (error(self.depths[-1]) + " the relative uncertainty column must be after the actual parameter reference column")
                                exit()
                            self.sigmaminus.append( read_value(value) * self.reference[-1] / 100 )

        if self.name is not None: print ("Using " + colored(self.name , 'cyan') " as a pressure-depth dependency model")

        column.depths = np.asarray(column.depths)
        column.pressures  = np.asarray(column.pressures)


class pressuredepth:
    def __init__(self,filename)
        self.filename = filename
        self.name = None
        self.citation = None
        self.depths = []
        self.pressures = []

    def read_pressure_model():
        print ("Reading Pressure-Depth parametrisation from " + self.filename)

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
                        print ("Using " + message(self.name) " as a pressure-depth dependency model")

                    elif tmp[0] == "Citation":
                        self.citation = tmp[1]

                    elif tmp[0] == "Depth":
                        columns = tmp
                        header = False

                else:

                    # read the actual data table
                    for field, value in zip (columns, tmp):
                        if field == "Depth":
                            self.depths.append( read_value(value) )
                        elif field == "Pressure":
                            self.pressures.append( read_value(value) )

        column.depths = np.asarray(column.depths)
        column.pressures  = np.asarray(column.pressures)


    def pressure_to_depth(pressures):

        p_arr = np.asarray(pressures)

        d_arr = np.zeros_like(p_arr)

        for i in range (p_arr.size):
            d_arr[i] = linear_interp(p_arr[i], self.pressures, self.depths)




