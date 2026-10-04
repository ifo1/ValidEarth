#!/bin/bash

# this is a sample minimalistic script that parses a log file from ValidEarth batch run to produce a list of columns that resulted in errors. 
# check the readme for further information

awk '
BEGIN { IGNORECASE = 1 }

/Reading file/ {
    filename = $0
    sub(/^[[:space:]]*Reading file[[:space:]]*/, "", filename)
    found = 0
    next
}

found == 0 && /error/ {
    print filename " " $0
    found = 1
}
' "$1"
