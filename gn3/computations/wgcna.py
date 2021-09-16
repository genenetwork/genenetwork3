"""module contains code to preprocess and call wgcna script"""

import os
import json
import uuid
from gn3.settings import TMPDIR


def dump_wgcna_data(request_data):
    """function to dump request data to json file"""
    filename = f"{str(uuid.uuid4())}.json"

    temp_file_path = os.path.join(TMPDIR, filename)

    with open(temp_file_path, "w") as output_file:
        json.dump(request_data, output_file)

    return temp_file_path
