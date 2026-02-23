#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import argparse
import keyword
import re
from pathlib import Path

from .common import BasicJinjaRender, OutputFile
from .lang import language, TEMPLATE_DIR


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

    def __init__(self, args: argparse.Namespace):
        super().__init__(args, TEMPLATE_DIR / "python.j2")
        self.output_file = args.output
        self.__render_args = {
            "elide_lists": args.elide_lists,
        }

    def get_outputs(self):
        yield self.output_file, TEMPLATE_DIR / "python.j2", {}

        if self.output_file.path != "-":
            path = Path(self.output_file.path)
            stub_path = path.with_suffix(".pyi")
            yield OutputFile(stub_path), TEMPLATE_DIR / "python.pyi.j2", {}

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
