import os
import sys
from distutils.core import Command

class RunTests(Command):
    """
    A custom command to run tests.
    """
    description = "Run the tests"
    test_types = (
        "all", "unit", "integration", "performance")
    user_options = [
        ("type=", None,
         f"""Specify the type of tests to run.
         Valid types are {tuple(test_types)}.
         Default is `all`.""")]

    def __init__(self, dist):
        """Initialise the command."""
        super().__init__(dist)
        self.command = "pytest"

    def initialize_options(self):
        """Initialise the default values of all the options."""
        self.type = "all"

    def finalize_options(self):
        """Set final value of all the options once they are processed."""
        if self.type not in RunTests.test_types:
            raise Exception(f"""
            Invalid test type (self.type) requested!
            Valid types are
            {tuple(RunTests.test_types)}""")

        if self.type != "all":
            self.command = f"pytest -m {self.type}_test"
    def run(self):
        """Run the chosen tests"""
        print(f"Running {self.type} tests")
        os.system(self.command)
