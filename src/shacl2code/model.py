#! /usr/bin/env python3
#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import typing
from dataclasses import dataclass

from rdflib import URIRef
from rdflib.namespace import RDF, RDFS, OWL, SH, XSD, DefinedNamespace, Namespace

PATTERN_DATATYPES = [
    str(XSD.string),
    str(XSD.dateTime),
    str(XSD.dateTimeStamp),
    str(XSD.anyURI),
]


class SHACL2CODE(DefinedNamespace):
    idPropertyName: URIRef
    isExtensible: URIRef
    isAbstract: URIRef

    _NS = Namespace("https://jpewdev.github.io/shacl2code/schema#")


class ModelException(Exception):
    pass


def common_prefix(*s):
    if not s:
        return ""

    if len(s) == 1:
        return s[0]

    p1 = common_prefix(*s[: len(s) // 2])
    p2 = common_prefix(*s[len(s) // 2 :])
    for idx in range(len(p1)):
        if idx >= len(p2):
            return p2

        if p1[idx] != p2[idx]:
            return p2[:idx]

    return p1


def remove_common_prefix(val, *cmp):
    prefix = common_prefix(val, *cmp)
    return val[len(prefix) :]


@dataclass
class Individual:
    _id: str
    varname: str
    comment: str = ""


@dataclass
class Property:
    path: str
    varname: str
    comment: str = ""
    max_count: int = None
    min_count: int = None
    enum_values: list = None
    class_id: str = ""
    datatype: str = ""
    pattern: str = ""
    deprecated: bool = False


@dataclass
class Class:
    _id: str
    clsname: str
    parent_ids: typing.List[str]
    derived_ids: list
    properties: typing.List[Property]
    comment: str = ""
    id_property: str = ""
    node_kind: str = None
    is_extensible: bool = False
    is_abstract: bool = False
    named_individuals: list = None
    deprecated: bool = False


class Model(object):
    def __init__(self, graph, context=None):
        self.model = graph
        self.context = context
        self.compact_ids = {}
        self.objects = {}
        self.enums = []
        self.classes = []
        class_iris = set()
        classes_by_iri = {}

        def int_val(v):
            if not v:
                return None
            return int(v)

        def str_val(v):
            if v is None:
                return v
            return str(v)

        def get_inherited_value(subject, predicate, default=None):
            def get_value(subject, predicate):
                value = self.model.value(subject, predicate)
                if value is not None:
                    return value

                for parent in self.model.objects(subject, RDFS.subClassOf):
                    value = get_value(parent, predicate)
                    if value is not None:
                        return value

                return None

            value = get_value(subject, predicate)
            if value is not None:
                return value
            return default

        def set_prop_range(p, range_id):
            if range_id in class_iris:
                p.class_id = str(range_id)
                return True

            return False

        def get_named_individuals(cls_iri):
            members = []
            for member_iri in self.model.subjects(RDF.type, cls_iri):
                if (member_iri, RDF.type, OWL.NamedIndividual) not in self.model:
                    continue

                members.append(
                    Individual(
                        _id=str(member_iri),
                        varname=remove_common_prefix(member_iri, cls_iri).lstrip("/"),
                        comment=str(
                            self.model.value(member_iri, RDFS.comment, default="")
                        ),
                    )
                )
            members.sort(key=lambda i: i._id)
            return members

        def is_abstract(s):
            if (
                s,
                RDF.type,
                URIRef("http://spdx.invalid./AbstractClass"),
            ) in self.model:
                return True

            if bool(self.model.value(s, SHACL2CODE.isAbstract, default=False)):
                return True

            return False

        class_iris = set(self.model.subjects(RDF.type, OWL.Class)) | set(
            self.model.subjects(RDF.type, OWL.DeprecatedClass)
        )
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
                id_property=str_val(
                    get_inherited_value(cls_iri, SHACL2CODE.idPropertyName)
                ),
                node_kind=get_inherited_value(cls_iri, SH.nodeKind, SH.BlankNodeOrIRI),
                is_extensible=bool(self.model.value(cls_iri, SHACL2CODE.isExtensible)),
                is_abstract=is_abstract(cls_iri),
                named_individuals=get_named_individuals(cls_iri),
                deprecated=(cls_iri, RDF.type, OWL.DeprecatedClass) in self.model,
            )

            if c.node_kind not in (SH.IRI, SH.BlankNode, SH.BlankNodeOrIRI):
                raise ModelException(
                    f"Class {c._id} has unsupported '{SH.nodeKind}' value '{c.node_kind}'"
                )

            for obj_prop in self.model.objects(cls_iri, SH.property):
                prop = self.model.value(obj_prop, SH.path)
                if prop == RDF.type:
                    for n in self.model.objects(obj_prop, SH["not"]):
                        if (n, SH.hasValue, cls_iri) in self.model:
                            c.is_abstract = True
                    continue

                p = Property(
                    varname=self.model.value(
                        obj_prop,
                        SH.name,
                        default=self.get_compact_id(
                            prop,
                            fallback=remove_common_prefix(prop, cls_iri).lstrip("/"),
                        ),
                    ),
                    path=str(prop),
                    comment=str(self.model.value(prop, RDFS.comment, default="")),
                    max_count=int_val(self.model.value(obj_prop, SH.maxCount)),
                    min_count=int_val(self.model.value(obj_prop, SH.minCount)),
                    deprecated=(prop, RDF.type, OWL.DeprecatedProperty) in self.model,
                )

                if in_list := self.model.value(obj_prop, SH["in"]):
                    p.enum_values = sorted(tuple(self.model.items(in_list)))

                if range_id := self.model.value(obj_prop, SH["class"]):
                    if not set_prop_range(p, range_id):
                        raise ModelException(
                            f"Prop {prop} has unknown class restriction {range_id}"
                        )

                elif range_id := self.model.value(obj_prop, SH.datatype):
                    p.datatype = str(range_id)

                elif range_id := self.model.value(prop, RDFS.range):
                    if not set_prop_range(p, range_id):
                        p.datatype = str(range_id)

                else:
                    raise ModelException(f"Prop '{prop}' is missing range")

                if pattern := self.model.value(obj_prop, SH.pattern):
                    if not p.datatype:
                        raise ModelException(
                            f"Property '{prop}' is not a datatype and may not have a pattern"
                        )
                    if p.datatype not in PATTERN_DATATYPES:
                        raise ModelException(
                            f"Property '{prop}' of type '{p.datatype}' cannot have a pattern. Must be one of type {' '.join(PATTERN_DATATYPES)}"
                        )
                    p.pattern = str(pattern)

                c.properties.append(p)

            c.properties.sort(key=lambda p: p.path)

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

    def get_compact_id(self, _id, *, fallback=None):
        """
        Returns the "compacted" name of an object, that is the name of the
        object with the context applied
        """
        _id = str(_id)
        if _id not in self.compact_ids:
            self.compact_ids[_id] = self.context.compact_iri(_id)

        if self.compact_ids[_id] == _id and fallback is not None:
            return fallback
        return self.compact_ids[_id]

    def get_class_name(self, c):
        """
        Returns the name for a class that should be used in Code
        """
        return self.get_compact_id(c).split(":")
