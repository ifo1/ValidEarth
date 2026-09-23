from termcolor import colored

def warning(depth = None):
    if depth is None:
        print (colored ("Warning: ", 'yellow'))
    else:
        print (colored ("Warning: ", 'yellow') + " at the depth of " + colored (str(depth), 'yellow') + " ")

def error(depth = None):
    if depth is None:
        print (colored ("Error: ", 'yellow'))
    else:
        print (colored ("Error: ", 'yellow') + " at the depth of " + colored (str(depth), 'yellow') + " ")

