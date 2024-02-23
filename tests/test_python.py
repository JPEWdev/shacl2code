#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import json
import jsonschema
import pytest
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

EXPECT_DIR = THIS_DIR / "expect"
DATA_DIR = THIS_DIR / "data"

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


@pytest.fixture
def spdx3_import(tmp_path):
    outfile = tmp_path / "spdx3.py"
    subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
            "--context-url",
            SPDX3_CONTEXT,
            SPDX3_CONTEXT_URL,
            "python",
            "--output",
            outfile,
        ],
        check=True,
    )

    old_path = sys.path[:]
    sys.path.append(str(tmp_path))
    try:
        yield
    finally:
        sys.path = old_path


@pytest.mark.parametrize(
    "expect,args",
    [
        (
            "spdx3.py",
            [],
        ),
        (
            "spdx3-context.py",
            ["--context-url", SPDX3_CONTEXT, SPDX3_CONTEXT_URL],
        ),
    ],
)
class TestOutput:
    def test_generation(self, tmpdir, expect, args):
        """
        Tests that shacl2code generates python output that matches the expected
        output
        """
        outfile = tmpdir.join("spdx3.py")
        subprocess.run(
            [
                "shacl2code",
                "generate",
                "--input",
                SPDX3_MODEL,
            ]
            + args
            + [
                "python",
                "--output",
                outfile,
            ],
            check=True,
        )

        with (EXPECT_DIR / "python" / expect).open("r") as f:
            assert outfile.read() == f.read()

    def test_output_syntax(self, tmpdir, expect, args):
        """
        Checks that the output file is valid python syntax by executing it"
        """
        outfile = tmpdir.join("spdx3.py")
        subprocess.run(
            [
                "shacl2code",
                "generate",
                "--input",
                SPDX3_MODEL,
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

    def test_trailing_whitespace(self, expect, args):
        """
        Tests that the generated file does not have trailing whitespace
        """
        p = subprocess.run(
            [
                "shacl2code",
                "generate",
                "--input",
                SPDX3_MODEL,
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

    def test_tabs(self, expect, args):
        """
        Tests that the output file doesn't contain tabs
        """
        p = subprocess.run(
            [
                "shacl2code",
                "generate",
                "--input",
                SPDX3_MODEL,
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


def test_roundtrip(spdx3_import, tmp_path):
    import spdx3

    infile = DATA_DIR / "python" / "roundtrip.json"
    with infile.open("r") as f:
        objects, _ = spdx3.read_jsonld(f)

    outfile = tmp_path / "out.json"
    with outfile.open("wb") as f:
        spdx3.write_jsonld(objects, f, indent=4)

    with infile.open("r") as f:
        indata = json.load(f)

    with outfile.open("r") as f:
        outdata = json.load(f)

    assert outdata == indata


def test_jsonschema_validation():
    with (THIS_DIR / "expect" / "jsonschema" / "spdx3-context.json").open("r") as f:
        schema = json.load(f)

    with (DATA_DIR / "python" / "roundtrip.json").open("r") as f:
        data = json.load(f)

    jsonschema.validate(data, schema=schema)


def test_links(spdx3_import):
    import spdx3

    with (DATA_DIR / "python" / "links.json").open("r") as f:
        d = ObjectSet(*spdx3.read_jsonld(f))

    agent = d.get_obj("https://spdx.dev/test/agent-with-link", spdx3.core_Agent)
    agent_2 = d.get_obj("https://spdx.dev/test/agent-with-link-2", spdx3.core_Agent)
    creationinfo = d.get_obj(
        "https://spdx.dev/test/creationinfo", spdx3.core_CreationInfo
    )

    assert agent.creationInfo is creationinfo
    assert agent_2.creationInfo is creationinfo
    assert creationinfo.createdBy == [agent]

    agent_blank = d.get_obj("https://spdx.dev/test/agent-blank", spdx3.core_Agent)
    agent_blank_2 = d.get_obj("https://spdx.dev/test/agent-blank-2", spdx3.core_Agent)

    assert isinstance(agent_blank.creationInfo, spdx3.core_CreationInfo)
    assert agent_blank.creationInfo is agent_blank_2.creationInfo
    assert agent_blank.creationInfo.createdBy == [agent_blank]


def test_property_validation(spdx3_import):
    import spdx3

    with (DATA_DIR / "python" / "roundtrip.json").open("r") as f:
        d = ObjectSet(*spdx3.read_jsonld(f))

    agent = d.get_obj("https://spdx.dev/test/agent", spdx3.core_Agent)
    creationinfo = d.get_obj(
        "https://spdx.dev/test/creationinfo", spdx3.core_CreationInfo
    )

    # Setting an unknown property
    with pytest.raises(AttributeError):
        agent.foo = "Bar"

    # Basic type validation
    with pytest.raises(TypeError):
        agent.name = 1

    with pytest.raises(TypeError):
        agent.name = []

    with pytest.raises(ValueError):
        creationinfo.specVersion = "1"

    # Datetime
    assert isinstance(creationinfo.created, datetime)

    with pytest.raises(TypeError):
        creationinfo.created = 1

    creationinfo.created = datetime.now()

    # Object
    with pytest.raises(TypeError):
        agent.creationInfo = None

    agent.creationInfo = "https://spdx.dev/foo/bar"
    agent.creationInfo = creationinfo
    with pytest.raises(TypeError):
        agent.creationInfo = agent

    # Object Lists
    creationinfo.createdBy = []
    for i in range(3):
        with pytest.raises(TypeError):
            creationinfo.createdBy.append(None)

        with pytest.raises(TypeError):
            creationinfo.createdBy.append(creationinfo)

        assert len(creationinfo.createdBy) == i
        creationinfo.createdBy.append(agent)
        assert len(creationinfo.createdBy) == i + 1

    with pytest.raises(TypeError):
        creationinfo.createdBy = 1

    with pytest.raises(AttributeError):
        creationinfo.createdBy.foo

    # Enum
    h = spdx3.core_Hash()
    with pytest.raises(TypeError):
        h.algorithm = 1

    with pytest.raises(ValueError):
        h.algorithm = "sha1"

    h.algorithm = spdx3.core_HashAlgorithm.sha1
    assert isinstance(spdx3.core_HashAlgorithm.sha1, str)

    # Check valid values
    for name, value in spdx3.core_HashAlgorithm.valid_values:
        h.algorithm = value
        getattr(spdx3.core_HashAlgorithm, name)


def test_mandatory_properties(spdx3_import, tmp_path):
    """
    Tests that property ordinality (e.g. min count & max count) is checked when
    writing out a file
    """
    import spdx3

    outfile = tmp_path / "test.json"

    def base_obj():
        c = spdx3.core_CreationInfo()
        c.specVersion = "3.0.0"
        c.created = datetime.now()
        c.createdBy = ["https://spdx.dev/test/agent"]
        return c

    # First validate that the base object is actually valid
    c = base_obj()
    with outfile.open("wb") as f:
        spdx3.write_jsonld([c], f)

    # Optional argument
    c = base_obj()
    del c.specVersion
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            spdx3.write_jsonld([c], f)

    # Array that is deleted
    c = base_obj()
    del c.createdBy
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            spdx3.write_jsonld([c], f)

    # Array initialized to empty list
    c = base_obj()
    c.createdBy = []
    with outfile.open("wb") as f:
        with pytest.raises(ValueError):
            spdx3.write_jsonld([c], f)

    # TODO: Need to test max count, but there aren't any in the SPDX model currently
