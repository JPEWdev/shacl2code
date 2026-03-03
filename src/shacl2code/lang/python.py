# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT
"""Python language binding renderer"""

import keyword
import re
from pathlib import Path

from .common import JinjaTemplateRender
from .lang import TEMPLATE_DIR, language

DATATYPE_CLASSES = {
    "http://www.w3.org/2001/XMLSchema#string": "StringProp",
    "http://www.w3.org/2001/XMLSchema#anyURI": "AnyURIProp",
    "http://www.w3.org/2001/XMLSchema#integer": "IntegerProp",
    "http://www.w3.org/2001/XMLSchema#positiveInteger": "PositiveIntegerProp",
    "http://www.w3.org/2001/XMLSchema#nonNegativeInteger": "NonNegativeIntegerProp",
    "http://www.w3.org/2001/XMLSchema#boolean": "BooleanProp",
    "http://www.w3.org/2001/XMLSchema#decimal": "FloatProp",
    "http://www.w3.org/2001/XMLSchema#dateTime": "DateTimeProp",
    "http://www.w3.org/2001/XMLSchema#dateTimeStamp": "DateTimeStampProp",
}

DATATYPE_PYTHON_TYPES = {
    "http://www.w3.org/2001/XMLSchema#string": "str",
    "http://www.w3.org/2001/XMLSchema#anyURI": "str",
    "http://www.w3.org/2001/XMLSchema#integer": "int",
    "http://www.w3.org/2001/XMLSchema#positiveInteger": "int",
    "http://www.w3.org/2001/XMLSchema#nonNegativeInteger": "int",
    "http://www.w3.org/2001/XMLSchema#boolean": "bool",
    "http://www.w3.org/2001/XMLSchema#decimal": "float",
    "http://www.w3.org/2001/XMLSchema#dateTime": "datetime",
    "http://www.w3.org/2001/XMLSchema#dateTimeStamp": "datetime",
}


def varname(*name):
    """Make a valid Python variable name."""
    name = "_".join(name)
    # Any invalid characters at the beginning of the name are removed (except "@")
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
class PythonRender(JinjaTemplateRender):
    """Render Python Language Bindings."""

    HELP = "Python Language Bindings"

    FILES = (
        "__init__.py",
        "__main__.py",
        "cmd.py",
        "model.py",
        "stub.pyi",
    )

    def __init__(self, args):
        super().__init__(args)
        self.__output = args.output
        self.__use_slots = args.use_slots
        self.__render_args = {
            "elide_lists": args.elide_lists,
        }

    @classmethod
    def get_arguments(cls, parser):
        parser.add_argument(
            "--output",
            "-o",
            type=Path,
            help="Output directory",
            required=True,
        )
        parser.add_argument(
            "--elide-lists",
            action="store_true",
            help="Elide lists when writing documents if they only contain a single item",
        )
        parser.add_argument(
            "--use-slots",
            choices=("auto", "yes", "no"),
            default="auto",
            help=(
                "Use __slot__ to reduce memory usage. "
                "Slots prevents multiple inheritance. Default is %(default)s"
            ),
        )

    def get_outputs(self):
        t = TEMPLATE_DIR / "python"
        self.__output.mkdir(parents=True, exist_ok=True)

        for s in self.FILES:
            yield self.__output / s, t / (s + ".j2"), {}

    def get_extra_env(self):
        return {
            "varname": varname,
            "DATATYPE_CLASSES": DATATYPE_CLASSES,
            "DATATYPE_PYTHON_TYPES": DATATYPE_PYTHON_TYPES,
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
