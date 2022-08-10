"Custom actions for argparse"
from pathlib import Path
from typing import Any, Union, Sequence, Optional
from argparse import Action, Namespace, ArgumentError, ArgumentParser

class FileCheck(Action):
    "Action class to check existence of a given file path."

    def __init__(self, option_strings, dest, **kwargs):
        "Initialise the FileCheck action class"
        super().__init__(option_strings, dest, **kwargs)

    def __call__(# pylint: disable=[signature-differs]
            self, parser: ArgumentParser, namespace: Namespace,
            values: Union[str, Sequence[Any], None],
            option_string: Optional[str] = "") -> None:
        """Check existence of a given file path and set it, or raise an
        exception."""
        the_path = str(values or "")
        the_file = Path(the_path)
        if not the_file.is_file():
            raise ArgumentError(
                self,
                f"The file '{values}' does not exist or is a folder/directory.")

        setattr(namespace, self.dest, values)
