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

SPDX3_MODEL = THIS_DIR / "data" / "model" / "spdx3.jsonld"

SPDX3_CONTEXT = THIS_DIR / "data" / "model" / "spdx3-context.json"
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
            ["--input", SPDX3_MODEL],
            "spdx3.py",
        ),
        (
            ["--input", SPDX3_MODEL, "--context-url", SPDX3_CONTEXT, SPDX3_CONTEXT_URL],
            "spdx3-context.py",
        ),
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

    c = d.get_obj(name, model.linkclass)
    link = d.get_obj(expect, model.linkclass)

    assert c.linkclassprop is link
    assert c.linkclasspropnoclass is link
    assert c.linkclasslistprop == [link, link]


@pytest.mark.parametrize(
    "name,cls",
    [
        (
            "http://serialize.example.com/base-to-blank-base",
            "linkclass",
        ),
        (
            "http://serialize.example.com/base-to-blank-derived",
            "linkderivedclass",
        ),
        (
            "http://serialize.example.com/derived-to-blank-base",
            "linkclass",
        ),
        (
            "http://serialize.example.com/derived-to-blank-derived",
            "linkderivedclass",
        ),
    ],
)
def test_blank_links(import_test_context, name, cls):
    import model

    with (DATA_DIR / "python" / "links.json").open("r") as f:
        deserializer = model.JSONLDDeserializer()
        d = ObjectSet(*deserializer.read(f))

    c = d.get_obj(name, model.linkclass)

    expect = c.linkclassprop
    assert type(expect) is getattr(model, cls)
    assert c.linkclasspropnoclass is expect
    assert c.linkclasslistprop == [expect, expect]


def test_non_refable(import_test_context, test_context_url):
    import model

    s = model.JSONLDSerializer()
    c1 = model.linkclass()
    c2 = model.linkclass()

    non_ref = model.refnoclass()

    c1.linkclassprop = non_ref

    # A non-refable object should be inlined
    result = s.serialize_data([c1])
    assert result == {
        "@context": test_context_url,
        "@type": "link-class",
        "link-class-prop": {
            "@type": "ref-no-class",
        },
    }

    # A non-refable class cannot be referenced from multiple objects, as this
    # would require creating a blank node reference
    c1.linkclassprop = non_ref
    c2.linkclassprop = non_ref

    with pytest.raises(ValueError):
        result = s.serialize_data([c1, c2])
        print(result)

    # A non-refable class written as the root object is OK
    result = s.serialize_data([non_ref])
    assert result == {
        "@context": test_context_url,
        "@type": "ref-no-class",
    }

    # A non-refable class cannot have an explicit ID assigned
    with pytest.raises(ValueError):
        non_ref._id = "http://example.org/name"

    # Or a blank node
    with pytest.raises(ValueError):
        non_ref._id = "_:blank"


def test_yes_refable(import_test_context, test_context_url):
    import model

    TEST_ID = "http://example.com/name"

    s = model.JSONLDSerializer()
    c1 = model.linkclass()
    c2 = model.linkclass()

    ref = model.refyesclass()

    # Mandatory reference fails because there is no ID
    c1.linkclassprop = ref
    with pytest.raises(ValueError):
        s.serialize_data([c1])

    # Even references from multiple objects fails because it would generate a
    # blank node with is not referenceable
    c2.linkclassprop = ref
    with pytest.raises(ValueError):
        s.serialize_data([c1, c2])

    # Assigning a reference allows the object to be serialized
    ref._id = TEST_ID
    result = s.serialize_data([c1])
    # inline is allowed
    assert result == {
        "@context": test_context_url,
        "@type": "link-class",
        "link-class-prop": {
            "@id": TEST_ID,
            "@type": "ref-yes-class",
        },
    }

    # using a graph will force the object into the root @graph (even though not
    # explicitly specified)
    result = s.serialize_data([c1], force_graph=True)
    assert result == {
        "@context": test_context_url,
        "@graph": [
            {
                "@type": "link-class",
                "link-class-prop": TEST_ID,
            },
            {
                "@id": TEST_ID,
                "@type": "ref-yes-class",
            },
        ],
    }

    # Assignment of a blank node value is not allowed
    with pytest.raises(ValueError):
        ref._id = "_:blank"


def test_always_refable(import_test_context, test_context_url):
    import model

    TEST_ID = "http://example.com/name"

    s = model.JSONLDSerializer()
    c1 = model.linkclass()
    c2 = model.linkclass()

    ref = model.refalwaysclass()

    # Mandatory reference fails because there is no ID
    c1.linkclassprop = ref
    with pytest.raises(ValueError):
        s.serialize_data([c1])

    # Even references from multiple objects fails because it would generate a
    # blank node with is not referenceable
    c2.linkclassprop = ref
    with pytest.raises(ValueError):
        s.serialize_data([c1, c2])

    # Assigning a reference allows the object to be serialized
    ref._id = TEST_ID
    # inlining is not allowed since it is not a reference
    with pytest.raises(ValueError):
        s.serialize_data([c1])

    # using a graph will force the object into the root @graph (even though not
    # explicitly specified)
    result = s.serialize_data([c1], force_graph=True)
    assert result == {
        "@context": test_context_url,
        "@graph": [
            {
                "@type": "link-class",
                "link-class-prop": TEST_ID,
            },
            {
                "@id": TEST_ID,
                "@type": "ref-always-class",
            },
        ],
    }

    # Assignment of a blank node value is not allowed
    with pytest.raises(ValueError):
        ref._id = "_:blank"


def test_optional_refable(import_test_context, test_context_url):
    # This is the normal object behavior, so not much to test here that isn't
    # covered elsewhere
    import model

    TEST_ID = "http://example.com/name"

    s = model.JSONLDSerializer()
    c1 = model.linkclass()
    c2 = model.linkclass()

    ref = model.refoptionalclass()

    INLINE_RESULT = {
        "@context": test_context_url,
        "@type": "link-class",
        "link-class-prop": {
            "@type": "ref-optional-class",
        },
    }

    # Test that objects are inlined
    c1.linkclassprop = ref
    result = s.serialize_data([c1])
    assert result == INLINE_RESULT

    # Explict blank node assignment is not preserved
    ref._id = "_:blank"
    result = s.serialize_data([c1])
    assert result == INLINE_RESULT

    BLANK_RESULT = {
        "@context": test_context_url,
        "@graph": [
            {
                "@type": "link-class",
                "link-class-prop": "_:refoptionalclass0",
            },
            {
                "@type": "link-class",
                "link-class-prop": "_:refoptionalclass0",
            },
            {
                "@id": "_:refoptionalclass0",
                "@type": "ref-optional-class",
            },
        ],
    }

    # Multiple links means the object will be moved to the @graph instead of
    # being inlined
    del ref._id
    c2.linkclassprop = ref
    result = s.serialize_data([c1, c2])
    assert result == BLANK_RESULT

    # Explicit blank node assignment, but it's not preserved in serialization
    ref._id = "_:blank"
    result = s.serialize_data([c1, c2])
    assert result == BLANK_RESULT

    # Assign a non-blank node id (which is preserved)
    ref._id = TEST_ID
    result = s.serialize_data([c1, c2])
    assert result == {
        "@context": test_context_url,
        "@graph": [
            {
                "@type": "link-class",
                "link-class-prop": TEST_ID,
            },
            {
                "@type": "link-class",
                "link-class-prop": TEST_ID,
            },
            {
                "@id": TEST_ID,
                "@type": "ref-optional-class",
            },
        ],
    }


def test_local_refable(import_test_context):
    import model

    ref = model.reflocalclass()

    with pytest.raises(ValueError):
        ref._id = "http://example.com/name"

    # Blank node assignment is fine, but not preserved when serializing
    ref._id = "_:blank"


def test_id_name(import_test_context, test_context_url):
    import model

    s = model.JSONLDSerializer()
    c = model.idpropclass()

    TEST_ID = "http://example.com/name"

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
        "@type": "id-prop-class",
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
        ("testclasspositiveintegerprop", -1, ValueError),
        ("testclasspositiveintegerprop", 0, ValueError),
        ("testclasspositiveintegerprop", 1, 1),
        ("testclasspositiveintegerprop", False, ValueError),
        ("testclasspositiveintegerprop", True, 1),
        *type_tests("testclasspositiveintegerprop", int),
        # non-negative integer
        ("testclassnonnegativeintegerprop", -1, ValueError),
        ("testclassnonnegativeintegerprop", 0, 0),
        ("testclassnonnegativeintegerprop", 1, 1),
        ("testclassnonnegativeintegerprop", False, 0),
        ("testclassnonnegativeintegerprop", True, 1),
        *type_tests("testclassnonnegativeintegerprop", int),
        # integer
        ("testclassintegerprop", -1, -1),
        ("testclassintegerprop", 0, 0),
        ("testclassintegerprop", 1, 1),
        ("testclassintegerprop", False, 0),
        ("testclassintegerprop", True, 1),
        *type_tests("testclassintegerprop", int),
        # float
        ("testclassfloatprop", -1, -1.0),
        ("testclassfloatprop", -1.0, -1.0),
        ("testclassfloatprop", 0, 0.0),
        ("testclassfloatprop", 0.0, 0.0),
        ("testclassfloatprop", 1, 1.0),
        ("testclassfloatprop", 1.0, 1.0),
        ("testclassfloatprop", False, 0.0),
        ("testclassfloatprop", True, 1.0),
        *type_tests("testclassfloatprop", int, float),
        # boolean
        ("testclassbooleanprop", True, True),
        ("testclassbooleanprop", False, False),
        *type_tests("testclassbooleanprop", bool),
        # datetime
        (
            "testclassdatetimescalarprop",
            # Local time to UTC
            datetime(2024, 3, 11, 0, 0, 0),
            datetime(2024, 3, 11, 0, 0, 0).astimezone(timezone.utc),
        ),
        (
            "testclassdatetimescalarprop",
            # Explict timezone to UTC
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(-timedelta(hours=6))),
            datetime(2024, 3, 11, 6, 0, 0, tzinfo=timezone.utc),
        ),
        (
            "testclassdatetimescalarprop",
            # Already in UTC
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
        ),
        *type_tests("testclassdatetimescalarprop", datetime),
        # String
        ("testclassstringscalarprop", "foo", "foo"),
        ("testclassstringscalarprop", "", ""),
        *type_tests("testclassstringscalarprop", str),
        # Named property
        ("named_property", "foo", "foo"),
        ("named_property", "", ""),
        *type_tests("named_property", str),
        # Enumerated value
        (
            "testclassenumprop",
            "http://example.org/enumType/foo",
            "http://example.org/enumType/foo",
        ),
        ("testclassenumprop", "foo", ValueError),
        *type_tests("testclassenumprop", str),
        # Object
        ("testclassclassprop", lambda model: model.testclass(), SAME_AS_VALUE),
        ("testclassclassprop", lambda model: model.testderivedclass(), SAME_AS_VALUE),
        ("testclassclassprop", lambda model: model.testanotherclass(), TypeError),
        ("testclassclassprop", lambda model: model.parentclass(), TypeError),
        ("testclassclassprop", "_:blanknode", "_:blanknode"),
        (
            "testclassclassprop",
            "http://serialize.example.org/test",
            "http://serialize.example.org/test",
        ),
        *type_tests("testclassclassprop", str),
        # Pattern validated
        ("testclassregex", "foo1", "foo1"),
        ("testclassregex", "foo2", "foo2"),
        ("testclassregex", "foo2a", "foo2a"),
        ("testclassregex", "bar", ValueError),
        ("testclassregex", "fooa", ValueError),
        ("testclassregex", "afoo1", ValueError),
        *type_tests("testclassregex", str),
    ],
)
def test_scalar_prop_validation(import_test_context, prop, value, expect):
    import model

    c = model.testclass()

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
        ("testclassstringlistprop", ["foo", "bar"], ["foo", "bar"]),
        ("testclassstringlistprop", [""], [""]),
        *list_type_tests("testclassstringlistprop", str),
        # datetime
        (
            "testclassdatetimelistprop",
            [
                datetime(2024, 3, 11, 0, 0, 0),
                datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone(-timedelta(hours=6))),
                datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
            ],
            [
                datetime(2024, 3, 11, 0, 0, 0).astimezone(timezone.utc),
                datetime(2024, 3, 11, 6, 0, 0, tzinfo=timezone.utc),
                datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc),
            ],
        ),
        *list_type_tests("testclassdatetimelistprop", datetime),
        # Enumerate type
        (
            "testclassenumlistprop",
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
            "testclassenumlistprop",
            [
                "http://example.org/enumType/foo",
                "foo",
            ],
            ValueError,
        ),
        *list_type_tests("testclassenumlistprop", str),
        # Object
        (
            "testclassclasslistprop",
            lambda model: [
                model.testclass(),
                model.testderivedclass(),
                "_:blanknode",
                "http://serialize.example.org/test",
                "http://serialize.example.org/test",
            ],
            SAME_AS_VALUE,
        ),
        (
            "testclassclasslistprop",
            lambda model: [model.testanotherclass()],
            TypeError,
        ),
        (
            "testclassclasslistprop",
            lambda model: [model.parentclass()],
            TypeError,
        ),
        *list_type_tests("testclassclasslistprop", str),
        # Pattern validated
        (
            "testclassregexlist",
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
        ("testclassregexlist", ["bar"], ValueError),
        ("testclassregexlist", ["fooa"], ValueError),
        ("testclassregexlist", ["afoo1"], ValueError),
        *list_type_tests("testclassregexlist", str),
        # TODO Add more list tests
    ],
)
def test_list_prop_validation(import_test_context, prop, value, expect):
    import model

    c = model.testclass()

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


def test_enum_var_names(import_test_context):
    import model

    assert type(model.enumType.foo) is str
    assert model.enumType.foo == "http://example.org/enumType/foo"

    c = model.testclass()

    for name, value in model.enumType.valid_values:
        c.testclassenumprop = value
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
        c = model.testclassrequired()
        c.testclassrequiredstringscalarprop = "foo"
        c.testclassrequiredstringlistprop = ["bar", "baz"]
        return c

    # First validate that the base object is actually valid
    c = base_obj()
    with outfile.open("wb") as f:
        s.write([c], f)

    # Required scalar property
    c = base_obj()
    del c.testclassrequiredstringscalarprop
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            s.write([c], f)

    # Array that is deleted
    c = base_obj()
    del c.testclassrequiredstringlistprop
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            s.write([c], f)

    # Array initialized to empty list
    c = base_obj()
    c.testclassrequiredstringlistprop = []
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            s.write([c], f)

    # Array with too many items
    c = base_obj()
    c.testclassrequiredstringlistprop.append("too many")
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            s.write([c], f)


def test_iri(import_test_context, roundtrip):
    import model

    with roundtrip.open("r") as f:
        deserializer = model.JSONLDDeserializer()
        d = ObjectSet(*deserializer.read(f))

    c = d.get_obj("http://serialize.example.com/test", model.testclass)

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
        meta_shacl=True,
    )
    assert conforms, result_text
