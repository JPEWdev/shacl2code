# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT
"""Python language binding renderer"""

import keyword
import re
from pathlib import Path

from .common import JinjaTemplateRender
from .lang import TEMPLATE_DIR, language
from ..util import convert_version_string

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


SHACLOBJECT_RESERVED_WORDS = {
    "AUTO_NAMED_INDIVIDUALS",
    "CLASSES",
    "COMPACT_TYPE",
    "ID_ALIAS",
    "IS_ABSTRACT",
    "IS_DEPRECATED",
    "NAMED_INDIVIDUALS",
    "NODE_KIND",
    "PROPERTIES",
    "TYPE",
    "decode",
    "encode",
    "get_compact_type",
    "get_id",
    "get_type",
    "iter_objects",
    "link_helper",
    "property_keys",
    "set_id",
    "walk",
}


def protocol_name(cls):
    """Protocol name for a class — same as the class name (identity mapping)."""
    return varname(*cls.clsname)


def varname(*name):
    """Make a valid Python variable name."""
    name = "_".join(name)
    # Any invalid characters at the beginning of the name are removed (except "@")
    name = re.sub(r"^[^a-zA-Z0-9_@]*", "", name)
    # Any other invalid characters are replaced with "_" (including "@")
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    # Consolidate runs of "_" to a single one
    name = re.sub(r"__+", "_", name)
    # Append '_' to avoid collisions with Python or SHACLObject keywords
    while keyword.iskeyword(name) or name in SHACLOBJECT_RESERVED_WORDS:
        name = name + "_"
    return name


@language("python")
class PythonRender(JinjaTemplateRender):
    """Render Python Language Bindings."""

    HELP = "Python Language Bindings"

    FILES = (
        "__init__.py",
        "model.py",
        "model.pyi",
    )

    def __init__(self, args):
        super().__init__(args)
        self.__output = args.output
        self.__use_slots = args.use_slots
        self.__include_main = args.include_main == "yes"
        self.__protocols = args.use_protocols == "yes"
        self.__version_str = args.version
        if args.version:
            self.__version = repr(convert_version_string(args.version))
        else:
            self.__version = ""

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
            "--include-main",
            choices=("yes", "no"),
            default="yes",
            help="Generate a main function for the module. Default is '%(default)s'",
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
        parser.add_argument(
            "--version",
            help="Specify model version",
        )
        parser.add_argument(
            "--use-protocols",
            choices=("yes", "no"),
            default="no",
            help=(
                "Generate a protocols.py module with version-agnostic Protocol "
                "types for every class. Default is '%(default)s'"
            ),
        )

    def get_outputs(self):
        t = TEMPLATE_DIR / "python"
        self.__output.mkdir(parents=True, exist_ok=True)

        def get_file(name):
            return self.__output / name, t / (name + ".j2"), {}

        for s in self.FILES:
            yield get_file(s)

        if self.__include_main:
            yield get_file("cmd.py")
            yield get_file("__main__.py")

        if self.__protocols:
            yield get_file("protocols.py")

    def get_extra_env(self):
        return {
            "varname": varname,
            "protocol_name": protocol_name,
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
            "include_main": self.__include_main,
            "protocols": self.__protocols,
            "version_str": self.__version_str,
            "version": self.__version,
        }
