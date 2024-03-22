#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import hashlib
import json
import jsonschema
import pyshacl
import pytest
import rdflib
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

EXPECT_DIR = THIS_DIR / "expect"
DATA_DIR = THIS_DIR / "data"

TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"

TEST_CONTEXT = THIS_DIR / "data" / "model" / "test-context.json"

SPDX3_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"


class ObjectSet(object):
    def __init__(self, objects, object_ids):
        self.objects = objects
        self.object_ids = object_ids

    def get_obj(self, _id, typ):
        o = self.object_ids.get(_id, None)
        assert o is not None, f"Unable to find {_id}"
        assert isinstance(
            o, typ
        ), f"Object {_id} has wrong type {type(o)}. Expected {typ}"
        return o


@pytest.fixture(scope="session")
def roundtrip(tmp_path_factory, model_server):
    outfile = tmp_path_factory.mktemp("python-roundtrip") / "roundtrip.json"
    with (DATA_DIR / "python" / "roundtrip.json").open("r") as f:
        data = f.read()

    data = data.replace("@CONTEXT_URL@", model_server + "/test-context.json")

    with outfile.open("w") as f:
        f.write(data)

    yield outfile


@pytest.fixture(scope="module")
def test_context(tmp_path_factory, model_server):
    tmp_directory = tmp_path_factory.mktemp("pythontestcontext")
    outfile = tmp_directory / "model.py"
    subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "--context",
            model_server + "/test-context.json",
            "python",
            "--output",
            outfile,
        ],
        check=True,
    )
    outfile.chmod(0o755)
    yield (tmp_directory, outfile)


@pytest.fixture(scope="module")
def test_script(test_context):
    _, script = test_context
    yield script


@pytest.fixture(scope="module")
def import_test_context(test_context):
    tmp_directory, _ = test_context

    old_path = sys.path[:]
    sys.path.append(str(tmp_directory))
    try:
        yield
    finally:
        sys.path = old_path


@pytest.mark.parametrize(
    "args,expect",
    [
        (
            ["--input", TEST_MODEL],
            "test.py",
        ),
        (
            ["--input", TEST_MODEL, "--context-url", TEST_CONTEXT, SPDX3_CONTEXT_URL],
            "test-context.py",
        ),
    ],
)
class TestOutput:
    def test_generation(self, tmp_path, args, expect):
        """
        Tests that shacl2code generates python output that matches the expected
        output
        """
        outfile = tmp_path / "output.py"
        subprocess.run(
            [
                "shacl2code",
                "generate",
            ]
            + args
            + [
                "python",
                "--output",
                outfile,
            ],
            check=True,
        )

        with (EXPECT_DIR / "python" / expect).open("r") as expect_f:
            with outfile.open("r") as out_f:
                assert out_f.read() == expect_f.read()

    def test_output_syntax(self, tmp_path, args, expect):
        """
        Checks that the output file is valid python syntax by executing it"
        """
        outfile = tmp_path / "output.py"
        subprocess.run(
            [
                "shacl2code",
                "generate",
            ]
            + args
            + [
                "python",
                "--output",
                outfile,
            ],
            check=True,
        )

        subprocess.run([sys.executable, outfile, "--help"], check=True)

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
                "python",
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
                "python",
                "--output",
                "-",
            ],
            check=True,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )

        for num, line in enumerate(p.stdout.splitlines()):
            assert "\t" not in line, f"Line {num + 1} has tabs"


def test_roundtrip(import_test_context, tmp_path, roundtrip):
    import model

    def check_file(p, expect, digest):
        sha1 = hashlib.sha1()
        with p.open("rb") as f:
            while True:
                d = f.read(4096)
                if not d:
                    break
                sha1.update(d)

        assert sha1.hexdigest() == digest

        with p.open("r") as f:
            data = json.load(f)

        assert data == expect

    with roundtrip.open("r") as f:
        d = model.JSONLDDeserializer()
        objects, _ = d.read(f)

    with roundtrip.open("r") as f:
        expect_data = json.load(f)

    outfile = tmp_path / "out.json"
    with outfile.open("wb") as f:
        s = model.JSONLDSerializer()
        digest = s.write(objects, f, indent=4)

    check_file(outfile, expect_data, digest)

    with outfile.open("wb") as f:
        s = model.JSONLDInlineSerializer()
        digest = s.write(objects, f)

    check_file(outfile, expect_data, digest)


def test_script_roundtrip(test_script, tmp_path, roundtrip):
    outpath = tmp_path / "out.json"

    subprocess.run(
        [test_script, roundtrip, "--outfile", outpath],
        check=True,
    )

    with roundtrip.open("r") as f:
        expect_data = json.load(f)

    with outpath.open("r") as f:
        data = json.load(f)

    assert data == expect_data


def test_jsonschema_validation(roundtrip, test_jsonschema):
    with roundtrip.open("r") as f:
        data = json.load(f)

    jsonschema.validate(data, schema=test_jsonschema)


@pytest.mark.parametrize(
    "name,expect",
    [
        (
            "http://serialize.example.com/self",
            "http://serialize.example.com/self",
        ),
        (
            "http://serialize.example.com/self-derived",
            "http://serialize.example.com/self-derived",
        ),
        (
            "http://serialize.example.com/base-to-derived",
            "http://serialize.example.com/self-derived",
        ),
        (
            "http://serialize.example.com/derived-to-base",
            "http://serialize.example.com/self",
        ),
    ],
)
def test_links(import_test_context, name, expect):
    import model

    with (DATA_DIR / "python" / "links.json").open("r") as f:
        deserializer = model.JSONLDDeserializer()
        d = ObjectSet(*deserializer.read(f))

    c = d.get_obj(name, model.link_class)
    link = d.get_obj(expect, model.link_class)

    assert c.link_class_link_prop is link
    assert c.link_class_link_prop_no_class is link
    assert c.link_class_link_list_prop == [link, link]


@pytest.mark.parametrize(
    "name,cls",
    [
        (
            "http://serialize.example.com/base-to-blank-base",
            "link_class",
        ),
        (
            "http://serialize.example.com/base-to-blank-derived",
            "link_derived_class",
        ),
        (
            "http://serialize.example.com/derived-to-blank-base",
            "link_class",
        ),
        (
            "http://serialize.example.com/derived-to-blank-derived",
            "link_derived_class",
        ),
    ],
)
def test_blank_links(import_test_context, name, cls):
    import model

    with (DATA_DIR / "python" / "links.json").open("r") as f:
        deserializer = model.JSONLDDeserializer()
        d = ObjectSet(*deserializer.read(f))

    c = d.get_obj(name, model.link_class)

    expect = c.link_class_link_prop
    assert type(expect) is getattr(model, cls)
    assert c.link_class_link_prop_no_class is expect
    assert c.link_class_link_list_prop == [expect, expect]


def test_node_kind_blank(import_test_context, test_context_url):
    import model

    s = model.JSONLDSerializer()
    c1 = model.link_class()
    c2 = model.link_class()

    c1._id = "http://example.com/c1"
    c2._id = "http://example.com/c2"

    ref = model.node_kind_blank()

    with pytest.raises(ValueError):
        ref._id = "http://example.com/name"

    # Blank node assignment is fine but not preserved when serializing
    ref._id = "_:blank"

    # No blank ID is written out for one reference (inline)
    c1.link_class_link_prop = ref
    result = s.serialize_data([c1, c2])
    assert result == {
        "@context": test_context_url,
        "@graph": [
            {
                "@type": "link-class",
                "@id": "http://example.com/c1",
                "link-class-link-prop": {
                    "@type": "node-kind-blank",
                },
            },
            {
                "@type": "link-class",
                "@id": "http://example.com/c2",
            },
        ],
    }

    # Blank node is written out for multiple references
    c2.link_class_link_prop = ref
    result = s.serialize_data([c1, c2])
    assert result == {
        "@context": test_context_url,
        "@graph": [
            {
                "@type": "node-kind-blank",
                "@id": "_:node_kind_blank0",
            },
            {
                "@type": "link-class",
                "@id": "http://example.com/c1",
                "link-class-link-prop": "_:node_kind_blank0",
            },
            {
                "@type": "link-class",
                "@id": "http://example.com/c2",
                "link-class-link-prop": "_:node_kind_blank0",
            },
        ],
    }

    # Listing in the root graph requires a blank node be written
    result = s.serialize_data([c1, ref])
    assert result == {
        "@context": test_context_url,
        "@graph": [
            {
                "@type": "node-kind-blank",
                "@id": "_:node_kind_blank0",
            },
            {
                "@type": "link-class",
                "@id": "http://example.com/c1",
                "link-class-link-prop": "_:node_kind_blank0",
            },
        ],
    }


@pytest.mark.parametrize(
    "cls",
    ["node_kind_iri", "derived_node_kind_iri"],
)
def test_node_kind_iri(import_test_context, test_context_url, cls):
    import model

    TEST_ID = "http://serialize.example.com/name"
    TYP = cls.replace("_", "-")

    s = model.JSONLDSerializer()
    c1 = model.link_class()
    c2 = model.link_class()

    c1._id = "http://example.com/c1"
    c2._id = "http://example.com/c2"

    ref = getattr(model, cls)()

    with pytest.raises(ValueError):
        ref._id = "_:blank"

    # serializing without an ID is not allowed
    with pytest.raises(ValueError):
        s.serialize_data([ref])

    # Inlining not allowed
    ref._id = TEST_ID

    c1.link_class_link_prop = ref
    result = s.serialize_data([c1, c2])
    assert result == {
        "@context": test_context_url,
        "@graph": [
            {
                "@type": "link-class",
                "@id": "http://example.com/c1",
                "link-class-link-prop": TEST_ID,
            },
            {
                "@type": "link-class",
                "@id": "http://example.com/c2",
            },
            {
                "@type": TYP,
                "@id": TEST_ID,
            },
        ],
    }

    # Multiple references
    c2.link_class_link_prop = ref
    result = s.serialize_data([c1, c2])
    assert result == {
        "@context": test_context_url,
        "@graph": [
            {
                "@type": "link-class",
                "@id": "http://example.com/c1",
                "link-class-link-prop": TEST_ID,
            },
            {
                "@type": "link-class",
                "@id": "http://example.com/c2",
                "link-class-link-prop": TEST_ID,
            },
            {
                "@type": TYP,
                "@id": TEST_ID,
            },
        ],
    }

    # Listing in the root graph forces reference
    result = s.serialize_data([c1, ref])
    assert result == {
        "@context": test_context_url,
        "@graph": [
            {
                "@type": "link-class",
                "@id": "http://example.com/c1",
                "link-class-link-prop": TEST_ID,
            },
            {
                "@type": TYP,
                "@id": TEST_ID,
            },
        ],
    }


@pytest.mark.parametrize(
    "cls",
    ["id_prop_class", "inherited_id_prop_class"],
)
def test_id_name(import_test_context, test_context_url, cls):
    import model

    s = model.JSONLDSerializer()
    c = getattr(model, cls)()

    TEST_ID = "http://serialize.example.com/name"

    # Assign alternate ID
    c.testid = TEST_ID
    assert c.testid == TEST_ID

    # alternate ID is an alias for the _id property
    assert c._id == TEST_ID

    # Delete id
    del c.testid
    assert c.testid is None
    assert c._id is None

    # Serialization should the alias name
    c._id = TEST_ID
    result = s.serialize_data([c])
    assert result == {
        "@context": test_context_url,
        "@type": cls.replace("_", "-"),
        "testid": TEST_ID,
    }


SAME_AS_VALUE = object()


def type_tests(name, *typ):
    tests = [
        (name, None, TypeError),
        (name, [], TypeError),
        (name, object(), TypeError),
        (name, lambda model: sum, TypeError),
    ]
    if bool not in typ and int not in typ:
        tests.append((name, True, TypeError))
        tests.append((name, False, TypeError))

    if int not in typ:
        tests.append((name, 1, TypeError))

    if float not in typ:
        tests.append((name, 1.0, TypeError))

    if datetime not in typ:
        tests.append((name, datetime(2024, 3, 11, 0, 0, 0), TypeError)),

    if str not in typ:
        tests.append((name, "foo", TypeError))

    return tests


@pytest.mark.parametrize(
    "prop,value,expect",
    [
        # postive integer
        ("test_class_positive_integer_prop", -1, ValueError),
        ("test_class_positive_integer_prop", 0, ValueError),
        ("test_class_positive_integer_prop", 1, 1),
        ("test_class_positive_integer_prop", False, ValueError),
        ("test_class_positive_integer_prop", True, 1),
        *type_tests("test_class_positive_integer_prop", int),
        # non-negative integer
        ("test_class_nonnegative_integer_prop", -1, ValueError),
        ("test_class_nonnegative_integer_prop", 0, 0),
        ("test_class_nonnegative_integer_prop", 1, 1),
        ("test_class_nonnegative_integer_prop", False, 0),
        ("test_class_nonnegative_integer_prop", True, 1),
        *type_tests("test_class_nonnegative_integer_prop", int),
        # integer
        ("test_class_integer_prop", -1, -1),
        ("test_class_integer_prop", 0, 0),
        ("test_class_integer_prop", 1, 1),
        ("test_class_integer_prop", False, 0),
        ("test_class_integer_prop", True, 1),
        *type_tests("test_class_integer_prop", int),
        # float
        ("test_class_float_prop", -1, -1.0),
        ("test_class_float_prop", -1.0, -1.0),
        ("test_class_float_prop", 0, 0.0),
        ("test_class_float_prop", 0.0, 0.0),
        ("test_class_float_prop", 1, 1.0),
        ("test_class_float_prop", 1.0, 1.0),
        ("test_class_float_prop", False, 0.0),
        ("test_class_float_prop", True, 1.0),
        *type_tests("test_class_float_prop", int, float),
        # boolean
        ("test_class_boolean_prop", True, True),
        ("test_class_boolean_prop", False, False),
        *type_tests("test_class_boolean_prop", bool),
        # datetime
        (
            # Local time
            "test_class_datetime_scalar_prop",
            datetime(2024, 3, 11, 0, 0, 0),
            datetime(2024, 3, 11, 0, 0, 0).astimezone(),
        ),
        (
            # Explict timezone
            "test_class_datetime_scalar_prop",
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(-timedelta(hours=6))),
            SAME_AS_VALUE,
        ),
        (
            # Explict timezone
            "test_class_datetime_scalar_prop",
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(timedelta(hours=0))),
            SAME_AS_VALUE,
        ),
        (
            "test_class_datetime_scalar_prop",
            # UTC
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
            SAME_AS_VALUE,
        ),
        (
            "test_class_datetime_scalar_prop",
            # Microseconds are ignored
            datetime(2024, 3, 11, 0, 0, 0, 999),
            datetime(2024, 3, 11, 0, 0, 0).astimezone(),
        ),
        (
            "test_class_datetime_scalar_prop",
            # Minutes timezone
            datetime(
                2024, 3, 11, 0, 0, 0, tzinfo=timezone(timedelta(hours=-1, minutes=21))
            ),
            SAME_AS_VALUE,
        ),
        (
            "test_class_datetime_scalar_prop",
            # Seconds from timezone are dropped
            datetime(
                2024,
                3,
                11,
                0,
                0,
                0,
                tzinfo=timezone(timedelta(hours=-1, minutes=21, seconds=31)),
            ),
            datetime(
                2024, 3, 11, 0, 0, 0, tzinfo=timezone(timedelta(hours=-1, minutes=21))
            ),
        ),
        *type_tests("test_class_datetime_scalar_prop", datetime),
        # datetimestamp
        (
            # Local time
            "test_class_datetimestamp_scalar_prop",
            datetime(2024, 3, 11, 0, 0, 0),
            datetime(2024, 3, 11, 0, 0, 0).astimezone(),
        ),
        (
            # Explict timezone
            "test_class_datetimestamp_scalar_prop",
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(-timedelta(hours=6))),
            SAME_AS_VALUE,
        ),
        (
            # Explict timezone
            "test_class_datetimestamp_scalar_prop",
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(timedelta(hours=0))),
            SAME_AS_VALUE,
        ),
        (
            "test_class_datetimestamp_scalar_prop",
            # UTC
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
            SAME_AS_VALUE,
        ),
        (
            "test_class_datetimestamp_scalar_prop",
            # Microseconds are ignored
            datetime(2024, 3, 11, 0, 0, 0, 999, tzinfo=timezone.utc),
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
        ),
        (
            "test_class_datetimestamp_scalar_prop",
            # Minutes timezone
            datetime(
                2024, 3, 11, 0, 0, 0, tzinfo=timezone(timedelta(hours=-1, minutes=21))
            ),
            SAME_AS_VALUE,
        ),
        (
            "test_class_datetimestamp_scalar_prop",
            # Seconds from timezone are dropped
            datetime(
                2024,
                3,
                11,
                0,
                0,
                0,
                tzinfo=timezone(timedelta(hours=-1, minutes=21, seconds=31)),
            ),
            datetime(
                2024, 3, 11, 0, 0, 0, tzinfo=timezone(timedelta(hours=-1, minutes=21))
            ),
        ),
        *type_tests("test_class_datetimestamp_scalar_prop", datetime),
        # String
        ("test_class_string_scalar_prop", "foo", "foo"),
        ("test_class_string_scalar_prop", "", ""),
        *type_tests("test_class_string_scalar_prop", str),
        # Named property
        ("named_property", "foo", "foo"),
        ("named_property", "", ""),
        *type_tests("named_property", str),
        # Enumerated value
        (
            "test_class_enum_prop",
            "http://example.org/enumType/foo",
            "http://example.org/enumType/foo",
        ),
        ("test_class_enum_prop", "foo", ValueError),
        *type_tests("test_class_enum_prop", str),
        # Object
        ("test_class_class_prop", lambda model: model.test_class(), SAME_AS_VALUE),
        (
            "test_class_class_prop",
            lambda model: model.test_derived_class(),
            SAME_AS_VALUE,
        ),
        ("test_class_class_prop", lambda model: model.test_another_class(), TypeError),
        ("test_class_class_prop", lambda model: model.parent_class(), TypeError),
        ("test_class_class_prop", "_:blanknode", "_:blanknode"),
        (
            "test_class_class_prop",
            "http://serialize.example.org/test",
            "http://serialize.example.org/test",
        ),
        *type_tests("test_class_class_prop", str),
        # Pattern validated string
        ("test_class_regex", "foo1", "foo1"),
        ("test_class_regex", "foo2", "foo2"),
        ("test_class_regex", "foo2a", "foo2a"),
        ("test_class_regex", "bar", ValueError),
        ("test_class_regex", "fooa", ValueError),
        ("test_class_regex", "afoo1", ValueError),
        *type_tests("test_class_regex", str),
        # Pattern validated dateTime
        (
            "test_class_regex_datetime",
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(timedelta(hours=1))),
            SAME_AS_VALUE,
        ),
        (
            "test_class_regex_datetime",
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(-timedelta(hours=6))),
            ValueError,
        ),
        (
            "test_class_regex_datetime",
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
            ValueError,
        ),
        (
            "test_class_regex_datetime",
            datetime(2024, 3, 11, 0, 0, 0),
            ValueError,
        ),
        # Pattern validated dateTimeStamp
        (
            "test_class_regex_datetimestamp",
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(-timedelta(hours=6))),
            ValueError,
        ),
        (
            "test_class_regex_datetimestamp",
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(timedelta(hours=0))),
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
        ),
        (
            "test_class_regex_datetimestamp",
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
            SAME_AS_VALUE,
        ),
        # Property that is a keyword
        ("import_", "foo", "foo"),
        # A property that conflicts with an existing attribute
        ("encode_", "foo", "foo"),
        # Verify that existing attributes cannot be overwritten
        ("encode", "foo", AttributeError),
    ],
)
def test_scalar_prop_validation(import_test_context, prop, value, expect):
    import model

    c = model.test_class()

    if callable(value):
        value = value(model)

    if expect is SAME_AS_VALUE:
        expect = value

    if isinstance(expect, type) and issubclass(expect, Exception):
        with pytest.raises(expect):
            setattr(c, prop, value)
    else:
        setattr(c, prop, value)
        assert getattr(c, prop) == expect
        assert type(getattr(c, prop)) is type(expect)


def list_type_tests(name, *typ):
    tests = [
        # Non list types
        (name, 1, TypeError),
        (name, 1.0, TypeError),
        (name, True, TypeError),
        (name, "foo", TypeError),
        (name, datetime(2024, 3, 11, 0, 0, 0), TypeError),
        (name, object(), TypeError),
        (name, [object()], TypeError),
        (name, lambda model: sum, TypeError),
        (name, [sum], TypeError),
        # Empty list is always allowed
        (name, [], []),
    ]

    if bool not in typ and int not in typ:
        tests.append((name, [True], TypeError))
        tests.append((name, [False], TypeError))

    if int not in typ:
        tests.append((name, [1], TypeError))

    if float not in typ:
        tests.append((name, [1.0], TypeError))

    if datetime not in typ:
        tests.append((name, [datetime(2024, 3, 11, 0, 0, 0)], TypeError)),

    if str not in typ:
        tests.append((name, ["foo"], TypeError))

    return tests


@pytest.mark.parametrize(
    "prop,value,expect",
    [
        # string
        ("test_class_string_list_prop", ["foo", "bar"], ["foo", "bar"]),
        ("test_class_string_list_prop", [""], [""]),
        *list_type_tests("test_class_string_list_prop", str),
        # datetime
        (
            "test_class_datetime_list_prop",
            [
                datetime(2024, 3, 11, 0, 0, 0),
                datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(-timedelta(hours=6))),
                datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
                datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(timedelta(hours=0))),
                datetime(2024, 3, 11, 0, 0, 0, 999, tzinfo=timezone.utc),
                datetime(
                    2024,
                    3,
                    11,
                    0,
                    0,
                    0,
                    tzinfo=timezone(timedelta(hours=-1, minutes=21)),
                ),
                datetime(
                    2024,
                    3,
                    11,
                    0,
                    0,
                    0,
                    tzinfo=timezone(timedelta(hours=-1, minutes=21, seconds=31)),
                ),
            ],
            [
                datetime(2024, 3, 11, 0, 0, 0).astimezone(),
                datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(-timedelta(hours=6))),
                datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
                datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
                datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
                datetime(
                    2024,
                    3,
                    11,
                    0,
                    0,
                    0,
                    tzinfo=timezone(timedelta(hours=-1, minutes=21)),
                ),
                datetime(
                    2024,
                    3,
                    11,
                    0,
                    0,
                    0,
                    tzinfo=timezone(timedelta(hours=-1, minutes=21)),
                ),
            ],
        ),
        *list_type_tests("test_class_datetime_list_prop", datetime),
        # Enumerate type
        (
            "test_class_enum_list_prop",
            [
                "http://example.org/enumType/foo",
                "http://example.org/enumType/bar",
                "http://example.org/enumType/nolabel",
            ],
            [
                "http://example.org/enumType/foo",
                "http://example.org/enumType/bar",
                "http://example.org/enumType/nolabel",
            ],
        ),
        (
            "test_class_enum_list_prop",
            [
                "http://example.org/enumType/foo",
                "foo",
            ],
            ValueError,
        ),
        *list_type_tests("test_class_enum_list_prop", str),
        # Object
        (
            "test_class_class_list_prop",
            lambda model: [
                model.test_class(),
                model.test_derived_class(),
                "_:blanknode",
                "http://serialize.example.org/test",
                "http://serialize.example.org/test",
            ],
            SAME_AS_VALUE,
        ),
        (
            "test_class_class_list_prop",
            lambda model: [model.test_another_class()],
            TypeError,
        ),
        (
            "test_class_class_list_prop",
            lambda model: [model.parent_class()],
            TypeError,
        ),
        *list_type_tests("test_class_class_list_prop", str),
        # Pattern validated
        (
            "test_class_regex_list",
            [
                "foo1",
                "foo2",
                "foo2a",
            ],
            [
                "foo1",
                "foo2",
                "foo2a",
            ],
        ),
        ("test_class_regex_list", ["bar"], ValueError),
        ("test_class_regex_list", ["fooa"], ValueError),
        ("test_class_regex_list", ["afoo1"], ValueError),
        *list_type_tests("test_class_regex_list", str),
        # TODO Add more list tests
    ],
)
def test_list_prop_validation(import_test_context, prop, value, expect):
    import model

    c = model.test_class()

    if callable(value):
        value = value(model)

    if expect is SAME_AS_VALUE:
        expect = value

    if isinstance(expect, type) and issubclass(expect, Exception):
        with pytest.raises(expect):
            if value is list:
                for v in value:
                    getattr(c, prop).append(v)
            else:
                setattr(c, prop, value)

    else:
        for v in value:
            getattr(c, prop).append(v)

        import pprint

        pprint.pprint(getattr(c, prop))
        pprint.pprint(expect)

        assert getattr(c, prop) == expect
        for idx, v in enumerate(expect):
            assert getattr(c, prop)[idx] == v
            assert type(getattr(c, prop)[idx]) is type(v)

        setattr(c, prop, value[:])
        assert getattr(c, prop) == expect

        assert list(getattr(c, prop)) == expect

        getattr(c, prop).sort()
        assert getattr(c, prop) == list(sorted(expect))

        setattr(c, prop, [])
        getattr(c, prop).extend(value)
        assert getattr(c, prop) == expect

        setattr(c, prop, [])
        for v in value:
            getattr(c, prop).insert(0, v)
        assert getattr(c, prop) == list(reversed(expect))

        for v in expect:
            assert v in getattr(c, prop)


@pytest.mark.parametrize(
    "value,expect",
    [
        (
            "2024-03-11T01:02:03",
            datetime(2024, 3, 11, 1, 2, 3).astimezone(),
        ),
        (
            "2024-03-11T01:02:03Z",
            datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
        ),
        (
            "2024-03-11T01:02:03+00:00",
            datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
        ),
        (
            "2024-03-11T01:02:03+03:00",
            datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=3))),
        ),
        (
            "2024-03-11T01:02:03-03:00",
            datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=-3))),
        ),
        (
            "2024-03-11T01:02:03+03:21",
            datetime(
                2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=3, minutes=21))
            ),
        ),
        # Microseconds not allowed
        (
            "2024-03-11T01:02:03.999Z",
            ValueError,
        ),
        # Timezone with seconds not allowed
        (
            "2024-03-11T01:02:03+03:00:01",
            ValueError,
        ),
    ],
)
def test_datetime_from_string(import_test_context, value, expect):
    import model

    p = model.DateTimeProp()

    if isinstance(expect, type) and issubclass(expect, Exception):
        with pytest.raises(expect):
            p.from_string(value)
    else:
        v = p.from_string(value)
        assert v == expect


@pytest.mark.parametrize(
    "value,expect",
    [
        (
            "2024-03-11T01:02:03Z",
            datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
        ),
        (
            "2024-03-11T01:02:03+00:00",
            datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
        ),
        (
            "2024-03-11T01:02:03+03:00",
            datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=3))),
        ),
        (
            "2024-03-11T01:02:03-03:00",
            datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=-3))),
        ),
        (
            "2024-03-11T01:02:03+03:21",
            datetime(
                2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=3, minutes=21))
            ),
        ),
        # No timezone
        (
            "2024-03-11T01:02:03",
            ValueError,
        ),
        # Microseconds not allowed
        (
            "2024-03-11T01:02:03.999Z",
            ValueError,
        ),
        # Timezone with seconds not allowed
        (
            "2024-03-11T01:02:03+03:00:01",
            ValueError,
        ),
    ],
)
def test_datetimestamp_from_string(import_test_context, value, expect):
    import model

    p = model.DateTimeStampProp()

    if isinstance(expect, type) and issubclass(expect, Exception):
        with pytest.raises(expect):
            p.from_string(value)
    else:
        v = p.from_string(value)
        assert v == expect


@pytest.mark.parametrize(
    "value,expect",
    [
        (
            datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone.utc),
            "2024-03-11T01:02:03Z",
        ),
        (
            datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=0))),
            "2024-03-11T01:02:03Z",
        ),
        (
            datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=3))),
            "2024-03-11T01:02:03+03:00",
        ),
        (
            datetime(2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=-3))),
            "2024-03-11T01:02:03-03:00",
        ),
        (
            datetime(
                2024, 3, 11, 1, 2, 3, tzinfo=timezone(timedelta(hours=3, minutes=21))
            ),
            "2024-03-11T01:02:03+03:21",
        ),
        # Microseconds ignored
        (
            datetime(2024, 3, 11, 1, 2, 3, 999, tzinfo=timezone.utc),
            "2024-03-11T01:02:03Z",
        ),
        # Seconds in timezone ignored
        (
            datetime(
                2024,
                3,
                11,
                1,
                2,
                3,
                tzinfo=timezone(timedelta(hours=3, minutes=21, seconds=31)),
            ),
            "2024-03-11T01:02:03+03:21",
        ),
        (
            datetime(
                2024,
                3,
                11,
                1,
                2,
                3,
                tzinfo=timezone(timedelta(hours=-3, minutes=-21, seconds=31)),
            ),
            "2024-03-11T01:02:03-03:21",
        ),
    ],
)
def test_datetime_to_string(import_test_context, value, expect):
    import model

    p = model.DateTimeProp()

    if isinstance(expect, type) and issubclass(expect, Exception):
        with pytest.raises(expect):
            p.to_string(value)
    else:
        v = p.to_string(value)
        assert v == expect
        assert re.match(
            model.DateTimeProp.REGEX, v
        ), f"Value '{v}' does not match regex"


def test_enum_var_names(import_test_context):
    import model

    assert type(model.enumType.foo) is str
    assert model.enumType.foo == "http://example.org/enumType/foo"

    c = model.test_class()

    for name, value in model.enumType.valid_values:
        c.test_class_enum_prop = value
        assert getattr(model.enumType, name) == value


def test_mandatory_properties(import_test_context, tmp_path):
    """
    Tests that property ordinality (e.g. min count & max count) is checked when
    writing out a file
    """
    import model

    s = model.JSONLDSerializer()
    outfile = tmp_path / "test.json"

    def base_obj():
        c = model.test_class_required()
        c.test_class_required_string_scalar_prop = "foo"
        c.test_class_required_string_list_prop = ["bar", "baz"]
        return c

    # First validate that the base object is actually valid
    c = base_obj()
    with outfile.open("wb") as f:
        s.write([c], f)

    # Required scalar property
    c = base_obj()
    del c.test_class_required_string_scalar_prop
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            s.write([c], f)

    # Array that is deleted
    c = base_obj()
    del c.test_class_required_string_list_prop
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            s.write([c], f)

    # Array initialized to empty list
    c = base_obj()
    c.test_class_required_string_list_prop = []
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            s.write([c], f)

    # Array with too many items
    c = base_obj()
    c.test_class_required_string_list_prop.append("too many")
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            s.write([c], f)


def test_iri(import_test_context, roundtrip):
    import model

    with roundtrip.open("r") as f:
        deserializer = model.JSONLDDeserializer()
        d = ObjectSet(*deserializer.read(f))

    c = d.get_obj("http://serialize.example.com/test", model.test_class)

    assert c._IRI["_id"] == "@id"
    assert c._IRI["named_property"] == "http://example.org/test-class/named-property"

    for name, iri in c._IRI.items():
        assert c[iri] == getattr(c, name)

    with pytest.raises(KeyError):
        c._IRI["foo"]

    assert "foo" not in c._IRI


def test_shacl(roundtrip):
    model = rdflib.Graph()
    model.parse(TEST_MODEL)

    data = rdflib.Graph()
    data.parse(roundtrip)

    conforms, result_graph, result_text = pyshacl.validate(
        data,
        shacl_graph=model,
        ont_graph=model,
    )
    assert conforms, result_text
