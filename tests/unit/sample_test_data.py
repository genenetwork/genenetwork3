"""
This module holds a collection of sample data variables, used in more than one
 test.

This is mostly to avoid the `duplicate-code` pylint error that gets raised if
the same data is defined in more than one file. It has been found that adding
the `# pylint: disable=R0801` or `# pylint: disable=duplicate-code` to the top
of the file seems to not work as expected.

Adding these same declarations to .pylintrc is not an option, since that,
seemingly, would deactivate the warnings for all code in the project: We do not
want that.
"""

organised_trait_1 = {
    "1": {
        "ID": "1",
        "chromosomes": {
            1: {"Chr": 1,
                "loci": [
                    {
                        "Locus": "rs31443144", "cM": 1.500, "Mb": 3.010,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs6269442", "cM": 1.500, "Mb": 3.492,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs32285189", "cM": 1.630, "Mb": 3.511,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs258367496", "cM": 1.630, "Mb": 3.660,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs32430919", "cM": 1.750, "Mb": 3.777,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs36251697", "cM": 1.880, "Mb": 3.812,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs30658298", "cM": 2.010, "Mb": 4.431,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    }]},
            2: {"Chr": 2,
                "loci": [
                    {
                        "Locus": "rs51852623", "cM": 2.010, "Mb": 4.447,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs31879829", "cM": 2.140, "Mb": 4.519,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs36742481", "cM": 2.140, "Mb": 4.776,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    }]}}}}

organised_trait_2 = {
    "2": {
        "ID": "2",
        "chromosomes": {
            1: {"Chr": 1,
                "loci": [
                    {
                        "Locus": "rs31443144", "cM": 1.500, "Mb": 3.010,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs6269442", "cM": 1.500, "Mb": 3.492,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs32285189", "cM": 1.630, "Mb": 3.511,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs258367496", "cM": 1.630, "Mb": 3.660,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs32430919", "cM": 1.750, "Mb": 3.777,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs36251697", "cM": 1.880, "Mb": 3.812,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs30658298", "cM": 2.010, "Mb": 4.431,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    }]},
            2: {"Chr": 2,
                "loci": [
                    {
                        "Locus": "rs51852623", "cM": 2.010, "Mb": 4.447,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs31879829", "cM": 2.140, "Mb": 4.519,
                        "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                    },
                    {
                        "Locus": "rs36742481", "cM": 2.140, "Mb": 4.776,
                        "LRS": 0.579, "Additive": -0.074, "pValue": 1.000
                    }]}}}}
