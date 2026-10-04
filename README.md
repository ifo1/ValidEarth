# ValidEarth

ValidEarth is a geophysical Quality-Assurance toolkit for Deep Earth studies. Its core purpose is to assess differences between provided Earth physical-property profiles and established regional or global reference models. By simultaneously checking a wide range of parameters, the toolkit automates much of the routine work involved in data validation and helps identify genuine anomalies - or signals - that may indicate previously unrecognised features in the data.

The assessable properties include key parameters such as density, temperature, bulk and shear seismic velocities and their ratio, and the chemical composition of the mantle. The toolkit can be readily extended to support additional physical quantities and reference models.

For each parameter, ValidEarth provides a set of well-established reference models based on experimental and seismic data, with all sources documented in the bibliography. Each reference data point is associated with an independent relative or absolute uncertainty, allowing comparisons to account for the expected variability and uncertainty of the reference models. By default, the tool reports differences exceeding three standard deviations (3σ). When multiple reference models are available for a parameter - for example, geotherms corresponding to different geological settings - the toolkit automatically identifies the best-matching reference profile.

**ValidRock** is an additional tool for checking the rock properties. It assesses whether the combinations of given rock properties such as density, Vp, and Vs fall within the reported ranges of any rock species. It can rapidly identify the combinations of rock properties that are non-physical and potential problematic areas within the model.

*This tool cannot replace a careful examination of models by a qualified specialist having access to modern technical reports and scientific artices on the region of interest. The author is looking forward to collaboration with those interested in Quality Assurance for geological and geophysical models.*


# Input Data Format

A valid input file should contain the following sections:

- Optional keywords and values
- Column headers
- Data table

Optional keywords include **Name** (an arbitrary string without whitespace), **CoordinateSystem** (Geographic or Cartesian), **Longitude**, and **Latitude**. Each keyword must be specified on a separate line.

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

The header line must be followed by a data table containing the values to be validated. The table must be ordered by depth (increasing or decresing), the depth can be positive or negative above sea level (check flags **-depthneg** and **-depthrev**). The values by default are treated as nodes-centred (i.e. value at point). To use cell based approach (a value assigned to a volume, or voxel), specify the depth level at the beginning and at the end of each cell; ValidEarth allows repeating depth values for adjacent cells.

By default, ValidEarth assumes that physical quantities are expressed in SI units unless otherwise specified. Selected automatic unit conversions can be enabled using command-line options.

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

ValidEarth provides three main methods for profile validation:

- **Depth interval validation**: the main boundaries such as the water body depth, the thickness of unconsolidated sediments, and the Moho depth to be within certain feasible boundaries according to the modern sceintific data.

- **Range validation**: flags values outside a physically feasible range. The reference model must provide ParameterMin and ParameterMax columns for this type of validation.

- **Expected value validation**: flags values that differ significantly from an expected value. The reference model must provide Parameter (to be replaced by the name of an actual physical quantity) and ParameterStdev columns, or ParameterStdev+ and ParameterStdev- to specify different standard deviations above and below the reference value independently. Alternatively, the reference model can provide Parameter and Parameter% columns, with Parameter%+ and Parameter%- available for asymmetric relative uncertainties.

For each assessable record in the input data table, the corresponding reference parameter value is linearly interpolated to the provided depth. If a depth lies above the uppermost reference point or below the lowermost reference point, the first or last two reference points, respectively, are used for linear extrapolation.

An additional test is provided to assess whether melting may occur within the profile. In this case, ValidEarth reports temperatures exceeding the solidus and liquidus temperatures.

A reference model may use either Pressure or Depth as its independent variable. When pressure is used, it is converted to depth according to a supplied pressure-depth model.

## Configuring reference models

A default list of reference models is stored in the **config.txt** file (the file lists relative or absolute paths to the models, one path per line). The user can use command line options to specify a custom config file or amend the existing one.

ValidEarth performs some checks even if no reference file was provided, including the depth of major geological boundaries. Use **-noref** to perform only the basic checks.

## 3D Reference Models

By default, ValidEarth does not take into account the geographic locations of the reference and assesable columns. However, due to the great heterogeneity of mother Earth, it is really important to have this feature available.

ValidEarth allows the user to specify a certain distance (in metres) using the **-dist** option. Only if a reference column is within this distance from the examined column, it will be used for reporting. No global (1D) model (such as PREM) can be used in this mode, and vice versa.

Notice, that the code uses a simplified Haversine formula for the distance test.

The ValidEarth package contains a file called **ecm2validearth.py** (located in models/) that allows the user to convert the **ECM1** dataset to a ValidEarth 3D reference model file. 

# ValidRock

**ValidRock** (validrock.py) is an independent tool to verify the rock properties. This tool comes with its own databases (stored in **refrocks/** and specified in **configrocks.txt**) that allow to check whether the properties of rocks from a supplied file match any provided references. While many studies do not provide reference ranges for all rock properties simultaneously, **ValidRock** automatically checks all the provided reference models for different properties (e.g. the value for density may come from one study, and the values for Vp and Vs may be taken from another report). Like ValidEarth, ValidRock supports basic unit conversions and can produce **PNG** or **PDF** plots for each assessed physical quantity.

While ValidEarth operates using "pre-known" parameters listed in the corresponding section of this guide, **ValidRock** can operate with any physical quantities (while it cannot assess whether they are spelled correctly). The users can compile and add their own reference databases for rock resisitivity, conductivity, porosity, anisotropy or any other properties of interest. 

The author of this tool is highly interested in adding new databases to ValidEarth and ValidRock. Should there be any interest to develop a new database, please, contact me to discuss the best possible ways to implement and maintain it. 

**ValidRock** comes with its own example; this example contains a list of valid records and a botched one, that should be successfully identified:

python3 ./validrock.py -i examples/examplerock1.dat -pdf

Its expected output is stored in examples/examplerock2.log

# Understanding Program Outputs

Program outputs begin with general information summary from the input data file, which might be useful for troubleshooting.

The most important section, however, is a comparison table with the following columns:
- **Layer Name** is the name of geological unit. Note that only the units that exist in the reference model and in the input file will be shown. All the other units will be merged downwards. 
- **Layer Index** is an integer number indicating the row of data table with the layer boundary. Provided both for the input model and for the reference one.
- **Bedding Depth** is the depth of last record representing the given layer. Provided both for the input model and for the reference one.
- **Stdev** and **Abs** show the absolute difference between the reference model and the input file, represented by the number of standard deviations and by absolute value. The code shows separately differences for the predictions greater and less than the reference curve.
- **Rel** and **Abs** appear for the reference parameters that come with the Minimum and Maximum boundaries and show the distance from the minimum and maximum values (if the value is out of the range). The Relative column shows the absolute difference divided by the range. 

## Is the fit good or not?

A good question!

ValidEarth comes with a set of standard models such as PREM, as135f and others. Some of them, like PREM, are not suitable for the continental crust, as they severely underestimate the Moho depth and impose an ocean at the Earth's surface. Other models might be also not so good for the cratonic areas, and so on. The Earth is very diverse, and this toolkit is an instrument to automate and accelerate Quality Assessment, but not to replace it.

## Graphic Outputs

ValidEarth can automatically create plots (PDF or PNG) for each assessed physical quantity showing the relevant Earth reference models just next to it.

## Detailed Profiles

ValidEarth can produce tables with the properties of interest and relevant Earth reference models.

# Derived and Mutually-Dependent Parameters

Some important parameters are mutually dependent, for example, the Vp/Vs ratio and Vp and Vs velocities, or the Magnesium Number (Mg#) and MgO and FeO content. However, if the values of two parameters fall in between certain reasonable bounds, it does not necessarily mean that the third one will be feasible as well.

ValidEarth aims to tackle these issues and it calculates the third parameter if the other two are provided.

# Available Options

Run:

python validearth.py --help

or 

python validrock.py --help

to display the available command-line options.

ValidEarth comes with several examples, the expected outputs (logs, might be slightly different from the actual outputs) are stored in the models/ directory next to the input files:

## Example 1 

Run
python3 ./validearth.py -i examples/example1.dat
to assess the example column using a set of 1D models. The code automatically looks for the matching column names and compares the data.

The plots will show not only the input model and reference profiles, but also a highlighted area marking one standard deviation in each direction from the reference values.  

## Example 1a

Requires a valid ECM1 model file to be provided (see above)! Update the config file to include a path to the produced ValidEarth reference model file!

Run
python3 ./validearth.py -i examples/example1.dat -dist 100 -pdf

to assess the example column using a 3D model. The density, Vp and Vs charts allow to compare the properties of individual layers along the profile. 

## Example 2

Run
python3 ./validearth.py -i examples/example1.dat

to assess the example column using a set of 1D models. The code automatically looks for the matching column names and compares the data.

The plots will show the input model and a highighted area marking the range between minumum and maximum allowed values.  

## Example 3

Run
python3 ./validearth.py -i examples/example3.dat

to assess the example column using a set of 1D models. The code automatically looks for the matching column names and compares the data.

The plots will show not only the input model and reference profiles, but also a highlighted area marking one standard deviation in each direction from the reference values.  

## Example 4

Run
python3 ./validearth.py -i examples/example4.dat -pdf -detailed

to assess a geothermal profile using one of the reference lithospheric geotherms and solidus and liquidus curves. ValidEarth will produce the interpolated liquidus and solidus temperatures along the studied profile, as well as a short summary in the end. 

# To Do

Planned development of the toolkit include:

- Tool for comparing with reference specimens instead of profile-to-profile comparisons.

- Gradient analysis between adjacent vertical profiles, enabling the identification of spatial variations and potentially anomalous transitions between neighbouring profiles.

The author is looking forward for fruitfil collaboration and your suggestions!

# Bibliography

Refer to the bibliography.bib file in the root directory for all the reference models.

# Requirements

- Python 3.10
- modules termcolor, numpy, os, argparse, matplotlib

# Authorship

This code was written by Ilya Fomin
(C) Ilya Fomin, 2026
