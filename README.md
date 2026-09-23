# ValidEarth

ValidEarth is a toolkit for verifying whether vertical profiles of Earth's physical properties are consistent with established reference models. The assessable properties include key parameters such as density, temperature, bulk and shear seismic velocities and their ratio, chemical composition of the mantle. This list can be easily extended using new modules.

For each parameter, ValidEarth comes with a set of well-established reference models based on experimental and seismic data, with all sources documented in the **bibliography**. Each reference data point is associated with an independent relative or absolute uncertainty, allowing the comparison to account for the expected variability and uncertainty of the reference models. The tool reports the differences that are greater than three sigmas; for the parameters with more than reference models provided (for example, geotherms for different geological settings), the tool looks for the best matching profile automatically.

# Input Data Format

A valid input file should contain following sections:

- Optional Keywords and Values
- Column Headers
- Data Table

Optional keywords include Name (an arbitrary string without whitespace), CoordinateSystem (Geographic or Cartesian), Longitude, and Latitude. Each keyword must be on a separate line.

The first Column Header must be **Depth**. It can be followed by any of the following **Headers**:
- **Temperature**, K
- **Vp**, m/sec
- **Vs**, m/sec
- **Density**, kg/m3
- **VpVs** for the Vp/Vs ratio
- **SiO2**, wt.%
- **Al2O3**, wt.%
- **FeO**, wt.%
- **MgO**, wt.%
- **CaO**, wt.%
- **MgNum** or Mg#, mol.%

This line should be followed by a datatable with values to verify. By default, ValidEarth treats (almost) all the physical quantities as being expressed in SI units, unless specified. Some automated unit conversions can be enabled using the command line options.

Notice: the code will automatically compute the mutually depending quantities in case they are not supplied such as Vp/Vs from Vp and Vs, or Vp from Vp/Vs and Vs.

The code also allows specific tags for distinct geological domains (layers). They should appear as the last entry for each data row; an auxilliary word "Type" can be used to mark this column. Currently the code recongnises the following keywords:
- **soil**: for all the layers representing soils
- **regolith**: for all the unconsolidated sediments such as sands, gravels and so on
- **sediments**: consolidated sediments like sandstone, limestone, and so on
- **crustupper**: the upper layer of crystalline crust
- **crustmiddle**: the middle layer of crystalline crust
- **crustlower**: the lower layer of crystalline crust
- **Moho**: an alternative keyword with the same meaning as crustlower
- **mantlelitho**: the lithospheric mantle
- **LAB**: an alternative keyword with the same meaning as mantlelitho
- **mantleupper**: the sublithospheric mantle above the 410 discontinuity 
- **410km**: the actual depth of 410 km discontinuity, an alternative to mantleupper
- **mantlemtz**: the mantle transition zone
- **670km**: an alternative keyword with the same meaning as mantlemtz
- **mantlelower**: lower mantle 

Notice: these keywords might be used for every data row, or mark the last one representing the given layer. Each of these layers must be continuous (without any other layers between its start and end points).

All lines starting with #, /, % and ! are treated as comments and ignored.

# Profile Validation

There are two main methods of profile validation:

- signalling if the value is outside a feasible range. **ParameterMin** and **ParameterMax** columns must be provided in the model reference file to utilise it 
- signalling if the value is too far from an expected value. In that case, the reference model must contain Parameter and **ParameterSigma** columns (or ParameterSigma+ and ParameterSigma- to apply different standard deviations for values above and below the reference one). Alternatively, the reference model can contain Parameter and **Parameter%** columns (or Parameter%+ and Parameter%-).

For each assessable record in the input data table, a corresponding reference parameter value is linearly interpolated to the provided depth levels. If the depth value is above the uppermost reference value or it is below the lowermost available value, two first (last) points of the reference profile are used to interpolate the value. 

An additional test scenario is provided to check whether any **melting** may occur along the profile. In that case, the code will report any temperature above the **solidus** and **liquidus**. 

Notice: a reference model can use Pressure or Depth as an input field. In the former case, the pressures will be converted to depths according to a supplied model. 

# Available Options

Type validearth.py --help to check the possible runtime options.

# Future Work

Planned extensions of the toolkit include

- Assessment of gradients between adjacent vertical profiles, enabling the identification of spatial variations and potentially anomalous transitions between neighbouring profiles.

- 3D reference models that will allow to assess the data with respect to its geological setting.

# Bibliography

Refer to the bibliography.bib file in the root directory for all the reference models.

# Standards

The code is written using Python 3.10 standard

# Authorship

This code was written by Ilya Fomin
(C) Ilya Fomin, 2026
