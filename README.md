# ValidEarth

ValidEarth is a toolkit for verifying whether vertical profiles of Earth’s physical properties are consistent with established reference models. The properties assessed include key parameters such as density, temperature (including solidi and liquidi), bulk and shear seismic velocities and their ratio, chemical composition of the mantle - and the list can be easily extended). The tool does not nee

For each parameter, the toolkit comes with a set of well-established reference models based on experimental and seismic data, with all sources documented in the bibliography. Each reference data point is associated with an independent relative or absolute uncertainty, allowing the comparison to account for the expected variability and uncertainty of the reference models. The tool reports the differences that are greater than three sigmas; for the parameters with more than reference models provided (for example, geotherms for different geological settings), the tool looks for the best matching profile automatically.

# Input Data Format

The code accepts an input file with the following format:

<Optional Keywords and Values>
<Column Headers>
<Data Table>

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

All lines starting with #, /, % and ! are treated as comments and ignored.

# Available Options

Type validearth.py --help to check the possible runtime options.

# Future Work

Planned extensions of the toolkit include

- Assessment of gradients between adjacent vertical profiles, enabling the identification of spatial variations and potentially anomalous transitions between neighbouring profiles.

- 3D reference models that will allow to assess the data with respect to its geological setting.

# Bibliography

Refer to the bibliography.bib file in the root directory for all the reference models.
