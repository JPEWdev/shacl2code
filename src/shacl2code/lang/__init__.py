#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from .lang import LANGUAGES

# All renderers must be imported here to be registered
from .python import PythonRender
from .raw import RawRender
