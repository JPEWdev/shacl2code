#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from .lang import LANGUAGES  # noqa: F401

# All renderers must be imported here to be registered
from .cpp import CppRender  # noqa: F401
from .jinja import JinjaRender  # noqa: F401
from .jsonschema import JsonSchemaRender  # noqa: F401
from .python import PythonRender  # noqa: F401
from .golang import GoLangRender  # noqa: F401
