"""Run the 'sample' correlations.

Converts code in
https://github.com/genenetwork/genenetwork2/blob/a08d91a234f700043d1d31164c7e2bacda4729da/wqflask/wqflask/correlation/correlation_gn3_api.py#L211-L216
into a script that can be run as an external process."""
import sys
import pickle
from argparse import ArgumentParser

from gn3.computations.correlations import compute_all_sample_correlation

from scripts.argparse_actions import FileCheck

# compute_all_sample_correlation(
#     corr_method=method, this_trait=this_trait_data, target_dataset=target_dataset_data)

if __name__ == "__main__":
    def cli_args():
        "Process the command-line arguments."
        parser = ArgumentParser(prog="sample_correlations")
        parser.add_argument(
            "corrmethod", help="The correlation method to use.", type=str,
            choices=("pearson", "spearman", "bicor"))
        parser.add_argument(
            "traitfile", help="Path to file with pickled trait.",
            type=str, action=FileCheck)
        parser.add_argument(
            "targetdataset", type=str, action=FileCheck,
            help="Path to file with pickled target dataset traits.")
        parser.add_argument(
            "destfile", type=str,
            help=("Path to file with pickled results of computing the "
                  "correlations."))
        args = parser.parse_args()
        return args

    def main():
        "CLI entry-point function"
        args = cli_args()
        with open(args.traitfile, "rb") as traitfile:
            with open(args.targetdataset, "rb") as targetdataset:
                corrs = compute_all_sample_correlation(
                    corr_method=args.corrmethod,
                    this_trait=pickle.load(traitfile),
                    target_dataset=pickle.load(targetdataset))

        with open(args.destfile, "wb") as dest:
            pickle.dump(corrs, dest)
        return 0

    sys.exit(main())
