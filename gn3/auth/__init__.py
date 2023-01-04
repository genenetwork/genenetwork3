"""Top-Level `Auth` module"""
from . import authorisation
from . import authentication

## Setup the endpoints
from .authorisation.views import *
from .authentication.oauth2.views import *
