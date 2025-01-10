#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from .common import JinjaTemplateRender
from .lang import language, TEMPLATE_DIR

from pathlib import Path

import re

GO_KEYWORDS = (
    "break",
    "default",
    "func",
    "interface",
    "select",
    "case",
    "defer",
    "go",
    "map",
    "struct",
    "chan",
    "else",
    "goto",
    "package",
    "switch",
    "const",
    "fallthrough",
    "if",
    "range",
    "type",
    "continue",
    "for",
    "import",
    "return",
    "var",
)


def varname(*name, public=True):
    new_name = []
    for n in name:
        for s in re.split(r"[^a-zA-Z0-9]+", n):
            if not s:
                continue
            new_name.append(s)
    if public:
        new_name = [s[0].upper() + s[1:] for s in new_name]
    else:
        new_name = [new_name[0][0].lower() + new_name[0][1:]] + [
            s[0].upper() + s[1:] for s in new_name[1:]
        ]
    new_name = "".join(new_name)
    if new_name in GO_KEYWORDS:
        new_name = new_name + "_"
    return new_name


def struct_name(cls):
    return varname(*cls.clsname) + "Object"


def interface_name(cls):
    return varname(*cls.clsname)


def class_type_var(cls):
    return varname(*cls.clsname, public=False) + "Type"


def prop_name(prop):
    return varname(prop.varname, public=False)


def prop_is_list(prop):
    return prop.max_count is None or prop.max_count != 1


def prop_go_type(prop, classes):
    if prop.enum_values:
        return "string"

    if prop.class_id:
        intf = interface_name(classes.get(prop.class_id))
        return f"Ref[{intf}]"

    if prop.datatype == "http://www.w3.org/2001/XMLSchema#string":
        return "string"

    if prop.datatype == "http://www.w3.org/2001/XMLSchema#anyURI":
        return "string"

    if prop.datatype == "http://www.w3.org/2001/XMLSchema#integer":
        return "int"

    if prop.datatype == "http://www.w3.org/2001/XMLSchema#positiveInteger":
        return "int"

    if prop.datatype == "http://www.w3.org/2001/XMLSchema#nonNegativeInteger":
        return "int"

    if prop.datatype == "http://www.w3.org/2001/XMLSchema#boolean":
        return "bool"

    if prop.datatype == "http://www.w3.org/2001/XMLSchema#decimal":
        return "float64"

    if prop.datatype == "http://www.w3.org/2001/XMLSchema#dateTime":
        return "time.Time"

    if prop.datatype == "http://www.w3.org/2001/XMLSchema#dateTimeStamp":
        return "time.Time"

    raise Exception("Unknown data type " + prop.datatype)  # pragma: no cover


def prop_ctx_name(cls, prop):
    return varname(*cls.clsname, public=False) + varname(prop.varname) + "Context"


def prop_decode_func(cls, prop, classes):
    if prop.enum_values:
        func = "DecodeIRI"

    elif prop.class_id:
        func = "Decode" + interface_name(classes.get(prop.class_id))

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#string":
        func = "DecodeString"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#anyURI":
        func = "DecodeString"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#integer":
        func = "DecodeInteger"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#positiveInteger":
        func = "DecodeInteger"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#nonNegativeInteger":
        func = "DecodeInteger"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#boolean":
        func = "DecodeBoolean"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#decimal":
        func = "DecodeFloat"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#dateTime":
        func = "DecodeDateTime"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#dateTimeStamp":
        func = "DecodeDateTimeStamp"

    else:
        raise Exception("Unknown data type " + prop.datatype)  # pragma: no cover

    if prop_is_list(prop):
        return f"DecodeList[{prop_go_type(prop, classes)}](value, path, {prop_ctx_name(cls, prop)}, {func}, obj.{varname(prop.varname)}())"

    return f"{func}(value, path, {prop_ctx_name(cls, prop)}, obj.{varname(prop.varname)}())"


def prop_encode_func(cls, prop, classes):
    if prop.enum_values:
        func = "EncodeIRI"

    elif prop.class_id:
        func = "EncodeRef[" + interface_name(classes.get(prop.class_id)) + "]"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#string":
        func = "EncodeString"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#anyURI":
        func = "EncodeString"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#integer":
        func = "EncodeInteger"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#positiveInteger":
        func = "EncodeInteger"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#nonNegativeInteger":
        func = "EncodeInteger"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#boolean":
        func = "EncodeBoolean"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#decimal":
        func = "EncodeFloat"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#dateTime":
        func = "EncodeDateTime"

    elif prop.datatype == "http://www.w3.org/2001/XMLSchema#dateTimeStamp":
        func = "EncodeDateTime"

    else:
        raise Exception("Unknown data type " + prop.datatype)  # pragma: no cover

    if prop_is_list(prop):
        return f'EncodeList[{prop_go_type(prop, classes)}](self.{prop_name(prop)}.Get(), path.PushPath("{prop_name(prop)}"), {prop_ctx_name(cls, prop)}, state, {func})'

    return f'{func}(self.{prop_name(prop)}.Get(), path.PushPath("{prop_name(prop)}"), {prop_ctx_name(cls, prop)}, state)'


@language("golang")
class GoLangRender(JinjaTemplateRender):
    HELP = "Go Schema"

    FILES = (
        "classes.go",
        "decode.go",
        "encode.go",
        "errorhandler.go",
        "errors.go",
        "extensible.go",
        "linkstate.go",
        "listproperty.go",
        "optional.go",
        "path.go",
        "property.go",
        "ref.go",
        "reflistproperty.go",
        "refproperty.go",
        "shaclobject.go",
        "shaclobjectset.go",
        "shacltype.go",
        "util.go",
        "validator.go",
    )

    def __init__(self, args):
        super().__init__(args)
        self.__output = args.output
        self.__render_args = {
            "package": args.package,
        }

    @classmethod
    def get_arguments(cls, parser):
        parser.add_argument(
            "-p",
            "--package",
            help="Go Package Name",
            default="model",
        )
        parser.add_argument(
            "--output",
            "-o",
            type=Path,
            help="Output directory",
            required=True,
        )

    def get_outputs(self):
        t = TEMPLATE_DIR / "golang"

        for s in self.FILES:
            yield self.__output / s, t / (s + ".j2"), {}

    def get_extra_env(self):
        return {
            "varname": varname,
            "struct_name": struct_name,
            "interface_name": interface_name,
            "class_type_var": class_type_var,
            "prop_name": prop_name,
            "prop_is_list": prop_is_list,
            "prop_go_type": prop_go_type,
            "prop_ctx_name": prop_ctx_name,
            "prop_decode_func": prop_decode_func,
            "prop_encode_func": prop_encode_func,
        }

    def get_additional_render_args(self):
        return self.__render_args
