verbose = False

def print_verbose(*args, **kwargs):
    global verbose
    if verbose:
        print(*args, **kwargs)