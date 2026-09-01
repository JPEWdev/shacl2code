# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT
"""Python language binding renderer"""

import hashlib
import keyword
import re
from pathlib import Path
from typing import Iterable

from jinja2 import TemplateRuntimeError

from .common import JinjaTemplateRender, prop_is_list
from .lang import TEMPLATE_DIR, language
from ..model import Class
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


def prop_shape(prop):
    """Classify a property's container shape: (is_list, has_ref, is_enum)."""
    is_enum = bool(prop.enum_values)
    has_ref = bool(prop.class_id) and not is_enum
    return prop_is_list(prop), has_ref, is_enum


def prop_element_pytype(prop, classes):
    """Python type of a single element of prop, ignoring container shape.

    Object-reference properties resolve to ``Union[str, 'ClassName']``, since
    they may be set from either an id string or the referenced object.
    """
    if prop.enum_values:
        return "str"
    if prop.class_id:
        return "Union[str, '" + varname(*classes.get(prop.class_id).clsname) + "']"
    if prop.datatype not in DATATYPE_PYTHON_TYPES:
        # Same error as model.py.j2's abort()
        raise TemplateRuntimeError("Unknown data type " + prop.datatype)
    return DATATYPE_PYTHON_TYPES[prop.datatype]


def protocols_use_datetime(classes: Iterable[Class]) -> bool:
    """Whether any class has a datetime-typed scalar or list property."""
    for cls in classes:
        for prop in cls.properties:
            _, has_ref, is_enum = prop_shape(prop)
            if has_ref or is_enum:
                continue
            if prop_element_pytype(prop, classes) == "datetime":
                return True
    return False


def protocols_use_object_refs(classes: Iterable[Class]) -> bool:
    """Whether any class has an object-reference-typed scalar or list property."""
    for cls in classes:
        for prop in cls.properties:
            _, has_ref, _ = prop_shape(prop)
            if has_ref:
                return True
    return False


def protocol_discriminator_name(cls: Class, key: str) -> str:
    """Stable, collision-resistant name for cls's Protocol discriminator method.

    key="iri": keyed by the class's raw IRI, so it matches across
    generations of the SAME model with different --context flags. varname()
    alone can sanitize two distinct IRIs to the same string (e.g. IRIs that
    differ only in punctuation runs both collapsing to "_"), so a short hash
    of the raw IRI is appended to disambiguate while staying stable across
    regenerations of the same class.

    key="compact-name": keyed by the --context-compacted class name
    instead -- the exact same name already used for the class itself, so
    any collision here would already be a duplicate Python class
    definition, independent of this function. Matches across different
    VERSIONS of an ontology that keeps its compact term names stable even
    as the underlying IRIs change (e.g. SPDX, which embeds its own spec
    version in every class IRI). Only safe when every generation being
    compared shares a canonical context.
    """
    if key == "compact-name":
        return varname(*cls.clsname)
    digest = hashlib.sha256(cls._id.encode("utf-8")).hexdigest()[:8]
    return varname(cls._id, digest)


def protocols_extra_imports(classes: Iterable[Class]) -> str:
    """Conditionally-needed stdlib imports for protocols.py.j2.

    Rendered as a single ``{{ }}`` expression (not a ``{% if %}`` block) so
    black can parse the .j2 source as Python. The blank lines black then
    requires around that expression separate these imports from the ones
    above by more than flake8-import-order allows within one group, so each
    line silences that deliberate exception. Always returns a non-blank
    line (a comment when there's nothing to import) so the surrounding
    black-mandated blank-line groups above and below never merge into one
    run long enough to trip flake8's too-many-blank-lines check.
    """
    lines = []
    if protocols_use_datetime(classes):
        lines.append("from datetime import datetime  # noqa: E402, I100, I202")
    if any(cls.named_individuals for cls in classes):
        lines.append("from typing import ClassVar, Dict  # noqa: E402, I100, I202")
    if protocols_use_object_refs(classes):
        lines.append("from typing import Union  # noqa: E402, I100, I202")
    if not lines:
        lines.append("# No extra imports needed for this model.")
    return "\n".join(lines)


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
        self.__include_main = args.include_main == "yes"
        self.__protocol_discriminator_key = args.include_protocols
        self.__include_protocols = args.include_protocols != "no"
        self.__use_slots = args.use_slots
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
            "--include-protocols",
            choices=("no", "iri", "compact-name"),
            default="no",
            help=(
                "Include a protocols.py module with version-agnostic Protocol "
                "types for every class. 'iri' keys each class's cross-version "
                "discriminator by its full IRI: stable across regenerations of "
                "the same model with different --context files, but differs if "
                "the ontology embeds its own version in class IRIs (e.g. SPDX). "
                "'compact-name' keys it by the --context-compacted class name "
                "instead: stable across ontology versions that keep the same "
                "compact term names (e.g. SPDX), but only safe when every "
                "generation being compared shares a canonical context. "
                "Default is '%(default)s'"
            ),
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

        if self.__include_protocols:
            yield get_file("protocols.py")

    def get_extra_env(self):
        return {
            "varname": varname,
            "prop_element_pytype": prop_element_pytype,
            "prop_shape": prop_shape,
            "protocol_discriminator_name": protocol_discriminator_name,
            "protocols_extra_imports": protocols_extra_imports,
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
            "include_main": self.__include_main,
            "include_protocols": self.__include_protocols,
            "protocol_discriminator_key": self.__protocol_discriminator_key,
            "use_slots": use_slots,
            "version": self.__version,
            "version_str": self.__version_str,
        }
