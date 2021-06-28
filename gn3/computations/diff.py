"""This module contains code that's used for generating diffs"""
from typing import Optional

from gn3.commands import run_cmd


def generate_diff(data: str, edited_data: str) -> Optional[str]:
    """Generate the diff between 2 files"""
    results = run_cmd(f"diff {data} {edited_data}")
    if results.get("code", -1) > 0:
        return results.get("output")
    return None
