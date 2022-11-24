"""Handle the management of resources."""
from uuid import UUID
from typing import NamedTuple

from gn3.auth import db
from .groups import Group
from .checks import authorised_p

class ResourceCategory(NamedTuple):
    """Class representing a resource category."""
    resource_category_id: UUID
    resource_category_key: str
    resource_category_description: str

class Resource(NamedTuple):
    """Class representing a resource."""
    group: Group
    resource_id: UUID
    resource_name: str
    resource_category: ResourceCategory

@authorised_p(("create-resource",),  error_message="Could not create resource")
def create_resource(
        conn: db.DbConnection, resource_name: str,
        resource_category: ResourceCategory):
    """Create a resource item."""
    return tuple()
