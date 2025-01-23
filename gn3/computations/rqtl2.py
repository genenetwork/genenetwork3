import os
import csv
import uuid
import json
from pathlib import Path
from typing import Dict


def write_to_csv(work_dir, file_name, data:list[dict],
                      headers= None, delimiter=","):
    """Functions to write data list  to csv file
    if headers is not provided use the keys for first boject.
    """
    file_path = os.path.join(work_dir, file_name)
    if headers is None and data:
        headers = data[0].keys()
    with open(file_path, "w", encoding="utf-8") as file_handler:
        writer = csv.DictWriter(file_handler, fieldnames=headers,
                               delimiter=delimiter)
        writer.writeheader()
        for row in  data:
            writer.writerow(row)
        return file_path
