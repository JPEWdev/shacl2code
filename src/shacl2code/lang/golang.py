#
# Copyright © 2024, Oracle and/or its affiliates
#
# SPDX-License-Identifier: MIT

from .common import BasicJinjaRender
from .lang import language, TEMPLATE_DIR

import re

DATATYPES = {
    "http://www.w3.org/2001/XMLSchema#string": "string",
    "http://www.w3.org/2001/XMLSchema#anyURI": "string",
    "http://www.w3.org/2001/XMLSchema#integer": "int",
    "http://www.w3.org/2001/XMLSchema#positiveInteger": "PInt",
    "http://www.w3.org/2001/XMLSchema#nonNegativeInteger": "uint",
    "http://www.w3.org/2001/XMLSchema#boolean": "bool",
    "http://www.w3.org/2001/XMLSchema#decimal": "float64",
    "http://www.w3.org/2001/XMLSchema#dateTime": "DateTime",
    "http://www.w3.org/2001/XMLSchema#dateTimeStamp": "DateTimeStamp",
}

RESERVED_WORDS = {
    "package"
}

def export(name):
    # export converts the shacl name into an exportable go type name
    name_list = name.split('_')
    for i in range(0,len(name_list)):
        name_list[i] = name_list[i][0].upper() + name_list[i][1:]
    return ''.join(name_list)


def type_name(name):
    parts = re.split(r'[^a-zA-Z0-9]', name)
    part = parts[len(parts)-1]
    return upper_first(part)


def struct_prop_name(prop):
    # prop:
    #  class_id, comment, datatype, enum_values, max_count, min_count, path, pattern, varname
    return lower_first(type_name(prop.varname))


def prop_type(prop):
    # prop:
    #  class_id, comment, datatype, enum_values, max_count, min_count, path, pattern, varname
    if prop.datatype in DATATYPES:
        typ = DATATYPES[prop.datatype]
    else:
        typ = type_name(prop.class_id)

    if prop.max_count is None or prop.max_count > 1:
        typ = '[]' + typ

    return typ


def setter_prop_type(prop):
    typ = prop_type(prop)
    return typ.replace('[]', "...")


def struct_prop(prop):
    return struct_prop_name(prop) + ' ' + prop_type(prop)


def interface_getter(prop):
    return upper_first(type_name(prop.varname)) + '() ' + prop_type(prop)


def interface_setter(prop):
    return "Set" + upper_first(type_name(prop.varname)) + '(' + setter_prop_type(prop) + ') error'


def struct_getter(cls, prop):
    return 'func (o *' + struct_name(cls) + ') ' + upper_first(type_name(prop.varname)) + '() ' + prop_type(prop) + '{\n' \
        + '    return o.' + struct_prop_name(prop) + '\n' \
        + '}'


def struct_setter(cls, prop):
    return 'func (o *' + struct_name(cls) + ') Set' + upper_first(type_name(prop.varname)) + '(v ' + setter_prop_type(prop) + ') error{\n' \
        + '    o.' + struct_prop_name(prop) + '  = v\n' \
        + '    return nil\n' \
        + '}'


def comment(indent_with, identifier, text):
    if text.lower().startswith(identifier.lower()):
        text = identifier + " " + text[len(identifier):]

    return indent(indent_with, text)

def parent_has_prop(classes, cls, prop):
    for parent_id in cls.parent_ids:
        parent = classes.get(parent_id)
        for p in parent.properties:
            if p.varname == prop.varname:
                return True
        if parent_has_prop(classes, parent, prop):
            return True

    return False


def include_prop(classes, cls, prop):
    return not parent_has_prop(classes, cls, prop)


def lower_first(str):
    return str[0].lower() + str[1:]


def interface_name(cls):
    return upper_first(type_name(cls.clsname))


def struct_name(cls):
    name = lower_first(type_name(cls.clsname))
    if name in RESERVED_WORDS:
        return name + "Impl"
    return name


def upper_first(str):
    return str[0].upper() + str[1:]


def indent(indent_with, str):
    parts = re.split("\n", str)
    return indent_with + ("\n"+indent_with).join(parts)


@language("golang")
class GolangRender(BasicJinjaRender):
    HELP = "Go Language Bindings"

    def __init__(self, args):
        super().__init__(args, TEMPLATE_DIR / "golang.j2")
        self.__render_args = {
                "module": args.module,
        }

    @classmethod
    def get_arguments(cls, parser):
        super().get_arguments(parser)
        parser.add_argument("--module", help="Go module name")

    def get_extra_env(self):
        return {
            "export": export,
            "type_name": type_name,
            "struct_prop": struct_prop,
            "struct_name": struct_name,
            "struct_getter": struct_getter,
            "struct_setter": struct_setter,
            "interface_name": interface_name,
            "interface_getter": interface_getter,
            "interface_setter": interface_setter,
            "include_prop": include_prop,
            "indent": indent,
            "comment": comment,
        }

    def get_additional_render_args(self):
        return self.__render_args
