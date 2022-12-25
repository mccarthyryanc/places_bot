"""Places Bot"""
from importlib import metadata

__version__ = metadata.version(__package__)

del metadata

from . import masto
from . import city

