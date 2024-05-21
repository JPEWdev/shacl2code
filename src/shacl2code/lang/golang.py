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


def upper_first(string):
    # upper_first will capitalize the string
    return string[0].upper() + string[1:]


def lower_first(string):
    # lower_first sets the first character of a string to lower case
    return string[0].lower() + string[1:]


def type_name(clsname):
    # type_name converts the class name into an exportable go type name
    return upper_first(''.join(clsname).replace('_',''))


def interface_method(propname):
    # returns an interface method name
    # The interface method names are capitalized so they can be exported
    parts = propname.split('_')
    parts[0] = upper_first(parts[0])
    return ''.join(parts)

def struct_name(clsname):
    # Go structs are only used when a class is a concrete class
    return lower_first(type_name(clsname)) + "Impl"


def struct_prop_name(propname):
    # All properties in a Go struct are non-exportable
    return propname.replace('_','')


def setter_prop_type(prop):
    typ = prop_type(prop)
    return typ.replace('[]', "...")


def struct_prop(prop):
    return struct_prop_name(prop) + ' ' + prop_type(prop)


def interface_getter(prop):
    return type_name(prop.varname) + '() ' + prop_type(prop)


def interface_setter(prop):
    return "Set" + type_name(prop.varname) + '(' + setter_prop_type(prop) + ') error'


def struct_getter(cls, prop):
    return 'func (o *' + struct_name(cls) + ') ' + type_name(prop.varname) + '() ' + prop_type(prop) + '{\n' \
        + '    return o.' + struct_prop_name(prop) + '\n' \
        + '}'


def struct_setter(cls, prop):
    return 'func (o *' + struct_name(cls) + ') Set' + type_name(prop.varname) + '(v ' + setter_prop_type(prop) + ') error{\n' \
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




def interface_name(cls):
    return type_name(cls.clsname)




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
            "type_name": type_name,
            "interface_method": interface_method,
            "struct_prop_name": struct_prop_name,
            "struct_name": struct_name,
            "struct_getter": struct_getter,
            "struct_setter": struct_setter,
            "interface_name": interface_name,
            "interface_getter": interface_getter,
            "interface_setter": interface_setter,
            "include_prop": include_prop,
            "indent": indent,
            "comment": comment,
            "DATATYPES": DATATYPES,
        }

    def get_additional_render_args(self):
        return self.__render_args
