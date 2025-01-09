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
from testfixtures import jsonvalidation

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
            EXPECT_DIR / "jsonschema" / "nocontext" / "test.json",
        ),
        (
            ["--input", TEST_MODEL, "--context-url", TEST_CONTEXT, SPDX3_CONTEXT_URL],
            EXPECT_DIR / "jsonschema" / "context" / "test-context.json",
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

        with expect.open("r") as expect_f:
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


@jsonvalidation.validation_tests()
def test_schema_validation(test_jsonschema, test_context_url, passes, data):
    jsonvalidation.replace_context(data, test_context_url)

    if passes:
        jsonschema.validate(data, schema=test_jsonschema)
    else:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, schema=test_jsonschema)


@jsonvalidation.type_tests()
def test_schema_type_validation(test_jsonschema, test_context_url, passes, data):
    jsonvalidation.replace_context(data, test_context_url)

    if passes:
        jsonschema.validate(data, schema=test_jsonschema)
    else:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, schema=test_jsonschema)


def test_schema_references(test_jsonschema):
    DEF_PREFIX = "#/$defs/"

    def check_refs(d, path):
        if isinstance(d, dict):
            if "$ref" in d:
                assert d["$ref"].startswith(
                    DEF_PREFIX
                ), f"{''.join(path)} must start with '{DEF_PREFIX}'"
                name = d["$ref"][len(DEF_PREFIX) :]
                assert (
                    name in test_jsonschema["$defs"]
                ), f"{''.join(path)}: {name} is not in $defs"

            for k, v in d.items():
                check_refs(v, path + [f".{k}"])

        if isinstance(d, list):
            for idx, v in enumerate(d):
                check_refs(v, path + [f"[{idx}]"])

    check_refs(test_jsonschema, [])
