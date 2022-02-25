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

    base_csv_header, delta_csv_header, header = "", "", ""
    for i, line in enumerate(base_csv_list):
        if line.startswith("Strain Name,Value,SE,Count"):
            header = line
            base_csv_header, delta_csv_header= line, delta_csv_list[i]
            break
    longest_header = max(base_csv_header, delta_csv_header)

    if base_csv_header != delta_csv_header:
        if longest_header != base_csv_header:
            base_csv = base_csv.replace("Strain Name,Value,SE,Count",
                                        longest_header, 1)
        else:
            delta_csv = delta_csv.replace("Strain Name,Value,SE,Count",
                                          longest_header, 1)
        print(delta_csv)
    file_name1 = os.path.join(tmp_dir, str(uuid.uuid4()))
    file_name2 = os.path.join(tmp_dir, str(uuid.uuid4()))

    with open(file_name1, "w") as f_:
        _l = len(longest_header.split(","))
        f_.write(fill_csv(csv_text=base_csv,
                          width=_l))
    with open(file_name2, "w") as f_:
        f_.write(fill_csv(delta_csv,
                          width=_l))

    # Now we can run the diff!
    _r = run_cmd(cmd=("csvdiff "
                      f"'{file_name1}' '{file_name2}' "
                      "--format json"))
    if _r.get("code") == 0:
        _r = json.loads(_r.get("output"))
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
    data = []
    for line in csv_text.strip().split("\n"):
        if line.startswith("Strain") or line.startswith("#"):
            data.append(line)
        elif line:
            data.append(
                ",".join((_n:=line.split(",")) + [value] * (width - len(_n))))
    return "\n".join(data)
