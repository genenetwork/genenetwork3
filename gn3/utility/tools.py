
import os 

from default_settings import GENENETWORK_FILES


def valid_file(fn):
    if os.path.isfile(fn):
        return fn
    return None

def valid_path(dir):
    if os.path.isdir(dir):
        return dir
    return None




def locate_ignore_error(name, subdir=None):
    """
    Locate a static flat file in the GENENETWORK_FILES environment.

    This function does not throw an error when the file is not found
    but returns None.
    """
    base = GENENETWORK_FILES
    if subdir:
        base = base+"/"+subdir
    if valid_path(base):
        lookfor = base + "/" + name
        if valid_file(lookfor):
            return lookfor
    return None
