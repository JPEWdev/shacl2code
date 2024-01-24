#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from .common import BasicJinjaRender
from .lang import language


@language("raw")
class RawRender(BasicJinjaRender):
    HELP = "Raw Jinja Output (for testing)"
    TEMPLATE = "raw.j2"
