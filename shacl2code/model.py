#! /usr/bin/env python3
#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import keyword
import re
from pathlib import Path

from pyld import jsonld


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


class Model(object):
    def __init__(self, model_data):
        self.model = jsonld.expand(model_data)
        self.context = model_data.get("@context", {})
        self.compact = {}
        self.objects = {}
        self.classes = []
        self.enums = []

        for obj in self.model:
            self.compact[obj["@id"]] = jsonld.compact(obj, self.context)
            del self.compact[obj["@id"]]["@context"]

            self.objects[obj["@id"]] = obj

            if "http://www.w3.org/2002/07/owl#oneOf" in obj:
                self.enums.append(obj)
            elif "@type" in obj:
                if "http://www.w3.org/2002/07/owl#Class" in obj["@type"]:
                    self.classes.append(obj)

        self.classes.sort(key=lambda c: c["@id"])
        self.class_ids = set(c["@id"] for c in self.classes)

        self.enums.sort(key=lambda e: e["@id"])
        self.enum_ids = set(e["@id"] for e in self.enums)

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

    def get_template_enums(self):
        """
        Returns a list of enums suitable for passing to a Jinja template
        """
        template_enums = []
        for e in self.enums:
            values = []
            for v in get_prop(e, "http://www.w3.org/2002/07/owl#oneOf", "@list"):
                values.append(
                    {
                        "id": v["@id"],
                        "varname": to_var_name(v["@id"].split("/")[-1]),
                        "comment": self.get_comment(self.objects[v["@id"]]),
                    }
                )
            values.sort(key=lambda v: v["id"])

            template_enums.append(
                {
                    "id": e["@id"],
                    "clsname": self.get_class_name(e),
                    "enum_values": values,
                    "comment": self.get_comment(e),
                }
            )
        template_enums.sort(key=lambda e: e["id"])
        return template_enums

    def get_class_template_properties(self, cls):
        """
        Returns a list of properties for a class suitable for passing to a
        Jinja template
        """

        props = []
        for prop_id in cls.get("http://www.w3.org/ns/shacl#property", []):
            prop = self.objects[prop_id["@id"]]
            name = prop["http://www.w3.org/ns/shacl#name"][0]["@value"]
            prop_path = get_prop(
                prop,
                "http://www.w3.org/ns/shacl#path",
                "@id",
            )

            p = {
                "varname": to_var_name(name),
                "path": prop_path,
                "comment": self.get_comment(self.objects[prop_path]),
                "max_count": get_prop(
                    prop,
                    "http://www.w3.org/ns/shacl#maxCount",
                    "@value",
                    None,
                ),
                "min_count": get_prop(
                    prop,
                    "http://www.w3.org/ns/shacl#minCount",
                    "@value",
                    None,
                ),
            }

            prop_cls_id = get_prop(prop, "http://www.w3.org/ns/shacl#class", "@id")
            if prop_cls_id:
                if self.is_enum(prop_cls_id):
                    p["enumname"] = self.get_class_name(self.objects[prop_cls_id])
                elif self.is_class(prop_cls_id):
                    p["clsname"] = self.get_class_name(self.objects[prop_cls_id])
                else:
                    raise Exception(f"Unknown type '{prop_cls_id}'")
            else:
                p["datatype"] = get_prop(
                    prop,
                    "http://www.w3.org/ns/shacl#datatype",
                    "@id",
                )

            props.append(p)

        return props

    def get_template_classes(self):
        done_classes = set()
        classes = self.classes[:]

        template_classes = []
        while classes:
            c = classes.pop(0)

            parents = []
            for p in c.get("http://www.w3.org/2000/01/rdf-schema#subClassOf", []):
                if p["@id"] in self.objects:
                    parents.append(self.get_class_name(self.objects[p["@id"]]))

            # If any parent classes of this class are outstanding, then push it
            # back on the end of the class list and try again. This ensures that
            # derived classes are always written after any parent classes
            if not all(p in done_classes for p in parents):
                classes.append(c)
                continue

            clsname = self.get_class_name(c)
            template_classes.append(
                {
                    "id": c["@id"],
                    "clsname": clsname,
                    "parents": parents,
                    "comment": self.get_comment(c),
                    "props": self.get_class_template_properties(c),
                }
            )
            done_classes.add(clsname)

        return template_classes
