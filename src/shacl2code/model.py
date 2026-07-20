#! /usr/bin/env python3
#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT
"""SHACL model parsing and data class definitions"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from rdflib import URIRef
from rdflib.namespace import (
    DefinedNamespace,
    Namespace,
    OWL,
    RDF,
    RDFS,
    SH,
    XSD,
)

from .util import convert_version_string

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
    isPreRelease: URIRef

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
class Ontology:
    _id: str
    name: str
    comment: str = ""
    label: str = ""
    version: str = ""
    is_prerelease: bool = False


@dataclass
class Individual:
    _id: str
    varname: str
    comment: str = ""
    ontology: Optional[Ontology] = None


@dataclass
class Property:
    path: str
    varname: str
    comment: str = ""
    max_count: Optional[int] = None
    min_count: Optional[int] = None
    enum_values: List[str] = field(default_factory=list)
    class_id: str = ""
    datatype: str = ""
    pattern: str = ""
    deprecated: bool = False


@dataclass
class Class:
    _id: str
    clsname: str
    parent_ids: List[str]
    derived_ids: List[str]
    properties: List[Property]
    comment: str = ""
    id_property: str = ""
    node_kind: Optional[str] = None
    is_extensible: bool = False
    is_abstract: bool = False
    named_individuals: Optional[List[Individual]] = None
    deprecated: bool = False
    ontology: Optional[Ontology] = None


class Model(object):
    def __init__(self, graph, context=None, is_prerelease=None):
        self.model = graph
        self.context = context
        self.compact_ids = {}
        self.objects = {}
        self.classes = []
        self.ontologies = []
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

        def get_ontology(_id):
            for o in self.ontologies:
                if str(_id).startswith(o._id):
                    return o
            return None

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
                        ontology=get_ontology(member_iri),
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

        def is_semver_prerelease(version_str):
            # Only treat a hyphen as a semver pre-release marker when it
            # directly follows a dotted numeric core (e.g. "1.2.3-beta"),
            # not e.g. a date-like version such as "2024-01-15".
            if re.match(r"^\d+\.\d+(?:\.\d+)?-[0-9A-Za-z]", version_str):
                return True
            if re.search(
                r"\b(alpha|beta|dev|pre|rc|snapshot|test)\b", version_str, re.IGNORECASE
            ):
                return True
            return False

        def get_is_prerelease(onto_iri):
            # 1) --pre-release command line option
            if is_prerelease is not None:
                return is_prerelease

            # 2) sh-to-code:isPreRelease
            val = self.model.value(onto_iri, SHACL2CODE.isPreRelease)
            if val is not None:
                return bool(val)

            adms_statuses = list(
                self.model.objects(onto_iri, URIRef("http://www.w3.org/ns/adms#status"))
            )
            if adms_statuses:
                semic = [
                    str(s)
                    for s in adms_statuses
                    if str(s).startswith(
                        "http://publications.europa.eu/resource/authority/dataset-status/"
                    )
                ]
                # 3) adms:status (EU SEMIC vocab)
                if semic:
                    return any(
                        s
                        == "http://publications.europa.eu/resource/authority/dataset-status/DEVELOP"
                        for s in semic
                    )
                original = [
                    str(s)
                    for s in adms_statuses
                    if str(s).startswith("http://purl.org/adms/status/")
                ]
                # 4) adms:status (Original ADMS vocab)
                if original:
                    return any(
                        s == "http://purl.org/adms/status/UnderDevelopment"
                        for s in original
                    )

            # 5) bibo:status (Bibliographic Ontology)
            bibo_statuses = list(
                self.model.objects(
                    onto_iri, URIRef("http://purl.org/ontology/bibo/status")
                )
            )
            if bibo_statuses:
                return any(
                    str(s) == "http://purl.org/ontology/bibo/status/draft"
                    for s in bibo_statuses
                )

            # 6) schema:creativeWorkStatus
            schema_statuses = list(
                self.model.objects(
                    onto_iri, URIRef("http://schema.org/creativeWorkStatus")
                )
            ) or list(
                self.model.objects(
                    onto_iri, URIRef("https://schema.org/creativeWorkStatus")
                )
            )
            if schema_statuses:
                return any(str(s) in ("Draft", "Incomplete") for s in schema_statuses)

            # 7) vs:term_status
            vs_statuses = list(
                self.model.objects(
                    onto_iri,
                    URIRef("http://www.w3.org/2003/06/sw-vocab-status/ns#term_status"),
                )
            )
            if vs_statuses:
                return any(str(s) in ("unstable", "testing") for s in vs_statuses)

            # 8) & 9) owl:versionInfo
            versions = list(self.model.objects(onto_iri, OWL.versionInfo))
            if versions:
                for version in versions:
                    version_str = str(version)
                    # 8) owl:versionInfo (pre-release extension e.g., "-beta", "-alpha", "-rc" etc)
                    if is_semver_prerelease(version_str):
                        return True
                    # 9) owl:versionInfo (major version zero)
                    parts = convert_version_string(version_str)
                    if parts and parts[0] == 0:
                        return True
                return False

            return False

        for onto_iri in self.model.subjects(RDF.type, OWL.Ontology):
            label = str(self.model.value(onto_iri, RDFS.label, default=""))
            o = Ontology(
                _id=str(onto_iri),
                name=label or str(onto_iri),
                label=label,
                comment=str(self.model.value(onto_iri, RDFS.comment, default="")),
                version=str(self.model.value(onto_iri, OWL.versionInfo, default="")),
                is_prerelease=get_is_prerelease(onto_iri),
            )
            self.ontologies.append(o)

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
                ontology=get_ontology(cls_iri),
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

                varname = self.model.value(
                    obj_prop,
                    SH.name,
                    default=self.get_compact_id(
                        prop,
                        fallback=remove_common_prefix(prop, cls_iri).lstrip("/"),
                    ),
                )

                for p in c.properties:
                    if p.path == str(prop):
                        break
                else:
                    p = Property(
                        varname=varname,
                        path=str(prop),
                        comment=str(self.model.value(prop, RDFS.comment, default="")),
                        deprecated=(prop, RDF.type, OWL.DeprecatedProperty)
                        in self.model,
                    )
                    c.properties.append(p)

                if varname < p.varname:
                    p.varname = varname

                if (v := int_val(self.model.value(obj_prop, SH.maxCount))) is not None:
                    p.max_count = v

                if (v := int_val(self.model.value(obj_prop, SH.minCount))) is not None:
                    p.min_count = v

                if in_list := self.model.value(obj_prop, SH["in"]):
                    enum_values = set(p.enum_values) | set(self.model.items(in_list))
                    p.enum_values = sorted(list(enum_values))

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

            c.properties.sort(key=lambda p: p.path)

            self.classes.append(c)
            classes_by_iri[str(cls_iri)] = c

        for c in self.classes:
            for p in c.parent_ids:
                classes_by_iri[p].derived_ids.append(c._id)

        for c in self.classes:
            c.derived_ids.sort()

        self.classes.sort(key=lambda c: c._id)
        self.ontologies.sort(key=lambda o: o._id)

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
        if not self.context:
            return _id
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
