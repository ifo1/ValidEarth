use numpy as np
import error, warning from colouredstrings

# velocity assesment constants

# the maximum difference between the supplied Vp/Vs ratio and the actually computed one
eps_vpvs = 0.01 



def check_velocities(Depth, Vp, Vs, VpVs, Crust, Mantle):

    #size of all arrays
    n = Depth.size

    # compute Vp, Vs, and Vp/Vs if one of the values is missing

    for i in range (n):

        if np.isfinite(VpVs[i]):

            if Vs[i] == 0.0 and VpVs[i] > 0:
                print (error(Depth[i]) + "Vs is zero (water), while Vp/Vs is finite " + str(VpVs[i]))

            if np.isfinite(Vp[i]) and np.isfinite(Vs[i]):
                eps = abs( VpVs[i] - Vp[i] / Vs[i])
                if eps > eps_vpvs:
                    print (error(Depth[i]) + "The following Vp, Vs, Vp/Vs values are inconsistent: " + str(Vp[i]) + " / " + str(Vs[i]) + " ≠ " + str(VpVs[i]))

            elif np.isfinite(Vp[i]):
                if VpVs[i] > 0:
                    Vs[i] = Vp[i] / VpVs[i]

            elif np.isfinite(Vs[i]):
                Vp[i] = Vs[i] * VpVs[i]

        else:

            if np.isfinite(Vp[i]) and np.isfinite(Vs[i]) and Vs[i] > 0.0:
                VpVs[i] = Vp[i] / Vs[i]


    # check velocities according to the 


    return Vp, Vs, VpVs
