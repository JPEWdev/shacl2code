#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from pathlib import Path

from .common import BasicJinjaRender
from .lang import language


@language("jinja")
class JinjaRender(BasicJinjaRender):
    HELP = "Render Jinja Output (for testing)"

    def __init__(self, args):
        super().__init__(args, args.template)

    @classmethod
    def get_arguments(cls, parser):
        super().get_arguments(parser)

        parser.add_argument(
            "--template",
            "-t",
            type=Path,
            help="Jinja Template file",
            required=True,
        )
