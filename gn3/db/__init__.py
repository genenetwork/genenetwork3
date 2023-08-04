# pylint: disable=[R0902, R0903]
"""Module that exposes common db operations"""
import logging
from dataclasses import asdict, astuple
from typing import Any, Dict, List, Optional, Generator, Tuple, Union
from typing_extensions import Protocol

from gn3.db.metadata_audit import MetadataAudit
from gn3.db.probesets import Probeset
from gn3.db.phenotypes import Phenotype
from gn3.db.phenotypes import Publication
from gn3.db.phenotypes import PublishXRef


from gn3.db.metadata_audit import metadata_audit_mapping
from gn3.db.probesets import probeset_mapping
from gn3.db.phenotypes import phenotype_mapping
from gn3.db.phenotypes import publication_mapping
from gn3.db.phenotypes import publish_x_ref_mapping

logger = logging.getLogger(__name__)


TABLEMAP = {
    "Phenotype": phenotype_mapping,
    "ProbeSet": probeset_mapping,
    "Publication": publication_mapping,
    "PublishXRef": publish_x_ref_mapping,
    "metadata_audit": metadata_audit_mapping,
}

DATACLASSMAP = {
    "Phenotype": Phenotype,
    "ProbeSet": Probeset,
    "Publication": Publication,
    "PublishXRef": PublishXRef,
    "metadata_audit": MetadataAudit,
}


class Dataclass(Protocol):
    """Type Definition for a Dataclass"""
    __dataclass_fields__: Dict


def diff_from_dict(old: Dict, new: Dict) -> Dict:
    """Construct a new dict with a specific structure that contains the difference
between the 2 dicts in the structure:

diff_from_dict({"id": 1, "data": "a"}, {"id": 2, "data": "b"})

Should return:

{"id": {"old": 1, "new": 2}, "data": {"old": "a", "new": "b"}}
    """
    dict_ = {}
    for key in old.keys():
        dict_[key] = {"old": old[key], "new": new[key]}
    return dict_
