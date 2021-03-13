"""module contains general tools forgenenetwork"""

import os

from default_settings import GENENETWORK_FILES


def valid_file(file_name):
    """check if file is valid"""
    if os.path.isfile(file_name):
        return file_name
    return None


def valid_path(dir_name):
    """check if path is valid"""
    if os.path.isdir(dir_name):
        return dir_name
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
