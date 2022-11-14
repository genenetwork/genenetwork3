"""Handle the management of resource/user groups."""

from . import authorised_p

@authorised_p
def create_group(group_name):
    raise Exception("NOT IMPLEMENTED!")
