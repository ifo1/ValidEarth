import numpy as np
from colouredstrings import error, warning, highlight, red, yellow, green

# velocity assesment constants

# the maximum difference between the supplied Vp/Vs ratio and the actually computed one
eps_vpvs = 0.01 
eps_mgnum = 0.1

# everything over this Vp/Vs value is considered sediments (if not provided in the input file)
sed_vpvs = 2.0
# everything below this Vp/Vs value is considered quartzite (if not provided in the input file)
qtz_vpvs = 1.6
# the maximum thickness of sediments (rocks with Vp/Vs over 2)
sed_maxthick = 5000
# threshold values for the Moho/mantle
mantle_density = 3300
mantle_vp = 7700
mantle_vs = 4200


def check_layers(column, allowqtz, maxsedthick, allowuhp, allowsalt):
    # this function checks the column structure and uses some simplistic thresholds to find out the depths of main divisions
    n = len(column.depth)

    print ("Checking layer structure")

    sediments = -1
    mantle = False

    for i in range(n-1):
        # check the depths are ok
        if column.depth[i] < -9000:
            print (error(column.depth[i]) + "the depth cannot be less than -9000 (exceeding the highest mountain on the Earth); probably, -depthneg flag might help")
            exit()

        # check some basic units
        if column.density is not None and column.density[i] < 10:
            print (error(column.depth[i]) + "the density is less than 10 kg/m3; probably, the units are wrong - kg/m3 expected. Check the -udens flag")
            exit()
        if column.Vp is not None and column.Vp[i] < 10:
            print (error(column.depth[i]) + "the Vp is less than 10 m/sec; probably, the units are wrong - kg/m3 expected. Check the -uvp flag")
            exit()

        # water
        if column.Vs is not None:
            if column.Vs[i] < 0.01 and column.Vs[i+1] > 0.01:
                print ("A layer of " + highlight("water") + " detected using Vs=0 with bottom depth of " + highlight(column.depth[i]) + " m")
                column.gn.assign_gn("water", i)
                continue
            elif column.Vs[i] < 0.01:
                continue

        # sediments
        if isinstance(column.VpVs,np.ndarray):
            if column.VpVs[i] > sed_vpvs and column.VpVs[i+1] < sed_vpvs:
                print ("A layer of " + highlight("sediments") + " detected using high Vp/Vs ratio with bedding depth of " + highlight(column.depth[i]) + " m")
                sediments = i
            elif column.VpVs[i] > sed_vpvs and column.depth[i] > max(maxsedthick,sed_maxthick):
                print (error(column.depth[i]) + "The thickness of " + highlight("sediments") + " exceeds the maximum allowed one of " + str(max(maxsedthick,sed_maxthick)) + " m")
                print ("To allow thicker sedimentary deposits, check the -allowthicksed command line option.")
                exit()
            elif column.VpVs[i] < qtz_vpvs:
                if allowqtz:
                    if column.VpVs[i] < 1.4:
                        print (error(column.depth[i]) + "the " + highlight("Vp/Vs") + " ratio is less than ")
                        exit ()
                    else:
                        print (warning(column.depth[i]) + "the " + highlight("Vp/Vs") + " ratio of " + str(column.VpVs[i]) + " is less than "+str(qtz_vpvs))
                else:
                    print (error(column.depth[i]) + "the " + highlight("Vp/Vs") + " ratio of " + str(column.VpVs[i]) + " is less than " + str(qtz_vpvs) + " and can only be explained by quartzites (alpha-quartz).")
                    print ("To allow quartzite, check the -allowqtz command line option.")
                    exit ()

        # check density inversions in the crust
        # TODO: check what's going on in the mantle
        if isinstance(column.density,np.ndarray) and not mantle:
            # check whether there is a negative density contrast with a reasonable threshold
            diff = column.density[i+1] - column.density[i]
            if diff < -25:
                if diff > -150 and allowuhp and column.depth[i+1] > max(maxsedthick,sed_maxthick):
                    print (warning(column.depth[i+1]) + "is " + str(abs(dens)) + " kg/m3 lighter than the overlying rocks")
                elif column.density[i+1] > 2000 and allowsalt and column.depth[i+1] < max(maxsedthick,sed_maxthick):
                    print (warning(column.depth[i+1]) + "a potential salt layer starts")
                else:
                    print (error(column.depth[i+1]) + "a negative density contrast is detected! Check -allowsalt, -allowuhp, and -allowthicksed options")
                    exit()

        # Moho - all these conditions must be met!
        if isinstance(column.density,np.ndarray):
            if column.density[i] < mantle_density and column.density[i+1] > mantle_density:
                print ("The " + highlight("Moho") + " detected using density contrast right beneath " + highlight(column.depth[i]) + " m")
                column.gn.assign_gn("moho", i)
                if mantle:
                    print (error() + "The mantle has already been detected using Vs!")
                    exit()
                else:
                    mantle = True

        if isinstance(column.Vs,np.ndarray):
            if column.Vs[i] < mantle_vs and column.Vs[i+1] > mantle_vs:
                print ("The " + highlight("Moho") + " detected using Vs contrast right beneath " + highlight(column.depth[i]) + " m")
                column.gn.assign_gn("moho", i)
                if not mantle:
                    print (error() + "The crustal-mantle transition has no density contrast!")
                    exit()
                else:
                    mantle = True

        if isinstance(column.Vp,np.ndarray):
            if column.Vp[i] < mantle_vp and column.Vp[i+1] > mantle_vp:
                print ("The " + highlight("Moho") + " detected using Vp contrast right beneath " + highlight(column.depth[i]) + " m")
                column.gn.assign_gn("moho", i)
                if not mantle:
                    print (error() + "The crustal-mantle transition has no density and Vs contrast!")
                    exit()
                else:
                    mantle = True

    # try to assign sediments after the deepest layer with sedimentary properties was identified
    column.gn.assign_gn("sediments", sediments )


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

    print ("Checking layer boundaries")

    #if there is no water, it is a continent
    geosetting = "continental"
    # the depth of water body
    waterdepth = 0
    if column.gn.water >= 0:
        waterdepth = column.depth[column.gn.water]
        for region in water_depths:
            if waterdepth <= region["depth"]:
                print ("According to the water body depth of " + str(waterdepth) + " m, the region is " + region["colour"](region["setting"]))
                geosetting = region["setting"].split(' ', 1)[0]
                break
        else:
            print (error() + "The depth of water layer (" + str(waterdepth) + " m) exceeds the plausible range")
            exit()

    # check the thickness of sediments
    if column.gn.crust_sediment >= 0:
        sed_thickness = column.depth[column.gn.crust_sediment] - waterdepth
        if sed_thickness > sed_maxthick:
            # if it was an error, it was already suppressed
            print (warning() + "the thickness of sedimentary layer exceeds the maximum expected value: " + str(sed_thickness) + " vs " + str(sed_maxthick) + " m")

    # Moho depth
    if column.gn.crust_lower >= 0:
        thickness = column.depth[column.gn.crust_lower] - waterdepth
        if thickness < 0:
            print (error() + "the total crustal thickness is negative - check whether the -depthneg flag is required")
            exit()

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
        if thickness < 0:
            print (error() + "the total lithospheric thickness is negative - check whether the -depthneg flag is required")
            exit()

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
    n = column.depth.size

    Vpadded = False
    Vsadded = False
    VpVsadded = False

    # allocate arrays if necessary
    if column.Vp.size == 0:
        column.Vp = np.empty((n))
        column.Vp[:] = np.nan
        Vpadded = True
    if column.Vs.size == 0:
        column.Vs = np.empty((n))
        column.Vs[:] = np.nan
        Vsadded = True
    if column.VpVs.size == 0:
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
            column.Vp = None

    if Vsadded:
        if np.any (np.isfinite(column.Vs)):
            print (highlight("Vs was computed automatically"))
            column.columns.append("Vs")
        else:
            column.Vs = None

    if VpVsadded:

        if np.any (np.isfinite(column.VpVs)):
            print (highlight("Vp/Vs was computed automatically"))
            column.columns.append("VpVs")
        else:
            column.VpVs = None

    # check physical boundary
    if isinstance(column.VpVs,np.ndarray):
        for i in range(column.VpVs.size):
            if np.isfinite(column.VpVs[i]):
                if column.VpVs[i] < 1.333:
                    print (error() + "the Vp/Vs ratio is less than 4/3!")
                    exit()


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
    n = column.depth.size

    MgNumadded = False
    MgOadded = False
    FeOadded = False

    # allocate arrays if necessary
    if column.MgNum.size == 0:
        column.MgNum = np.empty((n))
        column.MgNum[:] = np.nan
        MgNumadded = True
    if column.MgO.size == 0:
        column.MgO = np.empty((n))
        column.MgO[:] = np.nan
        MgOadded = True
    if column.FeO.size == 0:
        column.FeO = np.empty((n))
        column.FeO[:] = np.nan
        FeOadded = True

    # compute FeO, MgO, and MgNum if one of the values is missing

    for i in range (n):

        if np.isfinite(column.MgNum[i]):

            if np.isfinite(column.MgO[i]) and np.isfinite(column.FeO[i]):
                eps = abs( column.MgNum[i] - MgFe2MgNum (column.MgO[i], column.FeO[i]) )
                if eps > eps_mgnum:
                    print (error(column.depth[i]) + "The following MgO, FeO, Mg# values are inconsistent: " + str(column.MgO[i]) + " / " + str(column.FeO[i]) + " ≠ " + str(column.MgNum[i]))

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
            column.MgNum = None

    if MgOadded:
        if np.any (np.isfinite(column.MgO)):
            print (highlight("MgO was computed automatically"))
            column.columns.append("MgO")
        else:
            column.MgO = None

    if FeOadded:
        if np.any (np.isfinite(column.FeO)):
            print (highlight("FeO was computed automatically"))
            column.columns.append("FeO")
        else:
            column.FeO = None

