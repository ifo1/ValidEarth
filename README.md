# ValidEarth

**ValidEarth** is a geophysical Quality-Assurance toolkit for Deep Earth studies. Its core purpose is to assess differences between provided Earth physical-property profiles and established regional or global reference models. By simultaneously checking a wide range of parameters, the toolkit automates much of the routine work involved in data validation and helps identify genuine anomalies - or signals - that may indicate previously unrecognised features in the data.

The assessable properties include key parameters such as density, temperature, bulk and shear seismic velocities and their ratio, and the chemical composition of the mantle. The toolkit can be readily extended to support additional physical quantities and reference models.

For each parameter, ValidEarth provides a set of well-established reference models based on experimental and seismic data, with all sources documented in the bibliography. Each reference data point is associated with an independent relative or absolute uncertainty, allowing comparisons to account for the expected variability and uncertainty of the reference models. By default, the tool reports differences exceeding three standard deviations (3σ). When multiple reference models are available for a parameter - for example, geotherms corresponding to different geological settings - the toolkit automatically identifies the best-matching reference profile.

**ValidRock** is an additional tool for quality-checking rock properties. It assesses whether combinations of properties such as density, Vp, and Vs fall within the ranges reported for known rock types. It can rapidly identify physically implausible combinations and highlight potentially problematic areas within a geological or geophysical model.

*ValidEarth and ValidRock are not a substitute for expert geological interpretation. A thorough assessment should always be performed by a qualified specialist with access to up-to-date regional geological information, technical reports, and relevant scientific literature.*

The author welcomes collaboration with researchers and practitioners interested in improving Quality Assurance for geological and geophysical models and developing more reliable, transparent, and reproducible modelling workflows.


# Input Data Format

A valid input file should contain the following sections:

- Optional keywords and values
- Column headers
- Data table

Optional keywords include **Name** (an arbitrary string), **CoordinateSystem** (Geographic or Cartesian), **Longitude**, and **Latitude**. Each keyword must be specified on a separate line.

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

ValidEarth comes with a set of standard models such as PREM, as135f and others. Some of them, like PREM, are not suitable for the continental crust, as they severely underestimate the Moho depth and impose an ocean at the Earth's surface. Other models might be also not so good for the cratonic areas, and so on. The Earth is very diverse, and this toolkit is an instrument to automate and accelerate Quality Assessment, but not to replace it.

A default list of reference models is stored in the **config.txt** file (the file lists relative or absolute paths to the models, one path per line). The user can use a command line option (**-refmodels**) to specify a custom config file or amend the existing one.

ValidEarth performs some checks even if no reference file was provided, including the depths of major geological boundaries. Use **-refmodels noref** to perform only the basic checks.

Some models (like solidi and liquidi) use pressure instead of depth, so that the temperature-depth dependency must be computed during a separate step. ValidEarth allows to switch between pressure-depth models (look-up and interpolation tables) using the **-pressuremodel** command line option. By default, the PREM pressure model is used to convert mantle solidi and liquidi to depth profiles.

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
```console
python3 ./validrock.py -i examples/examplerock1.dat -pdf
```
Its expected output is stored in examples/examplerock1.log

# Understanding Program Outputs

Program outputs begin with general information summary from the input data file, which might be useful for troubleshooting.

The most important section, however, is a comparison table with the following columns:
- **Layer Name** is the name of geological unit. Note that only the units that exist in the reference model and in the input file will be shown. All the other units will be merged downwards. 
- **Layer Index** is an integer number indicating the row of data table with the layer boundary. Provided both for the input model and for the reference one.
- **Bedding Depth** is the depth of last record representing the given layer. Provided both for the input model and for the reference one.
- **Stdev** and **Abs** show the absolute difference between the reference model and the input file, represented by the number of standard deviations and by absolute value. The code shows separately differences for the predictions greater and less than the reference curve.
- **Rel** and **Abs** appear for the reference parameters that come with the Minimum and Maximum boundaries and show the distance from the minimum and maximum values (if the value is out of the range). The Relative column shows the absolute difference divided by the range. 

## Graphic Outputs and Detailed Profiles

Use **-png** or **-pdf**, so that ValidEarth and ValidRock will automatically create plots for each assessed physical quantity showing the relevant Earth reference models or available rock property dataset just next to it.

ValidEarth can produce detailed tables comparing properties along the supplied profiles and relevant Earth reference models (using **-detailed**).

# Derived and Mutually-Dependent Parameters

Some important parameters are mutually dependent, for example, the Vp/Vs ratio and Vp and Vs velocities, or the Magnesium Number (Mg#) and MgO and FeO content. However, if the values of two parameters fall in between certain reasonable bounds, it does not necessarily mean that the third one will be feasible as well.

ValidEarth aims to tackle these issues and it calculates the third parameter if the other two are provided.

# Available Options and Examples

Run:
```console
python3 validearth.py --help
```
or 
```console
python3 validrock.py --help
```
to display the available command-line options.

ValidEarth comes with several examples, the expected outputs (*.log files) are stored in the models/ directory next to the input files.

### Example 1 

Run
```console
python3 ./validearth.py -i examples/example1.dat
```
to assess the example column using a set of 1D models. The code automatically looks for the matching column names and compares the data.

The plots will show not only the input model and reference profiles, but also a highlighted area marking one standard deviation in each direction from the reference values.  

### Example 1a: using a 3D reference

Requires a valid ECM1 model file to be provided (see above)! Update the config file to include a path to the produced ValidEarth reference model file!

Run
```console
python3 ./validearth.py -i examples/example1.dat -dist 100 -pdf
```
to assess the example column using a 3D model. The density, Vp and Vs charts allow to compare the properties of individual layers along the profile. 

### Example 2: mantle chemistry

Run
```console
python3 ./validearth.py -i examples/example2.dat
```
This run should report
```console
Error: at the depth of 286000.0 The following MgO, FeO, Mg# values are inconsistent: 30.08 / 8.16 ≠ 89.27
```
as ValidEarth verifies that the value of Mg# matches the provided MgO and FeO contents, however, the execution continues and all the other reports are produced.

### Example 3: the quartzites and missed Moho

Run
```console
python3 ./validearth.py -i examples/example3.dat
```
This run should terminate saying
```console
Error at the depth of 6250.0: the Vp/Vs ratio of 1.5133290113958557 is less than 1.6 and can only be explained by quartzites (alpha-quartz).
To allow quartzite, check the -allowqtz command line option.
```
This check allows to find anomalous Vp/Vs values, as quartzites is probably the only rock species with very low Vp/Vs ratios. In case they are expected in the region, one can proceed and rerun the test saying:
```console
python3 ./validearth.py -i examples/example3.dat -allowqtz
```
This run will produce numerous warning about low Vp/Vs ratios and finally stop saying:
```console
Error: The crustal-mantle transition has no density contrast!
```
as ValidEarth verifies that all the available physical properties (such as density, Vp, and Vs) change simultaneously and consistently at the Moho.

### Example 4: the geotherm

Run
```console
python3 ./validearth.py -i examples/example4.dat -pdf -detailed
```
to assess a geothermal profile using one of the reference lithospheric geotherms and solidus and liquidus curves. ValidEarth will produce the interpolated liquidus and solidus temperatures along the studied profile, as well as a short summary in the end. 

### Example 5

Run
```console
python3 ./validearth.py -i examples/example5.dat -pdf -detailed
```
to try a yet another example of profile assessment and produce reference plots. ValidEarth will automatically select matching column names from the available models to perform the assessment. The plots will show not only the input model and reference profiles, but also a highlighted area marking one standard deviation in each direction from the reference values.  

### Example 6: the non-consistent Moho

Run
```console
python3 ./validearth.py -i examples/example6.dat
```
this example should result in failure; is reads:
```console
Error at the depth of -200000.0: the depth cannot be less than -9000 (exceeding the highest mountain on the Earth); probably, -depthneg flag might help
```
Indicating that the depth scale is wrong and offering a solution. However, once applied, it should return:
```console
Error: the depth is not non-increasing in the input file: 195000.0 vs 190000.0; probably, -depthrev flag might help
```
Indicating a yet another problem. However, with these two flags the example should go a bit further and crash again:
```console
Error at the depth of 10050.0: the density is less than 10 kg/m3; probably, the units are wrong - kg/m3 expected. Check the -udens flag
```
Finally, we can assemble a correct line:
```console
python3 ./validearth.py -i examples/example6.dat -depthneg -depthrev -udens g/cm3
```
the code should detect that the actual depth of Moho layer according to the physical properties is not consistent with the annotated value, annotating the numbers of rows:
```console
The Moho detected using Vs contrast right beneath -23000.0 m
Error: the Moho depth is not consistent: 61 vs 84
```

### Example 7: the sediments are too thick

Run
```console
python3 ./validearth.py -i examples/example6.dat
```
This run should fail reporting:
```console
Error at the depth of 5500.0: The thickness of sediments exceeds the maximum allowed one of 5000 m
To allow thicker sedimentary deposits, check the -allowthicksed command line option.
```
ValidEarth uses Vp/Vs > 2 to deem rocks as unconsolidated sediments; it should be a feasible threshold for a vast majority of cases. However, every such a reporting should be assessed individually, and if a very thick layer of sediments is present in the area, this error can be suppressed: 
```console
python3 ./validearth.py -i examples/example7.dat -allowthicksed 10000
```
And the code will still warn about a potential issue, but will proceed to other comparisons.

# Automatisation

The current version of ValidEarth and ValidRock allows to process only one file per call. However, it can be easily automated using simplistic shell scripts like:

```console
for file in /my/folder/with/model/files/*.txt ; do python3 validearth.py -i $file -depthrev -depthneg -udens g/cm3 ; done &>> log.txt &
```

During initial model assessment, it might be very useful to produce a list of columns that contain obvious errors. An additional shell script provided with the tool can do this job for you:

```console
./validearth_find_errors.sh log.txt
```

# To Do

Planned development of the toolkit include:

- Gradient analysis between adjacent vertical profiles, enabling the identification of spatial variations and potentially anomalous transitions between neighbouring profiles.

The author is looking forward for fruitfil collaboration and your suggestions!

# Bibliography

Refer to the bibliography.bib file in the root directory for all the reference models.

# Requirements

- Python 3.10
- modules termcolor, numpy, os, argparse, matplotlib

# Authorship

(C) Ilya Fomin, 2026
