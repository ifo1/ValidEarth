import numpy as np
from colouredstrings import error, warning, highlight, red, yellow, green

# velocity assesment constants

# the maximum difference between the supplied Vp/Vs ratio and the actually computed one
eps_vpvs = 0.01 
eps_mgnum = 0.1

# everything over this Vp/Vs value is considered sediments (if not provided in the input file)
sed_vpvs = 2.0
# threshold values for the Moho
mantle_density = 3300
mantle_vp = 7700
mantle_vs = 4200


def check_layers(column):
    # this function checks the column structure and uses some simplistic thresholds to find out the depths of main dvisions
    n = len(column.depth)

    print ("Checking layer structure")

    mantle = False

    for i in range(n-1):
        # water
        if column.Vs:
            if column.Vs[i] is not None and column.Vs[i+1] is not None:
                if column.Vs[i] < 0.01 and column.Vs[i+1] > 0.01:
                    print ("A layer of " + highlight("water") + " detected using Vs=0 with bottom depth of " + highlight(column.depth[i]) + " m")
                    column.gn.assign_gn("water", i)
                    continue
                elif column.Vs[i] < 0.01:
                    continue

        # sediments
        if column.Vs and column.Vp:
            if column.Vs[i] is not None and column.Vp[i] is not None and column.Vs[i+1] is not None and column.Vp[i+1] is not None:
                if column.Vp[i]/column.Vs[i] > sed_vpvs and column.Vp[i+1]/column.Vs[i+1] < sed_vpvs:
                    column.gn.assign_gn("sediments", i)
                    print ("A layer of " + highlight("sediments") + " detected using high Vp/Vs ratio with bedding depth of " + highlight(column.depth[i]) + " m")

        # Moho
        if column.density:
            if column.density[i] is not None and column.density[i+1] is not None:
                if column.density[i] < mantle_density and column.density[i+1] > mantle_density:
                    column.gn.assign_gn("moho", i)
                    print ("The " + highlight("Moho") + " detected using density contrast right beneath " + highlight(column.depth[i]) + " m")
                    mantle = True
        elif column.Vs:
            if column.Vs[i] is not None and column.Vs[i+1] is not None:
                if column.Vs[i] < mantle_vs and column.Vs[i+1] > mantle_vs:
                    column.gn.assign_gn("moho", i)
                    print ("The " + highlight("Moho") + " detected using Vs contrast right beneath " + highlight(column.depth[i]) + " m")
                    mantle = True
        elif column.Vs:
            if column.Vp[i] is not None and column.Vp[i+1] is not None:
                if column.Vp[i] < mantle_vp and column.Vp[i+1] > mantle_vp:
                    column.gn.assign_gn("moho", i)
                    print ("The " + highlight("Moho") + " detected using Vp contrast right beneath " + highlight(column.depth[i]) + " m")
                    mantle = True


# water depth level ranges
water_depths = [{"depth" :     0, "setting": "continental crust", "colour": green  }, 
                {"depth" :   200, "setting": "continental shelf", "colour": green  }, 
                {"depth" :  2500, "setting": "continental slope", "colour": yellow }, 
                {"depth" :  6000, "setting": "oceanic crust",     "colour": red    }, 
                {"depth" : 11000, "setting": "oceanic trench",    "colour": red    }]
# Crustal thickness for different lithospheres
crust_thick  = [{"type" :   "oceanic", "region": "too thin for ocean",        "depth":  4000, "colour": red },
                {"type" :   "oceanic", "region": "seafloor",                  "depth": 10000, "colour": green }, 
                {"type" :   "oceanic", "region": "seamounts / slow spearing", "depth": 20000, "colour": yellow }, 
                {"type" :   "oceanic", "region": "hot spots only!",           "depth": 30000, "colour": red },
                {"type" :   "oceanic", "region": "too thick for ocean",       "depth": 40000, "colour": red },
                {"type" :   "continental", "region": "too thin for continent","depth": 25000, "colour": red }, 
                {"type" :   "continental", "region": "thin continental",      "depth": 30000, "colour": yellow }, 
                {"type" :   "continental", "region": "platform",              "depth": 50000, "colour": green }, 
                {"type" :   "continental", "region": "orogens",               "depth": 70000, "colour": yellow }, 
                {"type" :   "continental", "region": "too thick for orogen",  "depth": 85000, "colour": red } ]
# LAB depth for different settings
LAB_depths   = [{"type" :   "oceanic", "region": "hotspot / too thin for ocean", "depth":  23000, "colour": red },
                {"type" :   "oceanic", "region": "Mid Ocean Ridge",              "depth":  55000, "colour": yellow }, 
                {"type" :   "oceanic", "region": "oceanic lithosphere",          "depth": 155000, "colour": green }, 
                {"type" :   "continental", "region": "too thin for continent",   "depth":  40000, "colour": red }, 
                {"type" :   "continental", "region": "thin continental",         "depth": 115000, "colour": yellow }, 
                {"type" :   "continental", "region": "platform",                 "depth": 160000, "colour": green }, 
                {"type" :   "continental", "region": "craton",                   "depth": 230000, "colour": yellow }]

def check_layer_depth(column):
    # check that the main layer boundaries are within reasonable ranges

    #if there is no water, it is a continent
    geosetting = "continental"
    # the depth of water body
    if column.gn.water >= 0:
        thickness = column.depth[column.gn.water]
        for region in water_depths:
            if thickness <= region["depth"]:
                print ("According to the depth of " + str(thickness) + " m, the region is " + region["colour"](region["setting"]))
                geosetting = region["setting"].split(' ', 1)[0]
                break
        else:
            print (error() + "The depth of water layer (" + str(thickness) + " m) exceeds the plausible range")
            exit()

    # Moho depth
    if column.gn.crust_lower >= 0:

        thickness = column.depth[column.gn.crust_lower]
        if column.gn.water >= 0:
            thickness -= column.depth[column.gn.water]

        for region in crust_thick:
            if geosetting == region["type"] and thickness <= region["depth"]:
                print ("The crust with total thickness " + str(thickness) + " m is identified as " + region["colour"](region["region"]))
                break
        else:
            print (error() + "The crust with total thickness " + str(thickness) + " m exceeds the plausible range")
            exit()

    # LAB depth
    if column.gn.mantle_litho >= 0:

        thickness = column.depth[column.gn.mantle_litho]

        for region in LAB_depths:
            if geosetting == region["type"] and thickness <= region["depth"]:
                print ("The " + geosetting + " lithosphere with total thickness " + str(thickness) + " m is identified as " + region["colour"](region["region"]))
                break
        else:
            print (error() + "The " + geosetting + " lithosphere with total thickness " + str(thickness) + " m exceeds the plausible range")
            exit()


def sanity_checks (column):
    # check the general scopes for data values
    pass


def recompute_vp_vs(column):

    # size of all arrays
    n = len(column.depth)

    Vpadded = False
    Vsadded = False
    VpVsadded = False

    # allocate arrays if necessary
    if not column.Vp:
        column.Vp = np.empty((n))
        column.Vp[:] = np.nan
        Vpadded = True
    if not column.Vs:
        column.Vs = np.empty((n))
        column.Vs[:] = np.nan
        Vsadded = True
    if not column.VpVs:
        column.VpVs = np.empty((n))
        column.VpVs[:] = np.nan
        VpVsadded = True

    # compute Vp, Vs, and Vp/Vs if one of the values is missing

    for i in range (n):

        if np.isfinite(column.VpVs[i]):

            if column.Vs[i] == 0.0 and column.VpVs[i] > 0:
                print (error() + "Vs is zero (liquid), while Vp/Vs is finite " + str(column.VpVs[i]))

            if np.isfinite(column.Vp[i]) and np.isfinite(column.Vs[i]):
                eps = abs( column.VpVs[i] - column.Vp[i] / column.Vs[i])
                if eps > eps_vpvs:
                    print (error(Depth[i]) + "The following Vp, Vs, Vp/Vs values are inconsistent: " + str(column.Vp[i]) + " / " + str(column.Vs[i]) + " ≠ " + str(column.VpVs[i]))

            elif np.isfinite(column.Vp[i]):
                if column.VpVs[i] > 0:
                    column.Vs[i] = column.Vp[i] / column.VpVs[i]

            elif np.isfinite(column.Vs[i]):
                column.Vp[i] = column.Vs[i] * column.VpVs[i]

        else:

            if np.isfinite(column.Vp[i]) and np.isfinite(column.Vs[i]) and column.Vs[i] > 0.0:
                column.VpVs[i] = column.Vp[i] / column.Vs[i]
    
    # check that something was actually added
    if Vpadded:
        if np.any (np.isfinite(column.Vp)):
            print (highlight("Vp was computed automatically"))
            column.columns.append("Vp")
        else:
            column.Vp = []

    if Vsadded:
        if np.any (np.isfinite(column.Vs)):
            print (highlight("Vs was computed automatically"))
            column.columns.append("Vs")
        else:
            column.Vs = []

    if VpVsadded:
        if np.any (np.isfinite(column.VpVs)):
            print (highlight("Vp/Vs was computed automatically"))
            column.columns.append("VpVs")
        else:
            column.VpVs = []


def MgFe2MgNum (MgO, FeO):
    # compute the magnesium number (mol.%) from MgO and FeO, wt%
    return 100 * (MgO/40.305)  / ( (MgO/40.305) + (FeO/71.844))

def MgMgNum2Fe (MgO, MgNum):
    # compute the FeO, wt% from the magnesium number (mol.%) and MgO, wt%
    return MgO * (71.844/40.305) * (100-MgNum) / MgNum

def FeMgNum2Mg (FeO, MgNum):
    # compute the MgO, wt% from the magnesium number (mol.%) and FeO, wt%
    return FeO * (40.305/71.844) * MgNum / (100-MgNum)


def recompute_mgnum(column):

    # size of all arrays
    n = len(column.depth)

    MgNumadded = False
    MgOadded = False
    FeOadded = False

    # allocate arrays if necessary
    if not column.MgNum:
        column.MgNum = np.empty((n))
        column.MgNum[:] = np.nan
        MgNumadded = True
    if not column.MgO:
        column.MgO = np.empty((n))
        column.MgO[:] = np.nan
        MgOadded = True
    if not column.FeO:
        column.FeO = np.empty((n))
        column.FeO[:] = np.nan
        FeOadded = True

    # compute FeO, MgO, and MgNum if one of the values is missing

    for i in range (n):

        if np.isfinite(column.MgNum[i]):

            if np.isfinite(column.MgO[i]) and np.isfinite(column.FeO[i]):
                eps = abs( column.MgNum[i] - MgFe2MgNum (column.MgO[i], column.FeO[i]) )
                if eps > eps_mgnum:
                    print (error(Depth[i]) + "The following MgO, FeO, Mg# values are inconsistent: " + str(column.MgO[i]) + " / " + str(column.FeO[i]) + " ≠ " + str(column.MgNum[i]))

            elif np.isfinite(column.MgO[i]):
                column.FeO[i] = MgMgNum2Fe (column.MgO[i], column.MgNum[i])

            elif np.isfinite(column.FeO[i]):
                column.MgO[i] = FeMgNum2Mg (column.FeO[i], column.MgNum[i])

        else:

            if np.isfinite(column.FeO[i]) and np.isfinite(column.MgO[i]):
                column.MgNum[i] = MgFe2MgNum (column.MgO[i], column.FeO[i])
    
    # check that something was actually added
    if MgNumadded:
        if np.any (np.isfinite(column.MgNum)):
            print (highlight("MgNum was computed automatically"))
            column.columns.append("MgNum")
        else:
            column.MgNum = []

    if MgOadded:
        if np.any (np.isfinite(column.MgO)):
            print (highlight("MgO was computed automatically"))
            column.columns.append("MgO")
        else:
            column.MgO = []

    if FeOadded:
        if np.any (np.isfinite(column.FeO)):
            print (highlight("FeO was computed automatically"))
            column.columns.append("FeO")
        else:
            column.FeO = []

