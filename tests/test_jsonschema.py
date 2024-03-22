#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import re
import subprocess
import json
import jsonschema
import pytest
from pathlib import Path

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

DATA_DIR = THIS_DIR / "data"
EXPECT_DIR = THIS_DIR / "expect"

TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"

TEST_CONTEXT = THIS_DIR / "data" / "model" / "test-context.json"

SPDX3_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"


@pytest.mark.parametrize(
    "args,expect",
    [
        (
            ["--input", TEST_MODEL],
            "test.json",
        ),
        (
            ["--input", TEST_MODEL, "--context-url", TEST_CONTEXT, SPDX3_CONTEXT_URL],
            "test-context.json",
        ),
    ],
)
class TestOutput:
    def test_generation(self, tmp_path, args, expect):
        """
        Tests that shacl2code generates json schema output that matches the
        expected output
        """
        outfile = tmp_path / "output.json"
        subprocess.run(
            [
                "shacl2code",
                "generate",
            ]
            + args
            + [
                "jsonschema",
                "--output",
                outfile,
            ],
            check=True,
        )

        with (EXPECT_DIR / "jsonschema" / expect).open("r") as expect_f:
            with outfile.open("r") as out_f:
                assert out_f.read() == expect_f.read()

    def test_output_syntax(self, args, expect):
        """
        Checks that the output file is valid json syntax by parsing it with Python
        """
        p = subprocess.run(
            [
                "shacl2code",
                "generate",
            ]
            + args
            + [
                "jsonschema",
                "--output",
                "-",
            ],
            check=True,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )

        json.loads(p.stdout)

    def test_trailing_whitespace(self, args, expect):
        """
        Tests that the generated file does not have trailing whitespace
        """
        p = subprocess.run(
            [
                "shacl2code",
                "generate",
            ]
            + args
            + [
                "jsonschema",
                "--output",
                "-",
            ],
            check=True,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )

        for num, line in enumerate(p.stdout.splitlines()):
            assert (
                re.search(r"\s+$", line) is None
            ), f"Line {num + 1} has trailing whitespace"

    def test_tabs(self, args, expect):
        """
        Tests that the output file doesn't contain tabs
        """
        p = subprocess.run(
            [
                "shacl2code",
                "generate",
            ]
            + args
            + [
                "jsonschema",
                "--output",
                "-",
            ],
            check=True,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )

        for num, line in enumerate(p.stdout.splitlines()):
            assert "\t" not in line, f"Line {num + 1} has tabs"


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


def node_kind_tests(name, blank, iri):
    return [
        (
            blank,
            {
                "@context": CONTEXT,
                "@type": name,
            },
        ),
        (
            blank,
            {
                "@context": CONTEXT,
                "@type": name,
                "@id": "_:blank",
            },
        ),
        (
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
            iri,
            {
                "@context": CONTEXT,
                "@type": name,
                "@id": "http://example.com/name",
            },
        ),
        (
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


@pytest.mark.parametrize(
    "passes,data",
    [
        # Empty graph
        (
            True,
            {
                "@context": CONTEXT,
                "@graph": [],
            },
        ),
        # Missing context
        (
            False,
            {
                "@graph": [],
            },
        ),
        # Bad context
        (
            False,
            {
                "@context": "http://foo.com",
                "@graph": [],
            },
        ),
        # Unknown root field
        (
            False,
            {
                "@context": CONTEXT,
                "@graph": [],
                "foo": "bar",
            },
        ),
        # Minimal with object
        (
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
        # Unknown object field
        (
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
        # Nested base class
        (
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
        # Nested derived class
        (
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
        # Derived class with nested base class
        (
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
        # Derived class with nested derived class
        (
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
        # Link by string
        (
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
        # Bad nested class type
        (
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
        # Pattern test
        (
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
        # Bad pattern
        (
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
        # Bad pattern list
        (
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
        # Empty list
        (
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
        # Required property
        (
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
        # Missing required scalar
        (
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
        # Missing required list
        (
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
        # Short list
        (
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
        # Long list
        (
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
        # Root object
        (
            True,
            {
                "@context": CONTEXT,
                "@type": "test-class",
            },
        ),
        # Root object with unknown field
        (
            False,
            {
                "@context": CONTEXT,
                "@type": "test-class",
                "foo": "bar",
            },
        ),
        # Root object with missing context
        (
            False,
            {
                "@type": "test-class",
            },
        ),
        # Root object with bad context
        (
            False,
            {
                "@context": "http://foo.bar",
                "@type": "test-class",
            },
        ),
        # Root object with unknown type
        (
            False,
            {
                "@context": CONTEXT,
                "@type": "foo",
            },
        ),
        # Node Kind tests
        *node_kind_tests("node-kind-blank", True, False),
        *node_kind_tests("node-kind-iri", False, True),
        *node_kind_tests("node-kind-iri-or-blank", True, True),
        *node_kind_tests("derived-node-kind-iri", False, True),
        # Alternate ID
        (
            True,
            {
                "@context": CONTEXT,
                "@type": "id-prop-class",
                "testid": "_:blank",
            },
        ),
        # @id not allowed for alternate ID classes
        (
            False,
            {
                "@context": CONTEXT,
                "@type": "id-prop-class",
                "@id": "_:blank",
            },
        ),
        # Alternate ID in inherited class
        (
            True,
            {
                "@context": CONTEXT,
                "@type": "inherited-id-prop-class",
                "testid": "_:blank",
            },
        ),
        # @id not allowed for alternate ID classes
        (
            False,
            {
                "@context": CONTEXT,
                "@type": "inherited-id-prop-class",
                "@id": "_:blank",
            },
        ),
        # Base object for type tests
        (True, BASE_OBJ),
    ],
)
def test_schema_validation(test_jsonschema, test_context_url, passes, data):
    replace_context(data, test_context_url)

    if passes:
        jsonschema.validate(data, schema=test_jsonschema)
    else:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, schema=test_jsonschema)


def type_tests(name, *, good=[], bad=[], typ=[]):
    tests = [
        # None is never allowed
        (False, name, None),
        # Empty object is not allowed for a scalar
        (False, name, {}),
    ]

    def lst(v):
        if list in typ:
            return [v]
        return v

    is_list = list in typ
    if is_list:
        # No scalars allowed
        tests.append((False, name, True))
        tests.append((False, name, False))
        tests.append((False, name, 1))
        tests.append((False, name, 1.5))
        tests.append((False, name, "foo"))

        # Empty list is allowed
        tests.append((True, name, []))
    else:
        # Lists not allowed
        tests.append((False, name, []))

    if bool not in typ:
        tests.append((False, name, lst(True)))
        tests.append((False, name, lst(False)))

    if not (int in typ or float in typ):
        tests.append((False, name, lst(1)))

    if float not in typ:
        tests.append((False, name, lst(1.5)))

    if str not in typ:
        tests.append((False, name, lst("foo")))

    for g in good:
        tests.append((True, name, g))

    for b in bad:
        tests.append((False, name, b))

    return tests


@pytest.mark.parametrize(
    "passes,name,val",
    [
        *type_tests(
            "test-class/nonnegative-integer-prop", good=[1, 0], bad=[-1], typ=[int]
        ),
        *type_tests("test-class/integer-prop", good=[1, 0, -1], typ=[int]),
        *type_tests(
            "test-class/float-prop",
            good=[-1.5, 0, 1.5, "1.5", "0.0", "-1.5", "1", "-1"],
            bad=["a1", "a", ""],
            typ=[float],
        ),
        *type_tests(
            "test-class/datetime-scalar-prop",
            good=[
                "2024-03-11T00:00:00+00:00",
                "2024-03-11T00:00:00Z",
                "2024-03-11T00:00:00",
            ],
            bad=["abc"],
            typ=[str],
        ),
        *type_tests(
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
        *type_tests("test-class/string-scalar-prop", good=["foo", ""], typ=[str]),
        *type_tests("test-class/named-property", good=["foo", ""], typ=[str]),
        *type_tests(
            "test-class/enum-prop",
            good=["enumType/foo"],
            bad=["foo"],
            typ=[str],
        ),
        *type_tests(
            "test-class/class-prop",
            good=[
                {"@type": "test-class"},
                {"@type": "test-derived-class"},
                "_:blanknode",
                "http://serialize.example.org/test",
            ],
            bad=[
                {"@type": "test-another-class"},
                {"@type": "parent-class"},
            ],
            typ=[object, str],
        ),
        *type_tests(
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
        *type_tests(
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
        *type_tests(
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
        *type_tests(
            "test-class/string-list-prop",
            good=[["foo", "bar"], [""]],
            typ=[str, list],
        ),
        *type_tests(
            "test-class/datetime-list-prop",
            good=[
                ["2024-03-11T00:00:00Z"],
            ],
            bad=[
                ["abc"],
            ],
            typ=[str, list],
        ),
        *type_tests(
            "test-class/enum-list-prop",
            good=[
                [
                    "enumType/foo",
                    "enumType/bar",
                    "enumType/nolabel",
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
        *type_tests(
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
def test_schema_type_validation(test_jsonschema, test_context_url, passes, name, val):
    data = BASE_OBJ.copy()
    replace_context(data, test_context_url)
    data[name] = val

    if passes:
        jsonschema.validate(data, schema=test_jsonschema)
    else:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, schema=test_jsonschema)
