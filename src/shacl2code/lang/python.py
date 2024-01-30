#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from .common import BasicJinjaRender
from .lang import language, TEMPLATE_DIR


@language("python")
class PythonRender(BasicJinjaRender):
    HELP = "Python Language Bindings"

    def __init__(self, args):
        super().__init__(args, TEMPLATE_DIR / "python.j2")
