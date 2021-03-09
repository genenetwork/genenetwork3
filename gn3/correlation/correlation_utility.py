"""module contains utility functions for correlation"""


class AttributeSetter:
    """class for setting Attributes"""

    def __init__(self, trait_obj):
        for key, value in trait_obj.items():
            setattr(self, key, value)

    def __str__(self):
        return self.__class__.__name__

    def get_dict(self):
        """dummy function  to get dict object"""
        return self.__dict__


def get_genofile_samplelist(dataset):
    """mock function to get genofile samplelist"""

    print(dataset)
    return ["C57BL/6J"]
