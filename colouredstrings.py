from termcolor import colored

def warning(depth = None):
    if depth is None:
        return colored ("Warning: ", 'yellow', attrs=["bold"])
    else:
        return colored ("Warning: ", 'yellow', attrs=["bold"]) + " at the depth of " + colored (str(depth), 'yellow', attrs=["bold"]) + " "

def error(depth = None):
    if depth is None:
        return colored ("Error: ", 'red', attrs=["bold"])
    else:
        return colored ("Error: ", 'red', attrs=["bold"]) + " at the depth of " + colored (str(depth), 'red', attrs=["bold"]) + " "

def highlight(message):
    return colored (str(message), 'cyan', attrs=["bold"])

def red(message):
    return colored (str(message), 'red', attrs=["bold"])

def yellow(message):
    return colored (str(message), 'yellow', attrs=["bold"])

def green(message):
    return colored (str(message), 'green', attrs=["bold"])
