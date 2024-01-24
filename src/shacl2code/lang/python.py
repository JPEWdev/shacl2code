#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from .common import BasicJinjaRender
from .lang import language


@language("python")
class PythonRender(BasicJinjaRender):
    HELP = "Python Language Bindings"
    TEMPLATE = "python.j2"
