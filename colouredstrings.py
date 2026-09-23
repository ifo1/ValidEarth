from termcolor import colored

def warning(depth = None):
    if depth is None:
        return colored ("Warning: ", 'yellow')
    else:
        return colored ("Warning: ", 'yellow') + " at the depth of " + colored (str(depth), 'yellow') + " "

def error(depth = None):
    if depth is None:
        return colored ("Error: ", 'yellow')
    else:
        return colored ("Error: ", 'yellow') + " at the depth of " + colored (str(depth), 'yellow') + " "

def highlight(message):
    return colored ("Error: ", 'cyan')
