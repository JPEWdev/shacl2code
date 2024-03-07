#! /usr/bin/env python3
#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import keyword
import re
import typing
from dataclasses import dataclass

from rdflib.namespace import RDF, RDFS, OWL, SH


class ModelException(Exception):
    pass


def to_var_name(name):
    name = str(name).replace("@", "_")
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
    derived_ids: list
    properties: typing.List[Property]
    comment: str = ""


class Model(object):
    def __init__(self, graph, context=None):
        self.model = graph
        self.context = context
        self.compact_ids = {}
        self.objects = {}
        self.enums = []
        self.classes = []
        class_iris = set()
        enum_iris = set()
        classes_by_iri = {}

        for cls_iri in self.model.subjects(RDF.type, OWL.Class):
            enum_values = []

            for value_iri in self.model.subjects(RDF.type, cls_iri):
                if (value_iri, RDF.type, OWL.NamedIndividual) not in self.model:
                    continue

                v = EnumValue(
                    _id=str(value_iri),
                    varname=str(
                        self.model.value(
                            value_iri,
                            RDFS.label,
                            default=to_var_name(str(value_iri).split("/")[-1]),
                        )
                    ),
                    comment=str(self.model.value(value_iri, RDFS.comment, default="")),
                )
                enum_values.append(v)

            if enum_values:
                enum_values.sort(key=lambda v: v._id)

                e = Enum(
                    _id=str(cls_iri),
                    clsname=self.get_class_name(cls_iri),
                    comment=str(self.model.value(cls_iri, RDFS.comment, default="")),
                    values=enum_values,
                )
                self.enums.append(e)
                enum_iris.add(cls_iri)
            else:
                class_iris.add(cls_iri)

        def int_val(v):
            if not v:
                return None
            return int(v)

        for cls_iri in class_iris:
            c = Class(
                _id=str(cls_iri),
                parent_ids=[
                    str(parent_iri)
                    for parent_iri in self.model.objects(cls_iri, RDFS.subClassOf)
                    if parent_iri in class_iris
                ],
                derived_ids=[],
                clsname=self.get_class_name(cls_iri),
                comment=str(self.model.value(cls_iri, RDFS.comment, default="")),
                properties=[],
            )

            for obj_prop in self.model.objects(cls_iri, SH.property):
                prop = self.model.value(obj_prop, SH.path)

                p = Property(
                    varname=to_var_name(
                        self.model.value(
                            prop,
                            SH.name,
                            default=self.get_compact_id(prop),
                        )
                    ),
                    path=str(prop),
                    comment=str(self.model.value(prop, RDFS.comment, default="")),
                    max_count=int_val(self.model.value(obj_prop, SH.maxCount)),
                    min_count=int_val(self.model.value(obj_prop, SH.minCount)),
                )

                range_id = self.model.value(
                    prop,
                    RDFS.range,
                    default=self.model.value(obj_prop, SH.datatype),
                )
                if range_id is None:
                    raise ModelException(f"Prop '{prop}' is missing range")

                if range_id in enum_iris:
                    p.enum_id = str(range_id)

                elif range_id in class_iris:
                    p.class_id = str(range_id)

                else:
                    p.datatype = str(range_id)

                c.properties.append(p)

            self.classes.append(c)
            classes_by_iri[str(cls_iri)] = c

        for c in self.classes:
            for p in c.parent_ids:
                classes_by_iri[p].derived_ids.append(c._id)

        for c in self.classes:
            c.derived_ids.sort()

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

    def get_compact_id(self, _id):
        """
        Returns the "compacted" name of an object, that is the name of the
        object with the context applied
        """
        _id = str(_id)
        if _id not in self.compact_ids:
            self.compact_ids[_id] = self.context.compact(_id)

        return self.compact_ids[_id]

    def get_class_name(self, c):
        """
        Returns the name for a class that should be used in Code
        """
        return to_var_name(self.get_compact_id(c).replace(":", "_"))
