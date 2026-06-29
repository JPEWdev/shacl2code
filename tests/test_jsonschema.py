#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import json
import re
import subprocess
from pathlib import Path

import jsonschema

import pytest

from testfixtures import jsonvalidation

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

DATA_DIR = THIS_DIR / "data"

TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"

TEST_CONTEXT = THIS_DIR / "data" / "model" / "test-context.json"

SPDX3_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"


def _check_schema_refs(schema):
    """Assert every $ref in the schema points to a valid $defs entry."""
    DEF_PREFIX = "#/$defs/"

    def check_refs(d, path):
        if isinstance(d, dict):
            if "$ref" in d:
                assert d["$ref"].startswith(
                    DEF_PREFIX
                ), f"{''.join(path)} must start with '{DEF_PREFIX}'"
                name = d["$ref"][len(DEF_PREFIX) :]
                assert (
                    name in schema["$defs"]
                ), f"{''.join(path)}: {name} is not in $defs"

            for k, v in d.items():
                check_refs(v, path + [f".{k}"])

        if isinstance(d, list):
            for idx, v in enumerate(d):
                check_refs(v, path + [f"[{idx}]"])

    check_refs(schema, [])


@pytest.mark.parametrize(
    "generate_args,schema_args",
    [
        (["--input", TEST_MODEL], []),
        (
            ["--input", TEST_MODEL, "--context-url", TEST_CONTEXT, SPDX3_CONTEXT_URL],
            [],
        ),
        (["--input", TEST_MODEL], ["--use-additional-properties"]),
        (
            ["--input", TEST_MODEL, "--context-url", TEST_CONTEXT, SPDX3_CONTEXT_URL],
            ["--use-additional-properties"],
        ),
    ],
)
class TestOutput:
    def _run(self, generate_args, schema_args):
        return subprocess.run(
            ["shacl2code", "generate"]
            + generate_args
            + ["jsonschema"]
            + schema_args
            + ["--output", "-"],
            check=True,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )

    def test_output_syntax(self, generate_args, schema_args):
        """
        Checks that the output file is valid json syntax by parsing it with Python
        """
        p = self._run(generate_args, schema_args)

        json.loads(p.stdout)

    def test_trailing_whitespace(self, generate_args, schema_args):
        """
        Tests that the generated file does not have trailing whitespace
        """
        p = self._run(generate_args, schema_args)

        for num, line in enumerate(p.stdout.splitlines()):
            assert (
                re.search(r"\s+$", line) is None
            ), f"Line {num + 1} has trailing whitespace"

    def test_tabs(self, generate_args, schema_args):
        """
        Tests that the output file doesn't contain tabs
        """
        p = self._run(generate_args, schema_args)

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


def _run_jsonschema_generate(generate_args, schema_args=None):
    """Run shacl2code generate jsonschema; return raw stdout string."""
    p = subprocess.run(
        ["shacl2code", "generate"]
        + generate_args
        + ["jsonschema"]
        + (schema_args or [])
        + ["--output", "-"],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )
    return p.stdout


def _assert_no_unevaluated_properties(schema):
    if isinstance(schema, dict):
        assert "unevaluatedProperties" not in schema, (
            f"unevaluatedProperties found: {schema}"
        )
        for v in schema.values():
            _assert_no_unevaluated_properties(v)
    elif isinstance(schema, list):
        for v in schema:
            _assert_no_unevaluated_properties(v)


def test_schema_references(test_jsonschema):
    _check_schema_refs(test_jsonschema)


def test_schema_references_additional_props():
    schema = json.loads(
        _run_jsonschema_generate(["--input", TEST_MODEL], ["--use-additional-properties"])
    )
    _check_schema_refs(schema)


def test_schema_version_default():
    """Default mode declares Draft 2020-12 (precise semantics for unevaluatedProperties)."""
    schema = json.loads(_run_jsonschema_generate(["--input", TEST_MODEL]))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_schema_version_additional_props():
    """--use-additional-properties mode declares Draft 2019-09 (accurate minimum, no unevaluatedProperties)."""
    schema = json.loads(
        _run_jsonschema_generate(["--input", TEST_MODEL], ["--use-additional-properties"])
    )
    assert schema["$schema"] == "https://json-schema.org/draft/2019-09/schema"


def test_no_unevaluated_properties():
    """--use-additional-properties output must not contain unevaluatedProperties."""
    schema = json.loads(
        _run_jsonschema_generate(["--input", TEST_MODEL], ["--use-additional-properties"])
    )
    _assert_no_unevaluated_properties(schema)


@jsonvalidation.validation_tests()
def test_schema_validation_additional_props(
    test_jsonschema_additional_props, test_context_url, passes, data
):
    jsonvalidation.replace_context(data, test_context_url)

    if passes:
        jsonschema.validate(data, schema=test_jsonschema_additional_props)
    else:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, schema=test_jsonschema_additional_props)


@jsonvalidation.type_tests()
def test_schema_type_validation_additional_props(
    test_jsonschema_additional_props, test_context_url, passes, data
):
    jsonvalidation.replace_context(data, test_context_url)

    if passes:
        jsonschema.validate(data, schema=test_jsonschema_additional_props)
    else:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, schema=test_jsonschema_additional_props)


# ---------------------------------------------------------------------------
# SPDX model tests
# ---------------------------------------------------------------------------

SPDX30_ARGS = [
    "--input",
    "https://spdx.org/rdf/3.0.1/spdx-model.ttl",
    "--input",
    "https://spdx.org/rdf/3.0.1/spdx-json-serialize-annotations.ttl",
    "--context-url",
    "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
    "https://spdx.org/rdf/3.0.1/spdx-context.jsonld",
]

SPDX31_ARGS = [
    "--input",
    "https://spdx.github.io/spdx-spec/v3.1-dev/rdf/spdx-model.ttl",
    "--input",
    "https://spdx.github.io/spdx-spec/v3.1-dev/rdf/jsonld-annotations.ttl",
    "--context-url",
    "https://spdx.github.io/spdx-spec/v3.1-dev/rdf/spdx-context.jsonld",
    "https://spdx.org/rdf/3.1/spdx-context.jsonld",
]


@pytest.mark.network
@pytest.mark.parametrize(
    "spdx_args,schema_args",
    [
        pytest.param(SPDX30_ARGS, [], id="spdx30-default"),
        pytest.param(SPDX30_ARGS, ["--use-additional-properties"], id="spdx30-additional-props"),
        pytest.param(SPDX31_ARGS, [], id="spdx31-default"),
        pytest.param(SPDX31_ARGS, ["--use-additional-properties"], id="spdx31-additional-props"),
    ],
)
class TestSPDXOutput:
    def test_output_syntax(self, spdx_args, schema_args):
        """Generated SPDX schema is valid JSON."""
        output = _run_jsonschema_generate(spdx_args, schema_args)
        json.loads(output)

    def test_trailing_whitespace(self, spdx_args, schema_args):
        """Generated SPDX schema has no trailing whitespace."""
        output = _run_jsonschema_generate(spdx_args, schema_args)
        for num, line in enumerate(output.splitlines()):
            assert (
                re.search(r"\s+$", line) is None
            ), f"Line {num + 1} has trailing whitespace"

    def test_tabs(self, spdx_args, schema_args):
        """Generated SPDX schema has no tabs."""
        output = _run_jsonschema_generate(spdx_args, schema_args)
        for num, line in enumerate(output.splitlines()):
            assert "\t" not in line, f"Line {num + 1} has tabs"

    def test_schema_references(self, spdx_args, schema_args):
        """All $refs in the generated SPDX schema resolve to $defs entries."""
        output = _run_jsonschema_generate(spdx_args, schema_args)
        schema = json.loads(output)
        _check_schema_refs(schema)

    def test_no_unevaluated_properties(self, spdx_args, schema_args):
        """--use-additional-properties schema has no unevaluatedProperties."""
        if "--use-additional-properties" not in schema_args:
            pytest.skip("only applies to --use-additional-properties mode")
        schema = json.loads(_run_jsonschema_generate(spdx_args, schema_args))
        _assert_no_unevaluated_properties(schema)
