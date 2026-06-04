# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT
"""shacl2code - Generate code from SHACL ontology models"""

from .main import main
from .model import Model, ModelException
from .urlcontext import ContextData, UrlContext
from .version import VERSION

__all__ = [
    "VERSION",
    "ContextData",
    "Model",
    "ModelException",
    "UrlContext",
    "main",
]
