# ValidEarth

ValidEarth is a toolkit for verifying whether vertical profiles of Earth’s physical properties are consistent with established reference models. The properties assessed include key parameters such as density, temperature (including solidi and liquidi), bulk and shear seismic velocities and their ratio, chemical composition of the mantle - and the list can be easily extended). The tool does not nee

For each parameter, the toolkit comes with a set of well-established reference models based on experimental and seismic data, with all sources documented in the bibliography. Each reference data point is associated with an independent relative or absolute uncertainty, allowing the comparison to account for the expected variability and uncertainty of the reference models. The tool reports the differences that are greater than three sigmas; for the parameters with more than reference models provided (for example, geotherms for different geological settings), the tool looks for the best matching profile automatically.

# Input Data Format

The code accepts an input file with the following format:

- Optional Keywords and Values
- Column Headers
- Data Table

Optional keywords include Name (an arbitrary string without whitespace), CoordinateSystem (Geographic or Cartesian), Longitude, and Latitude. Each keyword must be on a separate line.

The first Column Header must be Depth. It can be followed by any of the following Headers:
- Temperature
- Vp
- Vs
- Density
- VpVs for the Vp/Vs ratio
- SiO2
- Al2O3
- FeO
- MgO
- CaO
- MgNum or Mg#

This line should be followed by a datatable with the actual values

By default, the code treats all the values as SI inputs, the unit for chemical compounds is wt.%, and the Mg# is in mol.%; that behaviour can be controlled using the command line options.

The code also allows specific tags for distinct domains. They should appear as the last entry for each data row; an auxilliary word "Type" can be used to mark this column. Currently the code recongnises the following keywords:
- soil: for all the layers representing soils
- regolith: for all the unconsolidated sediments such as sands, gravels and so on
- sediments: consolidated sediments like sandstone, limestone, and so on
- crustupper: the upper layer of crystalline crust
- crustmiddle: the middle layer of crystalline crust
- crustlower: the lower layer of crystalline crust
- Moho: an alternative keyword with the same meaning as crustlower
- mantlelitho: the lithospheric mantle
- LAB: an alternative keyword with the same meaning as mantlelitho
- mantleupper: the sublithospheric mantle above the 410 discontinuity 
- 410km: the actual depth of 410 km discontinuity, an alternative to mantleupper
- mantlemtz: the mantle transition zone
- 670km: an alternative keyword with the same meaning as mantlemtz
- mantlelower: lower mantle 

Notice: these keywords might be used for every specific row, or only for the last one in the depth profile. Only one entry for each domain is allowed.

All lines starting with #, /, % and ! are treated as comments and ignored.

# Profile Validation

The code checks whether the properties submitted for each layer fall within the properties of corresponding layers. If the input file (or reference model file) has no layers provided, or if there are multiple datapoints within this layer, the comparison is performed according to the depth value.

For each depth value of the input file, a corresponding parameter value is estimated using linear interpolation. If the depth value is above the uppermost reference value or it is below the lowermost available value, two first (last) points of the reference profile are used to interpolate the value. 

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
