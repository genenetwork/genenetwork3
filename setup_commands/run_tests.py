import os
import sys
from distutils.core import Command

class RunTests(Command):
    """
    A custom command to run tests.
    """
    description = "Run the tests"
    commands = {
        "all": "pytest",
        "unit": "pytest tests/unit",
        "integration": "pytest tests/integration",
        "performance": "pytest tests/performance",
    }
    user_options = [
        ("type=", None,
         f"""Specify the type of tests to run.
         Valid types are {tuple(commands.keys())}.
         Default is `all`.""")]

    def __init__(self, dist):
        """Initialise the command."""
        super().__init__(dist)

    def initialize_options(self):
        """Initialise the default values of all the options."""
        self.type = "all"

    def finalize_options(self):
        """Set final value of all the options once they are processed."""
        if self.type not in RunTests.commands.keys():
            raise Exception(f"""
            Invalid test type (self.type) requested!
            Valid types are
            {tuple(RunTests.commands.keys())}""")

    def run(self):
        """Run the chosen tests"""
        print(f"Running {self.type} tests")
        os.system(RunTests.commands[self.type])
