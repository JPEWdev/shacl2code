#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from .lang import LANGUAGES  # noqa: F401

# All renderers must be imported here to be registered
from .jinja import JinjaRender  # noqa: F401
from .python import PythonRender  # noqa: F401
from .jsonschema import JsonSchemaRender  # noqa: F401
from .golang import GolangRender # noqa: F401
