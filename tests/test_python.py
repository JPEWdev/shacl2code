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
import importlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

from testfixtures import jsonvalidation, timetests

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

DATA_DIR = THIS_DIR / "data"

TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"

TEST_CONTEXT = THIS_DIR / "data" / "model" / "test-context.json"

SPDX3_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"

TEST_TZ = timezone(timedelta(hours=-2), name="TST")


def shacl2code_generate(args, outfile):
    return subprocess.run(
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
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )


@pytest.fixture(scope="module")
def test_context(tmp_path_factory, model_server):
    tmp_directory = tmp_path_factory.mktemp("pythontestcontext")
    outfile = tmp_directory / "model.py"
    shacl2code_generate(
        [
            "--input",
            TEST_MODEL,
            "--context",
            model_server + "/test-context.json",
        ],
        outfile,
    )
    outfile.chmod(0o755)
    yield (tmp_directory, outfile)


@pytest.fixture(scope="module")
def test_script(test_context):
    _, script = test_context
    yield script


@pytest.fixture(scope="function")
def model(test_context):
    tmp_directory, _ = test_context

    old_path = sys.path[:]
    sys.path.append(str(tmp_directory))
    try:
        import model

        importlib.reload(model)
        yield model
    finally:
        sys.path = old_path


@pytest.mark.parametrize(
    "args",
    [
        ["--input", TEST_MODEL],
        ["--input", TEST_MODEL, "--context-url", TEST_CONTEXT, SPDX3_CONTEXT_URL],
    ],
)
class TestOutput:
    """
    Test syntax and formatting of the output file
    """

    def test_output_syntax(self, tmp_path, args):
        """
        Checks that the output file is valid python syntax by executing it"
        """
        outfile = tmp_path / "output.py"
        shacl2code_generate(args, outfile)

        subprocess.run([sys.executable, outfile, "--help"], check=True)

    def test_trailing_whitespace(self, args):
        """
        Tests that the generated file does not have trailing whitespace
        """
        p = shacl2code_generate(args, "-")

        for num, line in enumerate(p.stdout.splitlines()):
            assert (
                re.search(r"\s+$", line) is None
            ), f"Line {num + 1} has trailing whitespace"

    def test_tabs(self, args):
        """
        Tests that the output file doesn't contain tabs
        """
        p = shacl2code_generate(args, "-")

        for num, line in enumerate(p.stdout.splitlines()):
            assert "\t" not in line, f"Line {num + 1} has tabs"


@pytest.mark.parametrize(
    "args",
    [
        ["--input", TEST_MODEL],
        ["--input", TEST_MODEL, "--context-url", TEST_CONTEXT, SPDX3_CONTEXT_URL],
    ],
)
class TestCheckType:
    """
    Static type checking tests for the generated Python code
    """

    def test_mypy(self, tmp_path, args):
        """
        Mypy static type checking
        """
        outfile = tmp_path / "output.py"
        shacl2code_generate(args, outfile)
        subprocess.run(
            ["mypy", outfile],
            encoding="utf-8",
            check=True,
        )

    def test_pyrefly(self, tmp_path, args):
        """
        Pyrefly static type checking
        """
        outfile = tmp_path / "output.py"
        shacl2code_generate(args, outfile)
        subprocess.run(
            ["pyrefly", "check", outfile],
            encoding="utf-8",
            check=True,
        )

    def test_pyright(self, tmp_path, args):
        """
        Pyright static type checking
        """
        outfile = tmp_path / "output.py"
        shacl2code_generate(args, outfile)
        subprocess.run(
            ["pyright", outfile],
            encoding="utf-8",
            check=True,
        )


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


def test_roundtrip(model, tmp_path, roundtrip):
    doc = model.SHACLObjectSet()
    with roundtrip.open("r") as f:
        d = model.JSONLDDeserializer()
        d.read(f, doc)

    with roundtrip.open("r") as f:
        expect_data = json.load(f)

    outfile = tmp_path / "out.json"
    with outfile.open("wb") as f:
        s = model.JSONLDSerializer()
        digest = s.write(doc, f, indent=4)

    check_file(outfile, expect_data, digest)

    with outfile.open("wb") as f:
        s = model.JSONLDInlineSerializer()
        digest = s.write(doc, f)

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


def test_from_rdf_roundtrip(model, tmp_path, roundtrip):
    with roundtrip.open("r") as f:
        expect_data = json.load(f)

    # Parse data using RDF
    g = rdflib.Graph()
    g.parse(roundtrip)

    # Convert to SHACL objects
    objset = model.SHACLObjectSet()
    model.RDFDeserializer().read(g, objset)

    # Write out
    outfile = tmp_path / "out.json"
    with outfile.open("wb") as f:
        digest = model.JSONLDInlineSerializer().write(objset, f)

    check_file(outfile, expect_data, digest)


def test_to_rdf_roundtrip(model, tmp_path, roundtrip):
    with roundtrip.open("r") as f:
        expect_data = json.load(f)

    # Read JSON data
    objset = model.SHACLObjectSet()
    with roundtrip.open("r") as f:
        model.JSONLDDeserializer().read(f, objset)

    # Convert to RDF
    g = rdflib.Graph()
    model.RDFSerializer().write(objset, g)

    # Convert from RDF to new object set
    objset = model.SHACLObjectSet()
    model.RDFDeserializer().read(g, objset)

    # Write out
    outfile = tmp_path / "out.json"
    with outfile.open("wb") as f:
        digest = model.JSONLDInlineSerializer().write(objset, f)

    check_file(outfile, expect_data, digest)


def test_jsonschema_validation(roundtrip, test_jsonschema):
    with roundtrip.open("r") as f:
        data = json.load(f)

    jsonschema.validate(data, schema=test_jsonschema)


@jsonvalidation.link_tests()
def test_links(filename, name, expect_tag, model, tmp_path, test_context_url):
    data_file = tmp_path / "data.json"
    data_file.write_text(
        filename.read_text().replace("@CONTEXT_URL@", test_context_url)
    )

    objset = model.SHACLObjectSet()
    with data_file.open("r") as f:
        deserializer = model.JSONLDDeserializer()
        deserializer.read(f, objset)

    c = objset.find_by_id(name)
    assert isinstance(c, model.link_class)

    for o in objset.foreach_type(model.link_class):
        if o.link_class_tag == expect_tag:
            link = o
            break
    else:
        assert False, f"Unable to find object with tag '{expect_tag}'"

    assert c.link_class_link_prop is link
    assert c.link_class_link_prop_no_class is link
    assert c.link_class_link_list_prop == [link, link]


@pytest.mark.parametrize(
    "filename,expect",
    [
        ("bad-object-type-inline.json", TypeError),
        ("bad-object-type-ref-before.json", TypeError),
        ("bad-object-type-ref-after.json", TypeError),
    ],
)
def test_deserialize(model, filename, expect):
    objset = model.SHACLObjectSet()
    deserializer = model.JSONLDDeserializer()
    with (DATA_DIR / "python" / filename).open("r") as f:
        if issubclass(expect, Exception):
            with pytest.raises(expect):
                deserializer.read(f, objset)
        else:
            deserializer.read(f, objset)


def test_node_kind_blank(model, test_context_url):
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
    result = s.serialize_data(model.SHACLObjectSet([c1, c2]))
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
    result = s.serialize_data(model.SHACLObjectSet([c1, c2]))
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
    result = s.serialize_data(model.SHACLObjectSet([c1, ref]))
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
def test_node_kind_iri(model, test_context_url, cls):
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
        s.serialize_data(model.SHACLObjectSet([ref]))

    # Inlining not allowed
    ref._id = TEST_ID

    c1.link_class_link_prop = ref
    result = s.serialize_data(model.SHACLObjectSet([c1, c2]))
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
    result = s.serialize_data(model.SHACLObjectSet([c1, c2]))
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
    result = s.serialize_data(model.SHACLObjectSet([c1, ref]))
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
def test_id_name(model, test_context_url, cls):
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
    result = s.serialize_data(model.SHACLObjectSet([c]))
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
        # positive integer
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
            lambda _: datetime(2024, 3, 11, 0, 0, 0),
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=TEST_TZ),
        ),
        (
            # Explicit timezone
            "test_class_datetime_scalar_prop",
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(-timedelta(hours=6))),
            SAME_AS_VALUE,
        ),
        (
            # Explicit timezone
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
            lambda _: datetime(2024, 3, 11, 0, 0, 0, 999),
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=TEST_TZ),
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
                tzinfo=timezone(timedelta(hours=-1, minutes=-21, seconds=-31)),
            ),
            datetime(
                2024, 3, 11, 0, 0, 0, tzinfo=timezone(timedelta(hours=-1, minutes=-21))
            ),
        ),
        *type_tests("test_class_datetime_scalar_prop", datetime),
        # datetimestamp
        (
            # Local time
            "test_class_datetimestamp_scalar_prop",
            lambda _: datetime(2024, 3, 11, 0, 0, 0),
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=TEST_TZ),
        ),
        (
            # Explicit timezone
            "test_class_datetimestamp_scalar_prop",
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(-timedelta(hours=6))),
            SAME_AS_VALUE,
        ),
        (
            # Explicit timezone
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
                tzinfo=timezone(timedelta(hours=-1, minutes=-21, seconds=-31)),
            ),
            datetime(
                2024, 3, 11, 0, 0, 0, tzinfo=timezone(timedelta(hours=-1, minutes=-21))
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
        ("test_class_class_prop", lambda model: model.test_class.named, SAME_AS_VALUE),
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
def test_scalar_prop_validation(model, test_timezone, prop, value, expect):
    c = model.test_class()

    if callable(value):
        value = value(model)

    if expect is SAME_AS_VALUE:
        expect = value

    kwargs = {prop: value}

    for cls in model.test_class, model.test_derived_class:
        c = cls()

        if isinstance(expect, type) and issubclass(expect, Exception):
            with pytest.raises(expect):
                setattr(c, prop, value)

            with pytest.raises(expect):
                c = cls(**kwargs)
        else:
            setattr(c, prop, value)
            assert getattr(c, prop) == expect
            assert type(getattr(c, prop)) is type(expect)

            c = cls(**kwargs)
            assert getattr(c, prop) == expect
            assert type(getattr(c, prop)) is type(expect)


def test_derived_property(model):
    # The test above covers most of the test cases with setting properties, but
    # it doesn't cover if the property is defined in the derived class, so test
    # those here
    c = model.test_derived_class(test_derived_class_string_prop="abc")
    assert c.test_derived_class_string_prop == "abc"

    c.test_derived_class_string_prop = "def"
    assert c.test_derived_class_string_prop == "def"


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
                    tzinfo=timezone(timedelta(hours=-1, minutes=-21, seconds=-31)),
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
                    tzinfo=timezone(timedelta(hours=-1, minutes=-21)),
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
def test_list_prop_validation(model, prop, value, expect):
    c = model.test_class()

    if callable(value):
        value = value(model)

    if expect is SAME_AS_VALUE:
        expect = value

    kwargs = {prop: value}
    for cls in model.test_class, model.test_derived_class:
        c = cls()

        if isinstance(expect, type) and issubclass(expect, Exception):
            with pytest.raises(expect):
                if value is list:
                    for v in value:
                        getattr(c, prop).append(v)
                else:
                    setattr(c, prop, value)

            with pytest.raises(expect):
                cls(**kwargs)

        else:
            for v in value:
                getattr(c, prop).append(v)

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

            c = cls(**kwargs)
            assert getattr(c, prop) == expect


@timetests.datetime_decode_tests()
def test_datetime_from_string(model, value, expect):
    p = model.DateTimeProp()

    if expect is None:
        with pytest.raises(ValueError):
            p.from_string(value)
    else:
        v = p.from_string(value)
        assert v == expect


@timetests.datetimestamp_decode_tests()
def test_datetimestamp_from_string(model, value, expect):
    p = model.DateTimeStampProp()

    if expect is None:
        with pytest.raises(ValueError):
            p.from_string(value)
    else:
        v = p.from_string(value)
        assert v == expect


@timetests.datetime_encode_tests()
def test_datetime_to_string(model, value, expect):
    p = model.DateTimeProp()

    if expect is None:
        with pytest.raises(expect):
            p.to_string(value)
    else:
        v = p.to_string(value)
        assert v == expect
        assert re.match(
            model.DateTimeProp.REGEX, v
        ), f"Value '{v}' does not match regex"


@pytest.mark.parametrize(
    "prop,serkey,value,expect",
    [
        (
            "extensible_class_property",
            "extensible-class/property",
            "foo",
            "foo",
        ),
        (
            "http://example.org/extensible-test-prop",
            "http://example.org/extensible-test-prop",
            "foo",
            AttributeError,
        ),
    ],
)
def test_extensible_prop(model, test_context_url, prop, serkey, value, expect):
    e = model.extensible_class(extensible_class_required="required")

    if isinstance(expect, type) and issubclass(expect, Exception):
        with pytest.raises(expect):
            setattr(e, prop, value)
    else:
        setattr(e, prop, value)
        assert getattr(e, prop, value) == expect

        s = model.JSONLDSerializer()
        objset = model.SHACLObjectSet()
        objset.add(e)

        data = s.serialize_data(objset)

        assert data == {
            "@context": test_context_url,
            "@type": "extensible-class",
            "extensible-class/required": "required",
            serkey: expect,
        }


@pytest.mark.parametrize(
    "iri,value,expect,ser_data,ser_expect",
    [
        (
            "extensible_class_property",
            "foo",
            KeyError,
            None,
            None,
        ),
        (
            "http://example.org/extensible-test-prop",
            "foo",
            SAME_AS_VALUE,
            ["foo"],
            ["foo"],
        ),
        (
            "http://example.org/extensible-test-prop",
            1,
            SAME_AS_VALUE,
            [1],
            [1],
        ),
        (
            "http://example.org/extensible-test-prop",
            1.123,
            SAME_AS_VALUE,
            ["1.123"],
            [1.123],
        ),
        (
            "http://example.org/extensible-test-prop",
            object(),
            SAME_AS_VALUE,
            TypeError,
            None,
        ),
        (
            "http://example.org/extensible-test-prop",
            [1, "foo", 1.123],
            SAME_AS_VALUE,
            [1, "foo", "1.123"],
            [1, "foo", 1.123],
        ),
        (
            "http://example.org/extensible-test-prop",
            [object()],
            SAME_AS_VALUE,
            TypeError,
            None,
        ),
    ],
)
def test_extensible_iri(
    model, test_context_url, iri, value, expect, ser_data, ser_expect
):
    e = model.extensible_class(extensible_class_required="required")

    if expect is SAME_AS_VALUE:
        expect = value

    if ser_data is SAME_AS_VALUE:
        ser_data = value

    if ser_expect is SAME_AS_VALUE:
        ser_expect = value

    if isinstance(expect, type) and issubclass(expect, Exception):
        with pytest.raises(expect):
            e[iri] = value
    else:
        e[iri] = value
        assert e[iri] == expect
        assert (None, iri, None) in e.property_keys()

        s = model.JSONLDSerializer()
        objset = model.SHACLObjectSet()
        objset.add(e)

        if isinstance(ser_data, type) and issubclass(ser_data, Exception):
            with pytest.raises(ser_data):
                data = s.serialize_data(objset)
        else:
            data = s.serialize_data(objset)
            assert data == {
                "@context": test_context_url,
                "@type": "extensible-class",
                "extensible-class/required": "required",
                iri: ser_data,
            }

            objset = model.SHACLObjectSet()
            d = model.JSONLDDeserializer()
            d.deserialize_data(data, objset)

            e = objset.objects.pop()
            assert e[iri] == ser_expect

        del e[iri]
        with pytest.raises(KeyError):
            e[iri]


def test_extensible_deserialize(model, test_context_url):
    def deserialize_extension(ext_data):
        d = model.JSONLDDeserializer()
        objset = model.SHACLObjectSet()
        d.deserialize_data(
            {
                "@context": test_context_url,
                "@type": "link-class",
                "link-class-extensible": ext_data,
            },
            objset,
        )
        return objset

    @model.register("http://example.org/closed-class")
    class ClosedExtension(model.extensible_class):
        CLOSED = True

    @model.register("http://example.org/open-class")
    class OpenExtension(model.extensible_class):
        pass

    TEST_TYPE = "http://example.org/test-extensible"
    TEST_IRI = "http://example.org/test-key"
    TEST_ID = "http://example.org/test-id"

    objset = deserialize_extension(
        {
            "@type": TEST_TYPE,
            "@id": TEST_ID,
            TEST_IRI: "foo",
        }
    )
    obj = objset.find_by_id(TEST_ID)
    assert obj is not None
    assert isinstance(obj, model.extensible_class)

    assert (None, TEST_IRI, None) in obj.property_keys()
    assert obj[TEST_IRI] == "foo"
    assert obj.TYPE == TEST_TYPE
    assert obj.COMPACT_TYPE is None

    with pytest.raises(KeyError):
        deserialize_extension(
            {
                "@type": TEST_TYPE,
                "@id": TEST_ID,
                "not-an-iri": "foo",
            }
        )

    with pytest.raises(KeyError):
        deserialize_extension(
            {
                "@type": TEST_TYPE,
                "@id": TEST_ID,
                "_:blank": "foo",
            }
        )

    objset = deserialize_extension(
        {
            "@type": "http://example.org/closed-class",
            "@id": TEST_ID,
        }
    )
    obj = objset.find_by_id(TEST_ID)
    assert obj is not None
    assert isinstance(obj, ClosedExtension)
    assert obj.TYPE == "http://example.org/closed-class"
    assert obj.COMPACT_TYPE is None

    # Derived object is closed and cannot have arbitrary IRI assignment
    with pytest.raises(KeyError):
        obj[TEST_IRI] = "foo"

    objset = deserialize_extension(
        {
            "@type": "http://example.org/open-class",
            "@id": TEST_ID,
        }
    )
    obj = objset.find_by_id(TEST_ID)
    assert obj is not None
    assert isinstance(obj, OpenExtension)
    assert obj.TYPE == "http://example.org/open-class"
    assert obj.COMPACT_TYPE is None

    # Derived object is open and can have arbitrary assignments
    obj[TEST_IRI] = "foo"


def test_enum_named_individuals(model):
    assert type(model.enumType.foo) is str
    assert model.enumType.foo == "http://example.org/enumType/foo"

    c = model.test_class()

    assert model.enumType.NAMED_INDIVIDUALS == {
        "foo": "http://example.org/enumType/foo",
        "bar": "http://example.org/enumType/bar",
        "nolabel": "http://example.org/enumType/nolabel",
    }

    for name, value in model.enumType.NAMED_INDIVIDUALS.items():
        c.test_class_enum_prop = value
        assert getattr(model.enumType, name) == value


def test_mandatory_properties(model, tmp_path):
    """
    Tests that property cardinality (e.g. min count & max count) is checked when
    writing out a file
    """
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
        s.write(model.SHACLObjectSet([c]), f)

    # Required scalar property
    c = base_obj()
    del c.test_class_required_string_scalar_prop
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            s.write(model.SHACLObjectSet([c]), f)

    # Array that is deleted
    c = base_obj()
    del c.test_class_required_string_list_prop
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            s.write(model.SHACLObjectSet([c]), f)

    # Array initialized to empty list
    c = base_obj()
    c.test_class_required_string_list_prop = []
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            s.write(model.SHACLObjectSet([c]), f)

    # Array with too many items
    c = base_obj()
    c.test_class_required_string_list_prop.append("too many")
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            s.write(model.SHACLObjectSet([c]), f)


def test_iri(model, roundtrip):
    doc = model.SHACLObjectSet()
    with roundtrip.open("r") as f:
        deserializer = model.JSONLDDeserializer()
        deserializer.read(f, doc)

    c = doc.find_by_id("http://serialize.example.com/test")
    assert isinstance(c, model.test_class)

    assert c._IRI["_id"] == "@id"
    assert c._IRI["named_property"] == "http://example.org/test-class/named-property"

    for name, iri in c._IRI.items():
        assert c[iri] == getattr(c, name)

    with pytest.raises(KeyError):
        c._IRI["foo"]

    assert "foo" not in c._IRI


def test_shacl(roundtrip):
    from rdflib import RDF, URIRef

    data = rdflib.Graph()
    data.parse(roundtrip)

    # We need to add the referenced non-shape object, otherwise SHACL will
    # complain it is missing
    data.add(
        (
            URIRef("http://serialize.example.com/non-shape"),
            RDF.type,
            URIRef("http://example.org/non-shape-class"),
        )
    )

    conforms, result_graph, result_text = pyshacl.validate(
        data,
        shacl_graph=str(TEST_MODEL),
        ont_graph=str(TEST_MODEL),
    )
    assert conforms, result_text


def test_single_register(model):
    # Ensures that class property registration is only called once
    assert model.test_class._NEEDS_REG
    c1 = model.test_class()
    assert not model.test_class._NEEDS_REG

    c2 = model.test_class()
    assert not model.test_class._NEEDS_REG

    c1.test_class_string_scalar_prop = "abc"
    c2.test_class_string_scalar_prop = "def"

    assert c1.test_class_string_scalar_prop == "abc"
    assert c2.test_class_string_scalar_prop == "def"

    assert model.test_derived_class._NEEDS_REG
    _ = model.test_derived_class()
    assert not model.test_derived_class._NEEDS_REG

    _ = model.test_derived_class()
    assert not model.test_derived_class._NEEDS_REG


def test_objset_foreach_type(model, roundtrip):
    objset = model.SHACLObjectSet()

    EXTENSION_ID = "http://example.org/custom-extension"

    @model.register("http://example.org/custom-extension-class")
    class Extension(model.extensible_class):
        pass

    with roundtrip.open("r") as f:
        model.JSONLDDeserializer().read(f, objset)

    objset.add(Extension(_id=EXTENSION_ID))

    expect = set()

    expect.add(objset.find_by_id("http://serialize.example.com/test"))
    expect.add(objset.find_by_id("http://serialize.example.com/nested-parent"))
    expect.add(
        objset.find_by_id(
            "http://serialize.example.com/test-named-individual-reference"
        )
    )
    expect.add(
        objset.find_by_id(
            "http://serialize.example.com/nested-parent"
        ).test_class_class_prop
    )
    expect.add(objset.find_by_id("http://serialize.example.com/test-special-chars"))
    assert expect != {None}

    assert set(objset.foreach_type(model.test_class, match_subclass=False)) == expect
    assert set(objset.foreach_type("test-class", match_subclass=False)) == expect
    assert (
        set(objset.foreach_type("http://example.org/test-class", match_subclass=False))
        == expect
    )

    expect.add(objset.find_by_id("http://serialize.example.com/required"))
    expect.add(objset.find_by_id("http://serialize.example.com/test-derived"))
    assert expect != {None}

    assert set(objset.foreach_type(model.test_class, match_subclass=True)) == expect
    assert set(objset.foreach_type("test-class", match_subclass=True)) == expect
    assert (
        set(objset.foreach_type("http://example.org/test-class", match_subclass=True))
        == expect
    )

    expect = set()
    assert (
        set(objset.foreach_type(model.extensible_class, match_subclass=False)) == expect
    )
    assert set(objset.foreach_type("extensible-class", match_subclass=False)) == expect
    assert (
        set(
            objset.foreach_type(
                "http://example.org/extensible-class", match_subclass=False
            )
        )
        == expect
    )

    expect.add(objset.find_by_id(EXTENSION_ID))
    assert expect != {None}

    assert (
        set(objset.foreach_type(model.extensible_class, match_subclass=True)) == expect
    )
    assert set(objset.foreach_type("extensible-class", match_subclass=True)) == expect
    assert (
        set(
            objset.foreach_type(
                "http://example.org/extensible-class", match_subclass=True
            )
        )
        == expect
    )

    assert set(objset.foreach_type(Extension, match_subclass=False)) == expect
    assert (
        set(
            objset.foreach_type(
                "http://example.org/custom-extension-class", match_subclass=False
            )
        )
        == expect
    )

    # Test that concrete classes derived from abstract classes can be iterated
    expect = set()
    assert (
        set(objset.foreach_type(model.abstract_class, match_subclass=False)) == expect
    )

    expect.add(objset.find_by_id("http://serialize.example.com/concrete-class"))
    assert expect != {None}
    assert set(objset.foreach_type(model.abstract_class, match_subclass=True)) == expect


@pytest.mark.parametrize(
    "abstract,concrete",
    [
        ("abstract_class", "concrete_class"),
        ("abstract_spdx_class", "concrete_spdx_class"),
        ("abstract_sh_class", "concrete_sh_class"),
    ],
)
def test_abstract_classes(model, abstract, concrete):
    # Test that abstract classes cannot be implemented
    with pytest.raises(NotImplementedError):
        cls = getattr(model, abstract)
        cls()

    # Test that concrete classes derived from abstract classes can be
    # implemented
    cls = getattr(model, concrete)
    cls()


def test_required_abstract_class_property(model, tmp_path):
    # Test that a class with a required property that references an abstract
    # class can be instantiated
    c = model.required_abstract()
    assert c.required_abstract_abstract_class_prop is None

    outfile = tmp_path / "out.json"
    objset = model.SHACLObjectSet()
    objset.add(c)
    s = model.JSONLDSerializer()

    # Attempting to serialize without assigning the property should fail
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            s.write(objset, f, indent=4)

    # Assigning a concrete class should succeed and allow serialization
    c.required_abstract_abstract_class_prop = model.concrete_class()
    with outfile.open("wb") as f:
        s.write(objset, f, indent=4)

    # Deleting an abstract class property should return it to None
    del c.required_abstract_abstract_class_prop
    assert c.required_abstract_abstract_class_prop is None


def test_extensible_abstract_class(model):
    @model.register("http://example.org/custom-extension-class")
    class Extension(model.extensible_abstract_class):
        pass

    # Test that an extensible abstract class cannot be created
    with pytest.raises(NotImplementedError):
        model.extensible_abstract_class()

    # Test that a class derived from an abstract extensible class can be
    # created
    Extension()


def test_named_individual(model, roundtrip):
    objset = model.SHACLObjectSet()
    with roundtrip.open("r") as f:
        d = model.JSONLDDeserializer()
        d.read(f, objset)

    c = objset.find_by_id(
        "http://serialize.example.com/test-named-individual-reference"
    )
    assert c is not None
    assert c.test_class_class_prop == model.test_class.named

    assert model.test_class.named not in objset.missing_ids


def test_missing_ids(model, roundtrip):
    objset = model.SHACLObjectSet()
    with roundtrip.open("r") as f:
        d = model.JSONLDDeserializer()
        d.read(f, objset)

    assert objset.missing_ids == {
        "http://serialize.example.com/non-shape",
    }


def test_deprecated_class(model):
    with pytest.deprecated_call():
        model.test_deprecated_class()


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_deprecated_property(model):
    c = model.test_deprecated_class()

    with pytest.deprecated_call():
        c.test_deprecated_class_deprecated_string_prop = "foo"
