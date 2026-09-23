
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
    def __init__ (self):
        # the actual reference profile expressed in terms of depth or pressure
        self.depth = []
        self.pressure = []
        self.observation = []
        # 1 sigma intervals on the left and on the right hand sides of the actual observation
        self.sigmaplus = []
        self.sigmaminus = []

