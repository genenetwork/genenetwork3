"""module contains performance tests for queries"""

import time
import sys

from inspect import getmembers
from inspect import isfunction

from typing import Optional
from functools import wraps
from gn3.db_utils import database_connector


def timer(func):
    """time function"""
    @wraps(func)
    def wrapper_time(*args, **kwargs):
        """time wrapper"""
        start_time = time.perf_counter()
        results = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print(f"the time taken is {run_time:.3f} seconds")
        return results

    return wrapper_time


def query_executor(query: str,
                   dataset_name: Optional[str] = "dataset_name",
                   fetch_all: bool = True):
    """function to execute a query"""
    conn, _ = database_connector()
    print(f"Performance test for {dataset_name}")

    with conn:
        cursor = conn.cursor()
        cursor.execute(query)

        if fetch_all:
            return cursor.fetchall()
        return cursor.fetchone()


def fetch_probeset_query(dataset_name: str):
    """contains queries for datasets"""

    query = """SELECT * from ProbeSetData
            where StrainID in (4, 5, 6, 7, 8, 9, 10, 11, 12,
            14, 15, 17, 18, 19, 20, 21, 22, 24, 25, 26, 28,
             29, 30, 31, 35, 36, 37, 39, 98, 99, 100, 103,
            487, 105, 106, 110, 115,116, 117, 118, 119, 
            120, 919, 147, 121, 40, 41, 124, 125, 128, 135,
            129, 130, 131, 132, 134, 138, 139, 140, 141, 142, 
            144, 145, 148, 149, 920, 922, 2, 3, 1, 1100)
            and id in (SELECT ProbeSetXRef.DataId
            FROM (ProbeSet, ProbeSetXRef, ProbeSetFreeze)
            WHERE ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id
            and ProbeSetFreeze.Name = '{}'
            and ProbeSet.Id = ProbeSetXRef.ProbeSetId)""".format(dataset_name)

    return query


@timer
def perf_simple_query():
    """initial simple query test"""

    query = """select * from ProbeSetData limit 1"""

    _results = query_executor(query)

    return {}


@timer
def perf_hc_m2_dataset():
    """test the default dataset HC_M2_0606_P"""

    query = fetch_probeset_query("HC_M2_0606_P")

    _results = query_executor(query, "HC_M2_0606_P")

    return {}


@timer
def perf_umutaffyexon_dataset():
    """largest dataset in gn"""

    query = fetch_probeset_query("UMUTAffyExon_0209_RMA")
    _results = query_executor(query, "UMUTAffyExon_0209_RMA")
    return {}


def fetch_perf_functions():
    """function to filter all functions strwith perf_"""
    name_func_dict = {name: func_obj for name, func_obj in
                      getmembers(sys.modules[__name__], isfunction)if isfunction(
                          func_obj)
                      and func_obj.__module__ == __name__ and name.startswith('perf_')}

    return name_func_dict


def fetch_cmd_args():
    """function to fetch cmd args\
    for example python file.py perf_hc_m2_dataset\
    output [perf_hc_m2_dataset obj]"""
    cmd_args = sys.argv[1:]

    name_func_dict = fetch_perf_functions()

    if len(cmd_args) > 0:
        callables = [func_call for name,
                     func_call in name_func_dict.items() if name in cmd_args]

        return callables

    return list(name_func_dict.values())


if __name__ == '__main__':
    func_list = fetch_cmd_args()
    for func_obj in func_list:
        func_obj()
