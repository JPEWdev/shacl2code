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
        self.__render_args = {
            "elide_lists": args.elide_lists,
        }

    @classmethod
    def get_arguments(cls, parser):
        super().get_arguments(parser)

        parser.add_argument(
            "--elide-lists",
            action="store_true",
            help="Elide lists when writing documents if they only contain a single item",
        )

    def get_additional_render_args(self):
        return self.__render_args
