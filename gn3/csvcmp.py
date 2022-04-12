"""This module contains functions for manipulating and working with csv
texts"""
from typing import Any, List

import re
import json
import os
import uuid
from gn3.commands import run_cmd


def extract_strain_name(csv_header, data, seek="Strain Name") -> str:
    """Extract a strain's name given a csv header"""
    for column, value in zip(csv_header.split(","), data.split(",")):
        if seek in column:
            return value
    return ""


def create_dirs_if_not_exists(dirs: list) -> None:
    """Create directories from a list"""
    for dir_ in dirs:
        if not os.path.exists(dir_):
            os.makedirs(dir_)


def remove_insignificant_edits(diff_data, epsilon=0.001):
    """Remove or ignore edits that are not within ε"""
    __mod = []
    if diff_data.get("Modifications"):
        for mod in diff_data.get("Modifications"):
            original = mod.get("Original").split(",")
            current = mod.get("Current").split(",")
            for i, (_x, _y) in enumerate(zip(original, current)):
                if (
                    _x.replace(".", "").isdigit()
                    and _y.replace(".", "").isdigit()
                    and abs(float(_x) - float(_y)) < epsilon
                ):
                    current[i] = _x
            if not (__o := ",".join(original)) == (__c := ",".join(current)):
                __mod.append(
                    {
                        "Original": __o,
                        "Current": __c,
                    }
                )
        diff_data["Modifications"] = __mod
    return diff_data


def clean_csv_text(csv_text: str) -> str:
    """Remove extra white space elements in all elements of the CSV file"""
    _csv_text = []
    for line in csv_text.strip().split("\n"):
        _csv_text.append(",".join([el.strip() for el in line.split(",")]))
    return "\n".join(_csv_text)


def csv_diff(base_csv, delta_csv, tmp_dir="/tmp") -> dict:
    """Diff 2 csv strings"""
    base_csv = clean_csv_text(base_csv)
    delta_csv = clean_csv_text(delta_csv)
    base_csv_list = base_csv.split("\n")
    delta_csv_list = delta_csv.split("\n")

    base_csv_header, delta_csv_header = "", ""
    for i, line in enumerate(base_csv_list):
        if line.startswith("Strain Name,Value,SE,Count"):
            base_csv_header, delta_csv_header = line, delta_csv_list[i]
            break
    longest_header = max(base_csv_header, delta_csv_header)

    if base_csv_header != delta_csv_header:
        if longest_header != base_csv_header:
            base_csv = base_csv.replace(
                "Strain Name,Value,SE,Count", longest_header, 1
            )
        else:
            delta_csv = delta_csv.replace(
                "Strain Name,Value,SE,Count", longest_header, 1
            )
    file_name1 = os.path.join(tmp_dir, str(uuid.uuid4()))
    file_name2 = os.path.join(tmp_dir, str(uuid.uuid4()))

    with open(file_name1, "w", encoding="utf-8") as _f:
        _l = len(longest_header.split(","))
        _f.write(fill_csv(csv_text=base_csv, width=_l))
    with open(file_name2, "w", encoding="utf-8") as _f:
        _f.write(fill_csv(delta_csv, width=_l))

    # Now we can run the diff!
    _r = run_cmd(
        cmd=('"csvdiff ' f"{file_name1} {file_name2} " '--format json"')
    )
    if _r.get("code") == 0:
        _r = json.loads(_r.get("output", ""))
        if any(_r.values()):
            _r["Columns"] = max(base_csv_header, delta_csv_header)
    else:
        _r = {}

    # Clean Up!
    if os.path.exists(file_name1):
        os.remove(file_name1)
    if os.path.exists(file_name2):
        os.remove(file_name2)
    return _r


def fill_csv(csv_text, width, value="x"):
    """Fill a csv text with 'value' if it's length is less than width"""
    data = []
    for line in csv_text.strip().split("\n"):
        if line.startswith("Strain") or line.startswith("#"):
            data.append(line)
        elif line:
            _n = line.split(",")
            for i, val in enumerate(_n):
                if not val.strip():
                    _n[i] = value
            data.append(",".join(_n + [value] * (width - len(_n))))
    return "\n".join(data)


def extract_invalid_csv_headers(allowed_headers: List, csv_text: str) -> List:
    """Check whether a csv text's columns contains valid headers"""
    csv_header = []
    for line in csv_text.split("\n"):
        if line.startswith("Strain Name"):
            csv_header = [_l.strip() for _l in line.split(",")]
            break
    invalid_headers = []
    for header in csv_header:
        if header not in allowed_headers:
            invalid_headers.append(header)
    return invalid_headers


def parse_csv_column(column: str) -> tuple:
    """Give a column, for example: 'Header(1)' or 'Header', return the
    column name i.e the column name outside the brackets, and the ID, the number
    inside the brackets."""
    case_attr_id = None
    name = column.strip()
    if (id_ := re.search(r"\((\w+)\)", column)):
        case_attr_id = id_.groups()[0].strip()
        name = column.split(f"({case_attr_id})")[0].strip()
    return (case_attr_id, name)
