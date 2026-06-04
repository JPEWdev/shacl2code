#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT
"""Rust language binding renderer"""

import re
from pathlib import Path

from .common import JinjaTemplateRender
from .lang import TEMPLATE_DIR, language

RUST_KEYWORDS = (
    "as",
    "async",
    "await",
    "break",
    "const",
    "continue",
    "crate",
    "dyn",
    "else",
    "enum",
    "extern",
    "false",
    "fn",
    "for",
    "if",
    "impl",
    "in",
    "let",
    "loop",
    "match",
    "mod",
    "move",
    "mut",
    "pub",
    "ref",
    "return",
    "self",
    "Self",
    "static",
    "struct",
    "super",
    "trait",
    "true",
    "type",
    "unsafe",
    "use",
    "where",
    "while",
    "yield",
    # Reserved keywords
    "abstract",
    "become",
    "box",
    "do",
    "final",
    "macro",
    "override",
    "priv",
    "try",
    "typeof",
    "unsized",
    "virtual",
)


def varname(*name):
    """Make a valid Rust variable/field name in snake_case."""
    combined = "_".join(name)
    # Replace any non-alphanumeric characters with _
    combined = re.sub(r"[^a-zA-Z0-9]", "_", combined)
    # Insert _ before uppercase letters for camelCase conversion
    combined = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", combined)
    combined = combined.lower()
    # Consolidate runs of "_" to a single one
    combined = re.sub(r"__+", "_", combined)
    # Strip leading/trailing _
    combined = combined.strip("_")
    if not combined:
        combined = "field"
    if combined in RUST_KEYWORDS:
        combined = "r#" + combined
    return combined


def type_name(*name):
    """Make a valid Rust type name in PascalCase."""
    parts = []
    for n in name:
        for s in re.split(r"[^a-zA-Z0-9]+", n):
            if s:
                parts.append(s[0].upper() + s[1:])
    result = "".join(parts)
    if not result:
        result = "Type"
    return result


def struct_name(cls):
    """Get the struct name for a class."""
    return type_name(*cls.clsname)


def prop_field_name(prop):
    """Get the field name for a property."""
    return varname(prop.varname)


def prop_is_list(prop):
    """Check if a property is a list."""
    return prop.max_count is None or prop.max_count != 1


def prop_rust_type(prop, classes):
    """Get the Rust type for a property's data type."""
    if prop.enum_values:
        return "String"

    if prop.class_id:
        return "Ref"

    datatype_map = {
        "http://www.w3.org/2001/XMLSchema#string": "String",
        "http://www.w3.org/2001/XMLSchema#anyURI": "String",
        "http://www.w3.org/2001/XMLSchema#integer": "i64",
        "http://www.w3.org/2001/XMLSchema#positiveInteger": "i64",
        "http://www.w3.org/2001/XMLSchema#nonNegativeInteger": "i64",
        "http://www.w3.org/2001/XMLSchema#boolean": "bool",
        "http://www.w3.org/2001/XMLSchema#decimal": "f64",
        "http://www.w3.org/2001/XMLSchema#dateTime": "DateTime<FixedOffset>",
        "http://www.w3.org/2001/XMLSchema#dateTimeStamp": "DateTime<FixedOffset>",
    }

    if prop.datatype in datatype_map:
        return datatype_map[prop.datatype]

    raise Exception("Unknown data type " + prop.datatype)  # pragma: no cover


def prop_full_type(prop, classes):
    """Get the full Rust type for a property field."""
    inner = prop_rust_type(prop, classes)
    if prop_is_list(prop):
        return f"Vec<{inner}>"
    else:
        return f"Option<{inner}>"


def const_name(*name):
    """Make a SCREAMING_SNAKE_CASE constant name."""
    combined = "_".join(name)
    combined = re.sub(r"[^a-zA-Z0-9]", "_", combined)
    combined = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", combined)
    combined = combined.upper()
    combined = re.sub(r"__+", "_", combined)
    combined = combined.strip("_")
    return combined


def prop_ctx_name(cls, prop):
    """Get the context map variable name for a property."""
    return varname(*cls.clsname) + "_" + varname(prop.varname) + "_ctx"


def all_props(cls, classes):
    """Get all properties including inherited ones."""
    props = []
    seen_paths = set()

    def collect(c):
        for pid in c.parent_ids:
            collect(classes.get(pid))
        for p in c.properties:
            if p.path not in seen_paths:
                props.append(p)
                seen_paths.add(p.path)

    collect(cls)
    return props


def prop_defining_class(cls, prop, classes):
    """Find which class originally defines a property (for context map naming)."""
    # Check if this class directly defines the property
    for p in cls.properties:
        if p.path == prop.path:
            return cls

    # Otherwise, search parent classes
    for pid in cls.parent_ids:
        parent = classes.get(pid)
        result = prop_defining_class(parent, prop, classes)
        if result is not None:
            return result

    return None


def get_all_parent_ids(cls, classes):
    """Get all ancestor class IDs."""
    result = set()
    for pid in cls.parent_ids:
        result.add(pid)
        parent = classes.get(pid)
        result |= get_all_parent_ids(parent, classes)
    return result


def is_effectively_extensible(cls, classes):
    """Check if a class or any of its ancestors is extensible."""
    if cls.is_extensible:
        return True
    for pid in get_all_parent_ids(cls, classes):
        parent = classes.get(pid)
        if parent.is_extensible:
            return True
    return False


def escape_rust_string(s):
    """Escape a string for use in a Rust string literal (not raw)."""
    return s.replace("\\", "\\\\")


@language("rust")
class RustRender(JinjaTemplateRender):
    HELP = "Rust Language Bindings"

    FILES = (
        ("Cargo.toml", "Cargo.toml.j2"),
        ("src/lib.rs", "lib.rs.j2"),
    )

    def __init__(self, args):
        super().__init__(args)
        self.__output = args.output
        self.__package_name = args.package_name

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
            "-p",
            "--package-name",
            help="Rust crate name",
            default="shacl_model",
        )

    def get_outputs(self):
        t = TEMPLATE_DIR / "rust"
        src_dir = self.__output / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        for output_name, template_name in self.FILES:
            yield self.__output / output_name, t / template_name, {}

    def get_extra_env(self):
        return {
            "varname": varname,
            "type_name": type_name,
            "struct_name": struct_name,
            "prop_field_name": prop_field_name,
            "prop_is_list": prop_is_list,
            "prop_rust_type": prop_rust_type,
            "prop_full_type": prop_full_type,
            "const_name": const_name,
            "prop_ctx_name": prop_ctx_name,
            "all_props": all_props,
            "get_all_parent_ids": get_all_parent_ids,
            "is_effectively_extensible": is_effectively_extensible,
            "escape_rust_string": escape_rust_string,
            "prop_defining_class": prop_defining_class,
        }

    def get_additional_render_args(self, model):
        return {
            "package_name": self.__package_name,
        }
