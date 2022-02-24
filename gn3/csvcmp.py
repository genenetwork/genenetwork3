import json
import os
import uuid
from gn3.commands import run_cmd


def create_dirs_if_not_exists(dirs: list):
    for dir_ in dirs:
        if not os.path.exists(dir_):
            os.makedirs(dir_)


def remove_insignificant_edits(diff_data, epsilon=0.001):
    _mod = []
    for mod in diff_data.get("Modifications"):
        original = mod.get("Original").split(",")
        current = mod.get("Current").split(",")
        for i, (x, y) in enumerate(zip(original, current)):
            if (x.replace('.', '').isdigit() and
                y.replace('.', '').isdigit() and
                    abs(float(x) - float(y)) < epsilon):
                current[i] = x
        if not (__o := ",".join(original)) == (__c := ",".join(current)):
            _mod.append({
                "Original": __o,
                "Current": __c,
            })
    diff_data['Modifications'] = _mod
    return diff_data


def csv_diff(base_csv, delta_csv, tmp_dir="/tmp"):
    base_csv_list = base_csv.strip().split("\n")
    delta_csv_list = delta_csv.strip().split("\n")

    _header1, _header2 = "", ""
    for i, line in enumerate(base_csv_list):
        if line.startswith("Strain Name,Value,SE,Count"):
            _header1, _header2 = line, delta_csv_list[i]
            break

    if _header1 != _header2:
        header = max(_header1, _header2)
        base_csv = base_csv.replace("Strain Name,Value,SE,Count",
                                    header, 1)
        delta_csv = delta_csv.replace("Strain Name,Value,SE,Count",
                                      header, 1)
    file_name1 = os.path.join(tmp_dir, str(uuid.uuid4()))
    file_name2 = os.path.join(tmp_dir, str(uuid.uuid4()))
    with open(file_name1, "w") as f_:
        f_.write(base_csv)
    with open(file_name2, "w") as f_:
        f_.write(delta_csv)

    # Now we can run the diff!
    _r = run_cmd(cmd=("csvdiff "
                      f"'{file_name1}' '{file_name2}' "
                      "--format json"))
    if _r.get("code") == 0:
        _r = json.loads(_r.get("output"))
        _r["Columns"] = max(_header1, _header2)
    else:
        _r = {}
    # Clean Up!
    if os.path.exists(file_name1):
        os.remove(file_name1)
    if os.path.exists(file_name2):
        os.remove(file_name2)
    return _r
