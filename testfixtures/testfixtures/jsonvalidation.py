#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from pathlib import Path

from .utils import parametrize

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
            (
                f"{name} no IRI",
                blank,
                {
                    "@context": CONTEXT,
                    "@type": name,
                },
            ),
            (
                f"{name} blank node",
                blank,
                {
                    "@context": CONTEXT,
                    "@type": name,
                    "@id": "_:blank",
                },
            ),
            (
                f"nested {name} no IRI",
                blank,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": name,
                    },
                },
            ),
            (
                f"nested {name} blank node",
                blank,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": name,
                        "@id": "_:blank",
                    },
                },
            ),
            (
                f"{name} IRI",
                iri,
                {
                    "@context": CONTEXT,
                    "@type": name,
                    "@id": "http://example.com/name",
                },
            ),
            (
                f"nest {name} IRI",
                iri,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": name,
                        "@id": "http://example.com/name",
                    },
                },
            ),
        ]

    return parametrize(
        "passes,data",
        [
            (
                "Empty graph",
                True,
                {
                    "@context": CONTEXT,
                    "@graph": [],
                },
            ),
            (
                "Missing context",
                False,
                {
                    "@graph": [],
                },
            ),
            (
                "Bad context",
                False,
                {
                    "@context": "http://foo.com",
                    "@graph": [],
                },
            ),
            (
                "Unknown root field",
                False,
                {
                    "@context": CONTEXT,
                    "@graph": [],
                    "foo": "bar",
                },
            ),
            (
                "Minimal with object",
                True,
                {
                    "@context": CONTEXT,
                    "@graph": [
                        {
                            "@type": "link-class",
                        }
                    ],
                },
            ),
            (
                "Missing type",
                False,
                {
                    "@context": CONTEXT,
                    "@graph": [{}],
                },
            ),
            (
                "Unknown object field",
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
            ),
            (
                "Nested base class",
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
            ),
            (
                "Nested derived class",
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
            ),
            (
                "Derived class with nested base class",
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
            ),
            (
                "Derived class with nested derived class",
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
            ),
            (
                "Link by string",
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
            ),
            (
                "Bad nested class type",
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
            ),
            (
                "Pattern test",
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
            ),
            (
                "Bad pattern",
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
            ),
            (
                "Bad pattern list",
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
            ),
            (
                "Empty list",
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
            ),
            (
                "Required property",
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
            ),
            (
                "Missing required scalar",
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
            ),
            (
                "Missing required list",
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
            ),
            (
                "Short list",
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
            ),
            (
                "Long list",
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
            ),
            (
                "Root object",
                True,
                {
                    "@context": CONTEXT,
                    "@type": "test-class",
                },
            ),
            (
                "Root object with unknown field",
                False,
                {
                    "@context": CONTEXT,
                    "@type": "test-class",
                    "foo": "bar",
                },
            ),
            (
                "Root object with missing context",
                False,
                {
                    "@type": "test-class",
                },
            ),
            (
                "Root object with missing type",
                False,
                {
                    "@context": CONTEXT,
                },
            ),
            (
                "Root object with bad context",
                False,
                {
                    "@context": "http://foo.bar",
                    "@type": "test-class",
                },
            ),
            (
                "Root object with unknown type",
                False,
                {
                    "@context": CONTEXT,
                    "@type": "foo",
                },
            ),
            *node_kind_tests("node-kind-blank", True, False),
            *node_kind_tests("node-kind-iri", False, True),
            *node_kind_tests("node-kind-iri-or-blank", True, True),
            *node_kind_tests("derived-node-kind-iri", False, True),
            (
                "Alternate ID",
                True,
                {
                    "@context": CONTEXT,
                    "@type": "id-prop-class",
                    "testid": "_:blank",
                },
            ),
            (
                "@id not allowed for alternate ID classes",
                False,
                {
                    "@context": CONTEXT,
                    "@type": "id-prop-class",
                    "@id": "_:blank",
                },
            ),
            (
                "Alternate ID in inherited class",
                True,
                {
                    "@context": CONTEXT,
                    "@type": "inherited-id-prop-class",
                    "testid": "_:blank",
                },
            ),
            (
                "@id not allowed for alternate ID classes",
                False,
                {
                    "@context": CONTEXT,
                    "@type": "inherited-id-prop-class",
                    "@id": "_:blank",
                },
            ),
            (
                "Extensible class",
                True,
                {
                    "@context": CONTEXT,
                    "@type": "extensible-class",
                    "extensible-class/required": "foo",
                    "link-class-link-prop": {
                        "@type": "link-class",
                    },
                },
            ),
            (
                "Extensible class with custom type",
                True,
                {
                    "@context": CONTEXT,
                    "@type": "http://example.com/extended",
                    "extensible-class/required": "foo",
                    "link-class-link-prop": {
                        "@type": "link-class",
                    },
                },
            ),
            (
                "Extensible class with unknown property",
                True,
                {
                    "@context": CONTEXT,
                    "@type": "http://example.com/extended",
                    "extensible-class/required": "foo",
                    "unknown-prop": "foo",
                },
            ),
            (
                "Extensible class with missing required property",
                False,
                {
                    "@context": CONTEXT,
                    "@type": "http://example.com/extended",
                    "unknown-prop": "foo",
                },
            ),
            (
                "Nested extensible class",
                True,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": "extensible-class",
                        "extensible-class/required": "foo",
                    },
                },
            ),
            (
                "Nested extensible class with non-IRI type",
                False,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": "not-an-iri",
                        "extensible-class/required": "foo",
                    },
                },
            ),
            (
                "Nested extensible class with custom type",
                True,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": "http://example.com/extended",
                        "extensible-class/required": "foo",
                    },
                },
            ),
            (
                "Nested extensible class with custom unknown property",
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
            ),
            (
                "Nested extended class with missing required property",
                False,
                {
                    "@context": CONTEXT,
                    "@type": "link-class",
                    "link-class-link-prop": {
                        "@type": "http://example.com/extended",
                    },
                },
            ),
            (
                "Abstract class",
                False,
                {
                    "@context": CONTEXT,
                    "@type": "abstract-class",
                },
            ),
            (
                "Concrete class derived from abstract class",
                True,
                {
                    "@context": CONTEXT,
                    "@type": "concrete-class",
                },
            ),
            (
                "Abstract SPDX style class",
                False,
                {
                    "@context": CONTEXT,
                    "@type": "abstract-spdx-class",
                },
            ),
            (
                "Concrete SPDX style class",
                True,
                {
                    "@context": CONTEXT,
                    "@type": "concrete-spdx-class",
                },
            ),
            (
                "Abstract SH style class",
                False,
                {
                    "@context": CONTEXT,
                    "@type": "abstract-sh-class",
                },
            ),
            (
                "Concrete SH style class",
                True,
                {
                    "@context": CONTEXT,
                    "@type": "concrete-sh-class",
                },
            ),
            (
                "An extensible abstract class cannot be instantiated",
                False,
                {
                    "@context": CONTEXT,
                    "@type": "extensible-abstract-class",
                },
            ),
            # Any can type can be used where a extensible abstract class is
            # references, except... (SEE NEXT)"
            (
                "Any type for extensible",
                True,
                {
                    "@context": CONTEXT,
                    "@type": "uses-extensible-abstract-class",
                    "uses-extensible-abstract-class/prop": {
                        "@type": "http://example.com/extended",
                    },
                },
            ),
            # ... the exact type of the extensible abstract class is specifically
            # not allowed
            (
                "No abstract extensible",
                False,
                {
                    "@context": CONTEXT,
                    "@type": "uses-extensible-abstract-class",
                    "uses-extensible-abstract-class/prop": {
                        "@type": "extensible-abstract-class",
                    },
                },
            ),
            (
                "Base object",
                True,
                BASE_OBJ,
            ),
        ],
    )


def type_tests():
    def create_type_tests(name, *, good=[], bad=[], typ=[]):
        def make_type_test(passes, val):
            data = BASE_OBJ.copy()
            data[name] = val
            tests.append((f"{name} = {val!r}", passes, data))

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

    return parametrize(
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
    return parametrize(
        "filename,name,expect_tag",
        [
            (
                "links to self",
                DATA_DIR / "links.json",
                "http://serialize.example.com/self",
                "self",
            ),
            (
                "links to self from derived class",
                DATA_DIR / "links.json",
                "http://serialize.example.com/self-derived",
                "self-derived",
            ),
            (
                "links to derived class from base class",
                DATA_DIR / "links.json",
                "http://serialize.example.com/base-to-derived",
                "self-derived",
            ),
            (
                "links to base class from derived class",
                DATA_DIR / "links.json",
                "http://serialize.example.com/derived-to-base",
                "self",
            ),
            (
                "links to blank node base",
                DATA_DIR / "links.json",
                "http://serialize.example.com/base-to-blank-base",
                "blank-base",
            ),
            (
                "links to blank node derived",
                DATA_DIR / "links.json",
                "http://serialize.example.com/base-to-blank-derived",
                "blank-derived",
            ),
            (
                "links to blank node base from derived class",
                DATA_DIR / "links.json",
                "http://serialize.example.com/derived-to-blank-base",
                "blank-base",
            ),
            (
                "links to blank node derived from derived class",
                DATA_DIR / "links.json",
                "http://serialize.example.com/derived-to-blank-derived",
                "blank-derived",
            ),
        ],
    )
