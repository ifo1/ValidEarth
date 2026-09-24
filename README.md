# ValidEarth

ValidEarth is a geophysical Quality-Assurance toolkit for Deep Earth studies. Its core purpose is to assess differences between provided Earth physical-property profiles and established regional or global reference models. By simultaneously checking a wide range of parameters, the toolkit automates much of the routine work involved in data validation and helps identify genuine anomalies - or signals - that may indicate previously unrecognised features in the data.

The assessable properties include key parameters such as density, temperature, bulk and shear seismic velocities and their ratio, and the chemical composition of the mantle. The toolkit can be readily extended to support additional physical quantities and reference models.

For each parameter, ValidEarth provides a set of well-established reference models based on experimental and seismic data, with all sources documented in the bibliography. Each reference data point is associated with an independent relative or absolute uncertainty, allowing comparisons to account for the expected variability and uncertainty of the reference models. By default, the tool reports differences exceeding three standard deviations (3σ). When multiple reference models are available for a parameter - for example, geotherms corresponding to different geological settings - the toolkit automatically identifies the best-matching reference profile.

# Input Data Format

A valid input file should contain the following sections:

- Optional keywords and values
- Column headers
- Data table

Optional keywords include Name (an arbitrary string without whitespace), CoordinateSystem (Geographic or Cartesian), Longitude, and Latitude. Each keyword must be specified on a separate line.

The first column header must be **Depth**. It can be followed by any of the following headers:
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

The header line must be followed by a data table containing the values to be validated. By default, ValidEarth assumes that physical quantities are expressed in SI units unless otherwise specified. Selected automatic unit conversions can be enabled using command-line options.

The input format also supports tags identifying distinct geological domains or layers. These tags should appear as the last entry in each data row. The optional header Type can be used to identify this column.

Currently, ValidEarth recognises the following layer types (internally referred as golden nails to highlight their role as layer bottom markers):

- **water**: water bodies
- **soil**: soils
- **regolith**: unconsolidated sediments such as sand or gravel
- **sediments**: consolidated sediments such as sandstone or limestone
- **crustupper**: upper crystalline crust bottom
- **crustmiddle**: middle crystalline crust bottom
- **crustlower**: tlower crystalline crust bottom
- **Moho**: an alternative keyword with the same meaning as crustlower
- **mantlelitho**: the lithospheric mantle
- **LAB**: an alternative keyword with the same meaning as mantlelitho
- **mantleupper**: the sublithospheric mantle above the 410 discontinuity
- **410km**: an alternative keyword with the same meaning as mantleupper, the actual depth of 410 km discontinuity
- **mantlemtz**: mantle transition zone
- **670km**: an alternative keyword with the same meaning as mantlemtz, the actual depth of 670 km discontinuity
- **mantlelower**: the bottom of the lower mantle
- **CMB**: an alternative keyword with the same meaning as mantlelower, the actual depth of Core-Mantle Boundary 

These keywords can either be assigned to every data row within a layer or used only on the final row of a layer. In the latter case, they serve as markers identifying the bottom of the corresponding layer. Each layer must be continuous, with no other layer types occurring between its upper and lower boundaries.

All lines beginning with #, /, %, or ! are treated as comments and ignored.

# Profile Validation

ValidEarth provides two main methods for profile validation:

- Range validation: flags values outside a physically feasible range. The reference model must provide ParameterMin and ParameterMax columns for this type of validation.

- Reference-value validation: flags values that differ significantly from an expected value. The reference model must provide Parameter and ParameterSigma columns, or ParameterSigma+ and ParameterSigma- to specify different standard deviations above and below the reference value. Alternatively, the reference model can provide Parameter and Parameter% columns, with Parameter%+ and Parameter%- available for asymmetric relative uncertainties.

For each assessable record in the input data table, the corresponding reference parameter value is linearly interpolated to the provided depth. If a depth lies above the uppermost reference point or below the lowermost reference point, the first or last two reference points, respectively, are used for linear extrapolation.

An additional test is provided to assess whether melting may occur within the profile. In this case, ValidEarth reports temperatures exceeding the solidus and liquidus temperatures.

A reference model may use either Pressure or Depth as its independent variable. When pressure is used, it is converted to depth according to a supplied pressure-depth model.

# Understanding Program Outputs

Program outputs begin with general information summary from the input data file, which might be useful for troubleshooting.

The most important section, however, is a comparison table with the following columns:
- **Layer Name** is the name of geological unit. Note that only the units that exist in the reference model and in the input file will be shown. All the other units will be merged downwards. 
- **Layer Index** is an integer number indicating the row of data table with the layer boundary. Provided both for the input model and for the reference one.
- **Bedding Depth** is the depth of last record representing the given layer. Provided both for the input model and for the reference one.
- **Stdev** and **Abs** show the absolute difference between the reference model and the input file, represented by the number of standard deviations and by absolute value. The code shows separately differences for the predictions greater and less than the reference curve.
- **Rel** and **Abs** appear for the reference parameters that come with the Minimum and Maximum boundaries and show the distance from the minimum and maximum values (if the value is out of the range). The Relative column shows the absolute difference divided by the range. 

# Derived and Mutually-Dependent Parameters

Some important parameters are mutually dependent, for example, the Vp/Vs ratio and Vp and Vs velocities, or the Magnesium Number (Mg#) and MgO and FeO content. However, if the values of two parameters fall in between certain reasonable bounds, it does not necessarily mean that the third one will be feasible as well.

ValidEarth aims to tackle these issues and it calculates the third parameter if the other two are provided.

# Available Options

Run:

python validearth.py --help

to display the available command-line options.

# Future Work

Planned development of the toolkit include:

- Plotting tools to visualise differences between observed data and reference profiles.

- Gradient analysis between adjacent vertical profiles, enabling the identification of spatial variations and potentially anomalous transitions between neighbouring profiles.

- 3D reference models for assessing data in the context of its geological setting.

# Bibliography

Refer to the bibliography.bib file in the root directory for all the reference models.

# Requirements

- Python 3.10
- modules termcolor, numpy, os, argparse

# Authorship

This code was written by Ilya Fomin
(C) Ilya Fomin, 2026
