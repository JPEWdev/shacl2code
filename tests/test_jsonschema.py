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

SPDX3_MODEL = DATA_DIR / "model" / "spdx3.jsonld"

SPDX3_CONTEXT = DATA_DIR / "model" / "spdx3-context.json"
SPDX3_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"

SPDX3_CONTEXT_ARGS = ["--context-url", SPDX3_CONTEXT, SPDX3_CONTEXT_URL]


@pytest.fixture(scope="module")
def test_schema():
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "--context-url",
            TEST_CONTEXT,
            SPDX3_CONTEXT_URL,
            "jsonschema",
            "--output",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    return json.loads(p.stdout)


@pytest.mark.parametrize(
    "args,expect",
    [
        (
            ["--input", SPDX3_MODEL],
            "spdx3.json",
        ),
        (
            ["--input", SPDX3_MODEL, "--context-url", SPDX3_CONTEXT, SPDX3_CONTEXT_URL],
            "spdx3-context.json",
        ),
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


BASE_OBJ = {
    "@context": SPDX3_CONTEXT_URL,
    "@type": "test-class",
}


def ref_tests(name, none, blank, iri, inline):
    return [
        (
            none,
            {
                "@context": SPDX3_CONTEXT_URL,
                "@type": name,
            },
        ),
        (
            none and inline,
            {
                "@context": SPDX3_CONTEXT_URL,
                "@type": "link-class",
                "link-class-prop": {
                    "@type": name,
                },
            },
        ),
        (
            blank,
            {
                "@context": SPDX3_CONTEXT_URL,
                "@type": name,
                "@id": "_:blank",
            },
        ),
        (
            blank and inline,
            {
                "@context": SPDX3_CONTEXT_URL,
                "@type": "link-class",
                "link-class-prop": {
                    "@type": name,
                    "@id": "_:blank",
                },
            },
        ),
        (
            iri,
            {
                "@context": SPDX3_CONTEXT_URL,
                "@type": name,
                "@id": "http://example.com/name",
            },
        ),
        (
            iri and inline,
            {
                "@context": SPDX3_CONTEXT_URL,
                "@type": "link-class",
                "link-class-prop": {
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
                "@context": SPDX3_CONTEXT_URL,
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
                "@context": SPDX3_CONTEXT_URL,
                "@graph": [],
                "foo": "bar",
            },
        ),
        # Minimal with object
        (
            True,
            {
                "@context": SPDX3_CONTEXT_URL,
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
                "@context": SPDX3_CONTEXT_URL,
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
                "@context": SPDX3_CONTEXT_URL,
                "@graph": [
                    {
                        "@type": "link-class",
                        "link-class-prop": {
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
                "@context": SPDX3_CONTEXT_URL,
                "@graph": [
                    {
                        "@type": "link-class",
                        "link-class-prop": {
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
                "@context": SPDX3_CONTEXT_URL,
                "@graph": [
                    {
                        "@type": "link-derived-class",
                        "link-class-prop": {
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
                "@context": SPDX3_CONTEXT_URL,
                "@graph": [
                    {
                        "@type": "link-derived-class",
                        "link-class-prop": {
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
                "@context": SPDX3_CONTEXT_URL,
                "@graph": [
                    {
                        "@type": "link-class",
                        "link-class-prop": "http://serialize.example.org/test",
                    }
                ],
            },
        ),
        # Bad nested class type
        (
            False,
            {
                "@context": SPDX3_CONTEXT_URL,
                "@graph": [
                    {
                        "@type": "link-class",
                        "link-class-prop": {
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
                "@context": SPDX3_CONTEXT_URL,
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
                "@context": SPDX3_CONTEXT_URL,
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
                "@context": SPDX3_CONTEXT_URL,
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
                "@context": SPDX3_CONTEXT_URL,
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
                "@context": SPDX3_CONTEXT_URL,
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
                "@context": SPDX3_CONTEXT_URL,
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
                "@context": SPDX3_CONTEXT_URL,
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
                "@context": SPDX3_CONTEXT_URL,
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
                "@context": SPDX3_CONTEXT_URL,
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
                "@context": SPDX3_CONTEXT_URL,
                "@type": "test-class",
            },
        ),
        # Root object with unknown field
        (
            False,
            {
                "@context": SPDX3_CONTEXT_URL,
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
                "@context": SPDX3_CONTEXT_URL,
                "@type": "foo",
            },
        ),
        # Referenceable tests
        *ref_tests("ref-no-class", True, False, False, True),
        *ref_tests("ref-local-class", True, True, False, True),
        *ref_tests("ref-optional-class", True, True, True, True),
        *ref_tests("ref-yes-class", False, False, True, True),
        *ref_tests("ref-always-class", False, False, True, False),
        # Alternate ID
        (
            True,
            {
                "@context": SPDX3_CONTEXT_URL,
                "@type": "id-prop-class",
                "testid": "_:blank",
            },
        ),
        # @id not allowed for alternate ID classes
        (
            False,
            {
                "@context": SPDX3_CONTEXT_URL,
                "@type": "id-prop-class",
                "@id": "_:blank",
            },
        ),
        # Base object for type tests
        (True, BASE_OBJ),
    ],
)
def test_schema_validation(test_schema, passes, data):
    if passes:
        jsonschema.validate(data, schema=test_schema)
    else:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, schema=test_schema)


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
        *type_tests("test-class/float-prop", good=[-1.5, 0, 1.5], typ=[float]),
        *type_tests(
            "test-class/datetime-scalar-prop",
            good=["2024-03-11T00:00:00Z"],
            bad=["abc"],
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
def test_schema_type_validation(test_schema, passes, name, val):
    data = BASE_OBJ.copy()
    data[name] = val

    if passes:
        jsonschema.validate(data, schema=test_schema)
    else:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, schema=test_schema)
