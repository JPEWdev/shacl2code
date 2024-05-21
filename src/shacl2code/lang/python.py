#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from .common import BasicJinjaRender
from .lang import language, TEMPLATE_DIR

import re
import keyword


def varname(*name):
    name = "_".join(name)
    # Any invalid characters at the beginning of the name are removed (except
    # "@")
    name = re.sub(r"^[^a-zA-Z0-9_@]*", "", name)
    # Any other invalid characters are replaced with "_" (including "@")
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    # Consolidate runs of "_" to a single one
    name = re.sub(r"__+", "_", name)
    # Add a _ to anything that is a python keyword
    while keyword.iskeyword(name):
        name = name + "_"
    return name


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

    def get_extra_env(self):
        return {
            "varname": varname,
        }

    def get_additional_render_args(self):
        return self.__render_args
