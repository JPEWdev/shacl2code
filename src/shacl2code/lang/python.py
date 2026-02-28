# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import re
import keyword

from .common import BasicJinjaRender, OutputFile
from .lang import language, TEMPLATE_DIR


def varname(*name):
    """
    Make a valid Python variable name.
    """

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
    """
    Render Python Language Bindings
    """

    HELP = "Python Language Bindings"

    def __init__(self, args):
        super().__init__(args, TEMPLATE_DIR / "python.py.j2")
        self._output_file = args.output
        self.__use_slots = args.use_slots
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
        parser.add_argument(
            "--use-slots",
            choices=("auto", "yes", "no"),
            default="auto",
            help="Use __slot__ to reduce memory usage. Slots prevents multiple inheritance. Default is %(default)s",
        )

    def get_extra_env(self):
        return {
            "varname": varname,
        }

    def get_additional_render_args(self, model):
        if self.__use_slots == "auto":
            use_slots = all(len(cls.parent_ids) <= 1 for cls in model.classes)
        elif self.__use_slots == "yes":
            use_slots = True
        else:
            use_slots = False
        return {
            "use_slots": use_slots,
            **self.__render_args,
        }

    def get_outputs(self):
        yield self._output_file, TEMPLATE_DIR / "python.py.j2", {}
        if self._output_file.path != "-":
            import os

            base, ext = os.path.splitext(self._output_file.path)
            pyi_path = base + ".pyi"
            yield OutputFile(pyi_path), TEMPLATE_DIR / "python.pyi.j2", {}
