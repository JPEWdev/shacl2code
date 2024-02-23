#! /usr/bin/env python3
#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import keyword
import re
import typing
from dataclasses import dataclass

from pyld import jsonld


class ModelException(Exception):
    pass


def get_prop(o, name, key, default=None):
    if name in o:
        return o[name][0][key]
    return default


def to_var_name(name):
    name = name.replace("@", "_")
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    while keyword.iskeyword(name):
        name = name + "_"
    return name


@dataclass
class EnumValue:
    _id: str
    varname: str
    comment: str = ""


@dataclass
class Enum:
    _id: str
    clsname: str
    values: typing.List[EnumValue]
    comment: str = ""


@dataclass
class Property:
    path: str
    varname: str
    comment: str = ""
    max_count: int = None
    min_count: int = None
    enum_id: str = ""
    class_id: str = ""
    datatype: str = ""


@dataclass
class Class:
    _id: str
    clsname: str
    parent_ids: typing.List[str]
    properties: typing.List[Property]
    comment: str = ""


class Model(object):
    def __init__(self, model_data, context=None):
        self.model = jsonld.expand(model_data)
        self.context = context
        self.compact = {}
        self.objects = {}
        self.enums = []
        self.classes = []
        classes = []
        enums = []

        context = model_data.get("@context", {})

        for obj in self.model:
            self.compact[obj["@id"]] = jsonld.compact(obj, context)
            del self.compact[obj["@id"]]["@context"]

            self.objects[obj["@id"]] = obj

            if "http://www.w3.org/2002/07/owl#oneOf" in obj:
                enums.append(obj)
            elif "@type" in obj:
                if "http://www.w3.org/2002/07/owl#Class" in obj["@type"]:
                    classes.append(obj)

        self.class_ids = set(c["@id"] for c in classes)
        self.enum_ids = set(e["@id"] for e in enums)

        for obj in enums:
            e = Enum(
                _id=obj["@id"],
                clsname=self.get_class_name(obj),
                comment=self.get_comment(obj),
                values=[],
            )

            for v in get_prop(obj, "http://www.w3.org/2002/07/owl#oneOf", "@list"):
                e.values.append(
                    EnumValue(
                        _id=v["@id"],
                        varname=to_var_name(v["@id"].split("/")[-1]),
                        comment=self.get_comment(self.objects[v["@id"]]),
                    )
                )

            e.values.sort(key=lambda v: v._id)

            self.enums.append(e)

        for obj in classes:
            c = Class(
                _id=obj["@id"],
                parent_ids=[
                    p["@id"]
                    for p in obj.get(
                        "http://www.w3.org/2000/01/rdf-schema#subClassOf", []
                    )
                    if p["@id"] in self.objects
                ],
                clsname=self.get_class_name(obj),
                comment=self.get_comment(obj),
                properties=[],
            )

            for prop_id in obj.get("http://www.w3.org/ns/shacl#property", []):
                prop = self.objects[prop_id["@id"]]
                name = prop["http://www.w3.org/ns/shacl#name"][0]["@value"]
                prop_path = get_prop(
                    prop,
                    "http://www.w3.org/ns/shacl#path",
                    "@id",
                )

                p = Property(
                    varname=to_var_name(name),
                    path=prop_path,
                    comment=self.get_comment(self.objects[prop_path]),
                    max_count=get_prop(
                        prop,
                        "http://www.w3.org/ns/shacl#maxCount",
                        "@value",
                        None,
                    ),
                    min_count=get_prop(
                        prop,
                        "http://www.w3.org/ns/shacl#minCount",
                        "@value",
                        None,
                    ),
                )

                prop_cls_id = get_prop(prop, "http://www.w3.org/ns/shacl#class", "@id")
                if prop_cls_id:
                    if self.is_enum(prop_cls_id):
                        p.enum_id = prop_cls_id

                    elif self.is_class(prop_cls_id):
                        p.class_id = prop_cls_id
                    else:
                        raise ModelException(f"Unknown type '{prop_cls_id}'")
                else:
                    p.datatype = get_prop(
                        prop,
                        "http://www.w3.org/ns/shacl#datatype",
                        "@id",
                    )

                c.properties.append(p)

            self.classes.append(c)

        self.enums.sort(key=lambda e: e._id)
        self.classes.sort(key=lambda c: c._id)

        tmp_classes = self.classes
        done_ids = set()
        self.classes = []

        while tmp_classes:
            c = tmp_classes.pop(0)

            # If any parent classes of this class are outstanding, then push it
            # back on the end of the class list and try again. This ensures that
            # derived classes are always written after any parent classes
            if not all(p in done_ids for p in c.parent_ids):
                tmp_classes.append(c)
                continue

            self.classes.append(c)
            done_ids.add(c._id)

    def is_enum(self, _id):
        return _id in self.enum_ids

    def is_class(self, _id):
        return _id in self.class_ids

    def get_compact(self, obj, *path):
        """
        Returns the "compacted" name of an object, that is the name of the
        object with the context applied
        """
        v = self.compact[obj["@id"]]
        for p in path:
            v = v[p]
        return v

    def get_class_name(self, c):
        """
        Returns the name for a class that should be used in Code
        """
        return self.get_compact(c, "@id").replace(":", "_")

    def get_comment(self, obj, indent=0):
        """
        Get the comment for a object, or "" if the object has no comment
        """
        comment = get_prop(
            obj,
            "http://www.w3.org/2000/01/rdf-schema#comment",
            "@value",
        )
        if not comment:
            return ""

        return comment
