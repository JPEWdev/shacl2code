# SPDX-FileContributor: Joshua Watt
# SPDX-FileContributor: Arthit Suriyawongkul
# SPDX-FileCopyrightText: 2024-present Joshua Watt
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jsonschema

import pytest

from testfixtures import jsonvalidation

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

DATA_DIR = THIS_DIR / "data"

TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"

TEST_CONTEXT = THIS_DIR / "data" / "model" / "test-context.json"

SPDX3_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"


def _check_schema_refs(schema: Dict[str, Any]) -> None:
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


def _run_jsonschema_generate(
    generate_args: List[Union[str, os.PathLike[str]]],
    schema_args: Optional[List[str]] = None,
) -> str:
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


def _assert_no_unevaluated_properties(schema: Any) -> None:
    if isinstance(schema, dict):
        assert (
            "unevaluatedProperties" not in schema
        ), f"unevaluatedProperties found: {schema}"
        for v in schema.values():
            _assert_no_unevaluated_properties(v)
    elif isinstance(schema, list):
        for v in schema:
            _assert_no_unevaluated_properties(v)


def test_schema_references(test_jsonschema):
    _check_schema_refs(test_jsonschema)


def test_schema_references_additional_props():
    schema = json.loads(
        _run_jsonschema_generate(
            ["--input", TEST_MODEL], ["--use-additional-properties"]
        )
    )
    _check_schema_refs(schema)


def test_schema_version_default():
    """Default mode declares Draft 2020-12 (precise semantics for unevaluatedProperties)."""
    schema = json.loads(_run_jsonschema_generate(["--input", TEST_MODEL]))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_schema_version_additional_props():
    """--use-additional-properties mode declares Draft 2019-09 (accurate minimum, no unevaluatedProperties)."""
    schema = json.loads(
        _run_jsonschema_generate(
            ["--input", TEST_MODEL], ["--use-additional-properties"]
        )
    )
    assert schema["$schema"] == "https://json-schema.org/draft/2019-09/schema"


def test_context_on_embedded_object_default_rejects():
    """Default mode rejects @context on an embedded object (unevaluatedProperties catches it)."""
    schema = json.loads(_run_jsonschema_generate(["--input", TEST_MODEL]))
    doc = {
        "@type": "http://example.org/link-class",
        "http://example.org/link-class-link-prop": {
            "@type": "http://example.org/link-class",
            "@context": "http://example.org/ctx",
        },
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, schema=schema)


def test_context_on_embedded_object_additional_props_accepts():
    """--use-additional-properties mode permits @context on embedded objects.

    @context is added to every class's inlined property list so that root-level
    documents (which carry @context) pass additionalProperties: false. As a
    known side-effect, @context is also accepted on embedded objects.
    """
    schema = json.loads(
        _run_jsonschema_generate(
            ["--input", TEST_MODEL], ["--use-additional-properties"]
        )
    )
    doc = {
        "@type": "http://example.org/link-class",
        "http://example.org/link-class-link-prop": {
            "@type": "http://example.org/link-class",
            "@context": "http://example.org/ctx",
        },
    }
    jsonschema.validate(doc, schema=schema)


def test_no_unevaluated_properties():
    """--use-additional-properties output must not contain unevaluatedProperties."""
    schema = json.loads(
        _run_jsonschema_generate(
            ["--input", TEST_MODEL], ["--use-additional-properties"]
        )
    )
    _assert_no_unevaluated_properties(schema)


# ---------------------------------------------------------------------------
# get_all_properties coverage: structural assertions on --use-additional-properties schema
# ---------------------------------------------------------------------------

# $defs keys are varname-processed (slashes/dots -> underscores, scheme stripped)
_TEST_CLASS = "http_exampleorgtestclass"
_TEST_DERIVED = "http_exampleorgtestderivedclass"
_EXTENSIBLE_CLASS = "http_exampleorgextensibleclass"

# Property path IRIs as they appear in then.properties (full form: no context URL supplied)
_PARENT_PROP = "http://example.org/test-class/string-scalar-prop"
_OWN_PROP = "http://example.org/test-derived-class/string-prop"


@pytest.fixture(scope="module")
def additional_props_schema() -> Dict[str, Any]:
    return json.loads(
        _run_jsonschema_generate(
            ["--input", TEST_MODEL], ["--use-additional-properties"]
        )
    )


def test_additional_props_no_props_defs(
    additional_props_schema: Dict[str, Any],
) -> None:
    """--use-additional-properties removes _props entries; all properties are inlined."""
    props_keys = [k for k in additional_props_schema["$defs"] if k.endswith("_props")]
    assert props_keys == [], f"unexpected _props entries: {props_keys}"


def test_additional_props_root_class_has_context_and_additional_properties(
    additional_props_schema: Dict[str, Any],
) -> None:
    """Root class then block has @context and additionalProperties: false."""
    then = additional_props_schema["$defs"][_TEST_CLASS]["then"]
    assert "@context" in then["properties"]
    assert then["additionalProperties"] is False


def test_additional_props_derived_class_has_parent_prop(
    additional_props_schema: Dict[str, Any],
) -> None:
    """Derived class then block contains properties inherited from the parent class."""
    props = additional_props_schema["$defs"][_TEST_DERIVED]["then"]["properties"]
    assert _PARENT_PROP in props, "parent property missing from derived class"


def test_additional_props_derived_class_has_own_prop(
    additional_props_schema: Dict[str, Any],
) -> None:
    """Derived class then block contains the class's own properties."""
    props = additional_props_schema["$defs"][_TEST_DERIVED]["then"]["properties"]
    assert _OWN_PROP in props, "own property missing from derived class"


def test_additional_props_derived_class_parent_props_come_first(
    additional_props_schema: Dict[str, Any],
) -> None:
    """Parent properties appear before the class's own properties (parent-first order)."""
    prop_keys = list(
        additional_props_schema["$defs"][_TEST_DERIVED]["then"]["properties"].keys()
    )
    assert prop_keys.index(_PARENT_PROP) < prop_keys.index(_OWN_PROP)


def test_additional_props_prop_refs_attributed_to_defining_class(
    additional_props_schema: Dict[str, Any],
) -> None:
    """Each property's $ref points to the class that originally defines it."""
    props = additional_props_schema["$defs"][_TEST_DERIVED]["then"]["properties"]
    assert (
        "prop_http_exampleorgtestclass" in props[_PARENT_PROP]["$ref"]
    ), "parent prop ref should point to test-class prop definition"
    assert (
        "prop_http_exampleorgtestderivedclass" in props[_OWN_PROP]["$ref"]
    ), "own prop ref should point to test-derived-class prop definition"


def test_additional_props_extensible_class_allows_additional_properties(
    additional_props_schema: Dict[str, Any],
) -> None:
    """Extensible class has additionalProperties: true with --use-additional-properties."""
    then = additional_props_schema["$defs"][_EXTENSIBLE_CLASS]["then"]
    assert then["additionalProperties"] is True


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
        pytest.param(
            SPDX30_ARGS, ["--use-additional-properties"], id="spdx30-additional-props"
        ),
        pytest.param(SPDX31_ARGS, [], id="spdx31-default"),
        pytest.param(
            SPDX31_ARGS, ["--use-additional-properties"], id="spdx31-additional-props"
        ),
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
