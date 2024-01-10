#! /usr/bin/env python3
#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import argparse
import json
import keyword
import re
import sys
import tempfile
import textwrap
import urllib.parse
import urllib.request
from pathlib import Path
import pprint

from pyld import jsonld
from jinja2 import Environment, FileSystemLoader, TemplateRuntimeError

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent
TEMPLATE_DIR = THIS_DIR / "templates"


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


def get_langs():
    langs = []
    for child in TEMPLATE_DIR.iterdir():
        if child.suffixes and child.suffixes[-1] == ".j2":
            langs.append(child.stem)
    return langs


def main():
    parser = argparse.ArgumentParser(description="Convert JSON-LD model to python")
    parser.add_argument(
        "--lang",
        help="Output Language",
        choices=get_langs(),
        required=True,
    )
    parser.add_argument("input", help="Input JSON-LD model")
    parser.add_argument("output", type=Path, help="Output file")

    args = parser.parse_args()

    if "://" in args.input:
        with urllib.request.urlopen(args.input) as url:
            model = json.load(url)
    else:
        with Path(args.input).open("r") as f:
            model = json.load(f)

    context = model.get("@context", {})

    model = jsonld.expand(model)
    compact = {}

    objects = {}
    classes = []
    enums = []

    for obj in model:
        compact[obj["@id"]] = jsonld.compact(obj, context)
        del compact[obj["@id"]]["@context"]

        objects[obj["@id"]] = obj

        if "http://www.w3.org/2002/07/owl#oneOf" in obj:
            enums.append(obj)
        elif "@type" in obj:
            if "http://www.w3.org/2002/07/owl#Class" in obj["@type"]:
                classes.append(obj)

    classes.sort(key=lambda c: c["@id"])
    class_ids = set(c["@id"] for c in classes)

    enums.sort(key=lambda e: e["@id"])
    enum_ids = set(e["@id"] for e in enums)

    def get_compact(obj, *path):
        """
        Returns the "compacted" name of an object, that is the name of the
        object with the context applied
        """
        nonlocal compact
        v = compact[obj["@id"]]
        for p in path:
            v = v[p]
        return v

    def get_class_name(c):
        return get_compact(c, "@id").replace(":", "_")

    def get_comment(obj, indent=0):
        comment = get_prop(
            obj, "http://www.w3.org/2000/01/rdf-schema#comment", "@value"
        )
        if not comment:
            return ""

        return comment

    def get_class_properties(cls):
        nonlocal objects

        props = []
        for prop_id in cls.get("http://www.w3.org/ns/shacl#property", []):
            prop = objects[prop_id["@id"]]
            name = prop["http://www.w3.org/ns/shacl#name"][0]["@value"]
            prop_path = get_prop(
                prop,
                "http://www.w3.org/ns/shacl#path",
                "@id",
            )

            p = {
                "varname": to_var_name(name),
                "path": prop_path,
                "comment": get_comment(objects[prop_path]),
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

            prop_cls = get_prop(prop, "http://www.w3.org/ns/shacl#class", "@id")
            if prop_cls:
                if prop_cls in enum_ids:
                    p["enumname"] = get_class_name(objects[prop_cls])
                else:
                    p["clsname"] = get_class_name(objects[prop_cls])
            else:
                p["datatype"] = get_prop(
                    prop,
                    "http://www.w3.org/ns/shacl#datatype",
                    "@id",
                )

            props.append(p)

        return props

    template_enums = []
    for e in enums:
        values = []
        for v in get_prop(e, "http://www.w3.org/2002/07/owl#oneOf", "@list"):
            values.append(
                {
                    "id": v["@id"],
                    "varname": to_var_name(v["@id"].split("/")[-1]),
                    "comment": get_comment(objects[v["@id"]]),
                }
            )
        values.sort(key=lambda v: v["id"])

        template_enums.append(
            {
                "id": e["@id"],
                "clsname": get_class_name(e),
                "enum_values": values,
                "comment": get_comment(e),
            }
        )
    template_enums.sort(key=lambda e: e["id"])

    done_classes = set()
    template_classes = []
    while classes:
        c = classes.pop(0)

        parents = []
        for p in c.get("http://www.w3.org/2000/01/rdf-schema#subClassOf", []):
            if p["@id"] in objects:
                parents.append(get_class_name(objects[p["@id"]]))

        # If any parent classes of this class are outstanding, then push it
        # back on the end of the class list and try again. This ensures that
        # derived classes are always written after any parent classes
        if not all(p in done_classes for p in parents):
            classes.append(c)
            continue

        clsname = get_class_name(c)
        template_classes.append(
            {
                "id": c["@id"],
                "clsname": clsname,
                "parents": parents,
                "comment": get_comment(c),
                "props": get_class_properties(c),
            }
        )
        done_classes.add(clsname)

    def abort_helper(msg):
        raise TemplateRuntimeError(msg)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    env.globals["abort"] = abort_helper
    template = env.get_template(args.lang + ".j2")

    with args.output.open("w") as f:
        f.write(
            template.render(
                disclaimer=f"This file was automatically generated by {THIS_FILE.name}. DO NOT MANUALLY MODIFY IT",
                enums=template_enums,
                classes=template_classes,
            )
        )


if __name__ == "__main__":
    sys.exit(main())
