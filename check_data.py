import numpy as np
from colouredstrings import error, warning, highlight

# velocity assesment constants

# the maximum difference between the supplied Vp/Vs ratio and the actually computed one
eps_vpvs = 0.01 

def is_new_data(array, columns, label):
    return ( label not in columns and isinstance(array,np.ndarray) )


def check_velocities(column):

    # size of all arrays
    n = len(column.depth)

    print(n)
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

    print (np.any (np.isfinite(column.Vs)))

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
        print (np.any (np.isfinite(column.Vs)))
        print (np.any (np.isfinite(column.Vs)))
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


