from colouredstrings import error, warning, highlight
import numpy as np

# this file contains only data checks during column reading

def read_field(fieldname, pair, default=None):
    # Attempt to read a field from the input file
    # Inputs
    # fieldname - the name of field to read
    # pair      - a keyword and its value in input file
    # default   - the value that is already accepted 
    # Outputs:
    # a new (or supplied) value to be used
    # a flag signalling whether the field was matched

    if fieldname != pair[0]: return default, False

    if len(pair) < 2: print (warning() + "no value for " + highlight(fieldname) + " was provided")
    if len(pair) > 2: print (warning() + "multiple values for " + highlight(fieldname) + " were provided")

    print (fieldname + ": " + highlight(pair[1]))
    return pair[1], True


def read_float(fieldname, pair, minval = None, maxval = None, default=None):
    # Attempt to read a float from the input file
    # Inputs
    # fieldname - the name of field to read
    # pair      - a keyword and its value in input file
    # minval    - the minimum possible value of a parameter
    # maxval    - the maximum possible value of a parameter
    # default   - the value that is already accepted 
    # Outputs:
    # a new (or supplied) value to be used
    # a flag signalling whether the field was matched

    if fieldname != pair[0]: return default, False

    if len(pair) < 2: print (warning() + "no value for " + fieldname + " was provided")
    if len(pair) > 2: print (warning() + "multiple values for " + fieldname + " were provided")

    try:
        value = float(pair[1])
    except ValueError:
        print (error() + "the value supplied for " + highlight(fieldname) + " is not a valid number!")

    print (fieldname + ": " + highlight(value))

    if minval is not None:
        if value < minval:
            print (error() + "the value supplied for " + highlight(fieldname) + " is less than the minimum bound " + str(minval))

    if maxval is not None:
        if value > maxval:
            print (error() + "the value supplied for " + highlight(fieldname) + " is greater than the maximum bound " + str(maxval))

    return value, True


def read_value(fieldname, value):
    # Attempt to read a field from the input file
    # fieldname - the name of field to read (for reporting purposes only)
    # value     - a value in the input file

    if len(value) < 1:
        print (warning() + "data for " + highlight(fieldname) + " was not supplied")
        return np.nan

    if value == "NaN": return np.nan

    try:
        return float(value)
    except ValueError:
        print (error() + "the value supplied for " + highlight(fieldname) + " is not a valid number!")

