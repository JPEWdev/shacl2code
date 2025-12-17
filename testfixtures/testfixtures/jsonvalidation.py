#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import pytest
from pathlib import Path
from pytest import param

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

DATA_DIR = THIS_DIR.parent.parent / "tests" / "data"

CONTEXT = object()


def replace_context(d, url):
    for k, v in d.items():
        if v is CONTEXT:
            d[k] = url
        elif isinstance(v, dict):
            replace_context(v, url)


BASE_OBJ = {
    "@context": CONTEXT,
    "@type": "test-class",
}


def validation_tests():
    def node_kind_tests(name, blank, iri):
        return [
            param(
                blank,
                {
                    "@context": CONTEXT,
                    "@type": name,
                },
                id=f"{name} no IRI",
            ),
            param(
                blank,
                {
                    "@context": CONTEXT,
                    "@type": name,
                    "@id": "_:blank",
                },
                id=f"{name} blank node",
            ),
            param(
                blank,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": name,
                    },
                },
                id=f"nested {name} no IRI",
            ),
            param(
                blank,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": name,
                        "@id": "_:blank",
                    },
                },
                id=f"nested {name} blank node",
            ),
            param(
                iri,
                {
                    "@context": CONTEXT,
                    "@type": name,
                    "@id": "http://example.com/name",
                },
                id=f"{name} IRI",
            ),
            param(
                iri,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": name,
                        "@id": "http://example.com/name",
                    },
                },
                id=f"nest {name} IRI",
            ),
        ]

    return pytest.mark.parametrize(
        "passes,data",
        [
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@graph": [],
                },
                id="Empty graph",
            ),
            param(
                False,
                {
                    "@graph": [],
                },
                id="Missing context",
            ),
            param(
                False,
                {
                    "@context": "http://foo.com",
                    "@graph": [],
                },
                id="Bad context",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@graph": [],
                    "foo": "bar",
                },
                id="Unknown root field",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "link-class",
                        }
                    ],
                },
                id="Minimal with object",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@graph": [{}],
                },
                id="Missing type",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "link-class",
                            "foo": "bar",
                        }
                    ],
                },
                id="Unknown object field",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "link-class",
                            "link-class-link-prop": {
                                "@type": "link-class",
                            },
                        }
                    ],
                },
                id="Nested base class",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "link-class",
                            "link-class-link-prop": {
                                "@type": "link-derived-class",
                            },
                        }
                    ],
                },
                id="Nested derived class",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "link-derived-class",
                            "link-class-link-prop": {
                                "@type": "link-class",
                            },
                        }
                    ],
                },
                id="Derived class with nested base class",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "link-derived-class",
                            "link-class-link-prop": {
                                "@type": "link-derived-class",
                            },
                        }
                    ],
                },
                id="Derived class with nested derived class",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "link-class",
                            "link-class-link-prop": "http://serialize.example.org/test",
                        }
                    ],
                },
                id="Link by string",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "link-class",
                            "link-class-link-prop": {
                                "@type": "test-another-class",
                            },
                        }
                    ],
                },
                id="Bad nested class type",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "test-class",
                            "test-class/regex": "foo1",
                            "test-class/regex-list": ["foo1", "foo2"],
                        }
                    ],
                },
                id="Pattern test",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "test-class",
                            "test-class/regex": "fooa",
                        }
                    ],
                },
                id="Bad pattern",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "test-class",
                            "test-class/regex-list": ["fooa"],
                        }
                    ],
                },
                id="Bad pattern list",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "test-class",
                            "test-class/string-list-prop": [],
                        }
                    ],
                },
                id="Empty list",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "test-class-required",
                            "test-class/required-string-scalar-prop": "hello",
                            "test-class/required-string-list-prop": ["hello", "world"],
                        }
                    ],
                },
                id="Required property",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "test-class-required",
                            "test-class/required-string-list-prop": ["hello", "world"],
                        }
                    ],
                },
                id="Missing required scalar",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "test-class-required",
                            "test-class/required-string-scalar-prop": "hello",
                        }
                    ],
                },
                id="Missing required list",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "test-class-required",
                            "test-class/required-string-scalar-prop": "hello",
                            "test-class/required-string-list-prop": [],
                        }
                    ],
                },
                id="Short list",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "test-class-required",
                            "test-class/required-string-scalar-prop": "hello",
                            "test-class/required-string-list-prop": [
                                "hello",
                                "world",
                                "too long",
                            ],
                        }
                    ],
                },
                id="Long list",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@type": "test-class",
                },
                id="Root object",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@type": "test-class",
                    "foo": "bar",
                },
                id="Root object with unknown field",
            ),
            param(
                False,
                {
                    "@type": "test-class",
                },
                id="Root object with missing context",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                },
                id="Root object with missing type",
            ),
            param(
                False,
                {
                    "@context": "http://foo.bar",
                    "@type": "test-class",
                },
                id="Root object with bad context",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@type": "foo",
                },
                id="Root object with unknown type",
            ),
            *node_kind_tests("node-kind-blank", True, False),
            *node_kind_tests("node-kind-iri", False, True),
            *node_kind_tests("node-kind-iri-or-blank", True, True),
            *node_kind_tests("derived-node-kind-iri", False, True),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@type": "id-prop-class",
                    "testid": "_:blank",
                },
                id="Alternate ID",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@type": "id-prop-class",
                    "@id": "_:blank",
                },
                id="@id not allowed for alternate ID classes",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@type": "inherited-id-prop-class",
                    "testid": "_:blank",
                },
                id="Alternate ID in inherited class",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@type": "inherited-id-prop-class",
                    "@id": "_:blank",
                },
                id="@id not allowed for alternate ID classes",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@type": "extensible-class",
                    "extensible-class/required": "foo",
                    "link-class-link-prop": {
                        "@type": "link-class",
                    },
                },
                id="Extensible class",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@type": "http://example.com/extended",
                    "extensible-class/required": "foo",
                    "link-class-link-prop": {
                        "@type": "link-class",
                    },
                },
                id="Extensible class with custom type",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@type": "http://example.com/extended",
                    "extensible-class/required": "foo",
                    "unknown-prop": "foo",
                },
                id="Extensible class with unknown property",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@type": "http://example.com/extended",
                    "unknown-prop": "foo",
                },
                id="Extensible class with missing required property",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": "extensible-class",
                        "extensible-class/required": "foo",
                    },
                },
                id="Nested extensible class",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": "not-an-iri",
                        "extensible-class/required": "foo",
                    },
                },
                id="Nested extensible class with non-IRI type",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": "http://example.com/extended",
                        "extensible-class/required": "foo",
                    },
                },
                id="Nested extensible class with custom type",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": "http://example.com/extended",
                        "extensible-class/required": "foo",
                        "unknown-prop": "foo",
                    },
                },
                id="Nested extensible class with custom unknown property",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": "http://example.com/extended",
                    },
                },
                id="Nested extended class with missing required property",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@type": "abstract-class",
                },
                id="Abstract class",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@type": "concrete-class",
                },
                id="Concrete class derived from abstract class",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@type": "abstract-spdx-class",
                },
                id="Abstract SPDX style class",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@type": "concrete-spdx-class",
                },
                id="Concrete SPDX style class",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@type": "abstract-sh-class",
                },
                id="Abstract SH style class",
            ),
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@type": "concrete-sh-class",
                },
                id="Concrete SH style class",
            ),
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@type": "extensible-abstract-class",
                },
                id="An extensible abstract class cannot be instantiated",
            ),
            # Any can type can be used where a extensible abstract class is
            # references, except... (SEE NEXT)"
            param(
                True,
                {
                    "@context": CONTEXT,
                    "@type": "uses-extensible-abstract-class",
                    "uses-extensible-abstract-class/prop": {
                        "@type": "http://example.com/extended",
                    },
                },
                id="Any type for extensible",
            ),
            # ... the exact type of the extensible abstract class is specifically
            # not allowed
            param(
                False,
                {
                    "@context": CONTEXT,
                    "@type": "uses-extensible-abstract-class",
                    "uses-extensible-abstract-class/prop": {
                        "@type": "extensible-abstract-class",
                    },
                },
                id="No abstract extensible",
            ),
            param(
                True,
                BASE_OBJ,
                id="Base object",
            ),
        ],
    )


def type_tests():
    def create_type_tests(name, *, good=[], bad=[], typ=[]):
        def make_type_test(passes, val):
            data = BASE_OBJ.copy()
            data[name] = val
            tests.append(param(passes, data, id=f"{name} = {val!r}"))

        tests = []
        # None is never allowed
        make_type_test(False, None)
        # Empty object is not allowed for a scalar
        make_type_test(False, {})

        def lst(v):
            if list in typ:
                return [v]
            return v

        is_list = list in typ
        if is_list:
            # No scalars allowed
            make_type_test(False, True)
            make_type_test(False, False)
            make_type_test(False, 1)
            make_type_test(False, 1.5)
            make_type_test(False, "foo")

            # Empty list is allowed
            make_type_test(True, [])
        else:
            # Lists not allowed
            make_type_test(False, [])

        if bool not in typ:
            make_type_test(False, lst(True))
            make_type_test(False, lst(False))

        if not (int in typ or float in typ):
            make_type_test(False, lst(1))

        if float not in typ:
            make_type_test(False, lst(1.5))

        if str not in typ:
            make_type_test(False, lst("foo"))

        for g in good:
            make_type_test(True, g)

        for b in bad:
            make_type_test(False, b)

        return tests

    return pytest.mark.parametrize(
        "passes,data",
        [
            *create_type_tests(
                "test-class/nonnegative-integer-prop",
                good=[1, 0],
                bad=[-1],
                typ=[int],
            ),
            *create_type_tests("test-class/integer-prop", good=[1, 0, -1], typ=[int]),
            *create_type_tests(
                "test-class/float-prop",
                good=[-1.5, 0, 1.5, "1.5", "0.0", "-1.5", "1", "-1"],
                bad=["a1", "a", ""],
                typ=[float],
            ),
            *create_type_tests(
                "test-class/datetime-scalar-prop",
                good=[
                    "2024-03-11T00:00:00+00:00",
                    "2024-03-11T00:00:00Z",
                    "2024-03-11T00:00:00",
                ],
                bad=["abc"],
                typ=[str],
            ),
            *create_type_tests(
                "test-class/datetimestamp-scalar-prop",
                good=[
                    "2024-03-11T00:00:00+00:00",
                    "2024-03-11T00:00:00Z",
                ],
                bad=[
                    "abc",
                    "2024-03-11T00:00:00",
                ],
                typ=[str],
            ),
            *create_type_tests(
                "test-class/string-scalar-prop", good=["foo", ""], typ=[str]
            ),
            *create_type_tests(
                "test-class/named-property", good=["foo", ""], typ=[str]
            ),
            *create_type_tests(
                "test-class/enum-prop",
                good=["foo"],
                bad=["enumType/foo"],
                typ=[str],
            ),
            *create_type_tests(
                "test-class/class-prop",
                good=[
                    {"@type": "test-class"},
                    {"@type": "test-derived-class"},
                    "_:blanknode",
                    "http://serialize.example.org/test",
                    # Named individual
                    "named",
                ],
                bad=[
                    {"@type": "test-another-class"},
                    {"@type": "parent-class"},
                    "not/an/iri",
                    "not-an-iri",
                ],
                typ=[object, str],
            ),
            *create_type_tests(
                "test-class/regex",
                good=[
                    "foo1",
                    "foo2",
                    "foo2a",
                ],
                bad=[
                    "bar",
                    "fooa",
                    "afoo1",
                ],
                typ=[str],
            ),
            *create_type_tests(
                "test-class/regex-datetime",
                good=[
                    "2024-03-11T00:00:00+01:00",
                ],
                bad=[
                    "2024-03-11T00:00:00+1:00",
                    "2024-03-11T00:00:00+00:00",
                    "2024-03-11T00:00:00",
                    "2024-03-11T00:00:00Z",
                ],
                typ=[],
            ),
            *create_type_tests(
                "test-class/regex-datetimestamp",
                good=[
                    "2024-03-11T00:00:00Z",
                ],
                bad=[
                    "2024-03-11T00:00:00",
                    "2024-03-11T00:00:00+1:00",
                    "2024-03-11T00:00:00+00:00",
                ],
                typ=[],
            ),
            *create_type_tests(
                "test-class/string-list-prop",
                good=[["foo", "bar"], [""]],
                typ=[str, list],
            ),
            *create_type_tests(
                "test-class/datetime-list-prop",
                good=[
                    ["2024-03-11T00:00:00Z"],
                ],
                bad=[
                    ["abc"],
                ],
                typ=[str, list],
            ),
            *create_type_tests(
                "test-class/enum-list-prop",
                good=[
                    [
                        "foo",
                        "bar",
                        "nolabel",
                    ]
                ],
                bad=[
                    [
                        "enumType/foo",
                        "foo",
                    ]
                ],
                typ=[str, list],
            ),
            *create_type_tests(
                "test-class/class-list-prop",
                good=[
                    [
                        {"@type": "test-class"},
                        {"@type": "test-derived-class"},
                        "_:blanknode",
                        "http://serialize.example.org/test",
                    ]
                ],
                bad=[
                    [{"@type": "test-another-class"}],
                    [{"@type": "parent-class"}],
                ],
                typ=[object, str, list],
            ),
        ],
    )


def link_tests():
    return pytest.mark.parametrize(
        "filename,name,expect_tag",
        [
            param(
                DATA_DIR / "links.json",
                "http://serialize.example.com/self",
                "self",
                id="links to self",
            ),
            param(
                DATA_DIR / "links.json",
                "http://serialize.example.com/self-derived",
                "self-derived",
                id="links to self from derived class",
            ),
            param(
                DATA_DIR / "links.json",
                "http://serialize.example.com/base-to-derived",
                "self-derived",
                id="links to derived class from base class",
            ),
            param(
                DATA_DIR / "links.json",
                "http://serialize.example.com/derived-to-base",
                "self",
                id="links to base class from derived class",
            ),
            param(
                DATA_DIR / "links.json",
                "http://serialize.example.com/base-to-blank-base",
                "blank-base",
                id="links to blank node base",
            ),
            param(
                DATA_DIR / "links.json",
                "http://serialize.example.com/base-to-blank-derived",
                "blank-derived",
                id="links to blank node derived",
            ),
            param(
                DATA_DIR / "links.json",
                "http://serialize.example.com/derived-to-blank-base",
                "blank-base",
                id="links to blank node base from derived class",
            ),
            param(
                DATA_DIR / "links.json",
                "http://serialize.example.com/derived-to-blank-derived",
                "blank-derived",
                id="links to blank node derived from derived class",
            ),
        ],
    )
