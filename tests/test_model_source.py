#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import shutil
import subprocess
import pytest
import rdflib
import json
from pathlib import Path

import shacl2code

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

RAW_TEMPLATE = THIS_DIR / "data" / "raw.j2"
TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"


CONTEXT_TEMPLATE = THIS_DIR / "data" / "context.j2"
CONTEXT_URL_TEMPLATE = THIS_DIR / "data" / "context-url.j2"
TEST_CONTEXT = THIS_DIR / "data" / "model" / "test-context.json"
TEST_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"


@pytest.fixture(scope="session")
def expect_output(tmp_path_factory):
    outfile = tmp_path_factory.mktemp("expect") / "expect.txt"
    subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "jinja",
            "--output",
            outfile,
            "--template",
            RAW_TEMPLATE,
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    d = outfile.read_text()
    assert d.strip(), "No output generated"
    yield d


@pytest.fixture(scope="session")
def expect_context_output(tmp_path_factory):
    outfile = tmp_path_factory.mktemp("expect") / "expect-context.txt"
    subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "--context-url",
            TEST_CONTEXT,
            TEST_CONTEXT_URL,
            "jinja",
            "--output",
            outfile,
            "--template",
            CONTEXT_TEMPLATE,
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    d = outfile.read_text()
    assert d.strip(), "No output generated"
    yield d


def test_generation_stdout(expect_output):
    """
    Tests that shacl2code generates output to stdout when requested
    """
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "jinja",
            "--output",
            "-",
            "--template",
            RAW_TEMPLATE,
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    assert p.stdout == expect_output


def test_generation_input_format(tmp_path, expect_output):
    """
    Tests that shacl2code generates output correctly with an explicit input
    format
    """
    # File has no extension
    dest = tmp_path / "model"
    shutil.copy(TEST_MODEL, dest)

    # Passing the wrong input format should fail
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            dest,
            "--input-format",
            "json-ld",
            "jinja",
            "--output",
            "-",
            "--template",
            RAW_TEMPLATE,
        ],
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )
    assert p.returncode != 0

    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            dest,
            "--input-format",
            "ttl",
            "jinja",
            "--output",
            "-",
            "--template",
            RAW_TEMPLATE,
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )
    assert p.stdout == expect_output


def test_generation_stdin(expect_output):
    """
    Tests that shacl2code generates output from a model on stdin
    """
    with TEST_MODEL.open("r") as f:
        p = subprocess.run(
            [
                "shacl2code",
                "generate",
                "--input",
                "-",
                "--input-format",
                "ttl",
                "jinja",
                "--output",
                "-",
                "--template",
                RAW_TEMPLATE,
            ],
            check=True,
            stdin=f,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )

    assert p.stdout == expect_output


def test_generation_stdin_auto_format():
    """
    Tests that shacl2code doesn't allow 'auto' format on stdin
    """
    with TEST_MODEL.open("r") as f:
        p = subprocess.run(
            [
                "shacl2code",
                "generate",
                "--input",
                "-",
                "--input-format",
                "auto",
                "jinja",
                "--output",
                "-",
                "--template",
                RAW_TEMPLATE,
            ],
            stdin=f,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )

    assert p.returncode != 0


def test_generation_url(model_server, expect_output):
    """
    Tests that shacl2code generates output from a model provided in a URL
    """
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            f"{model_server}/test.ttl",
            "jinja",
            "--output",
            "-",
            "--template",
            RAW_TEMPLATE,
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    assert p.stdout == expect_output


def test_context_file_missing_url():
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "--context",
            TEST_CONTEXT,
            "jinja",
            "--output",
            "-",
            "--template",
            CONTEXT_TEMPLATE,
        ],
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    assert p.returncode != 0, "Process exited successfully when an error was expected"


def test_context_url(model_server, expect_context_output):
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "--context-url",
            f"{model_server}/test-context.json",
            TEST_CONTEXT_URL,
            "jinja",
            "--output",
            "-",
            "--template",
            CONTEXT_TEMPLATE,
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    assert p.stdout == expect_context_output


def test_context_args(http_server):
    shutil.copyfile(TEST_CONTEXT, http_server.document_root / "context.json")
    shutil.copyfile(TEST_CONTEXT, http_server.document_root / "context2.json")

    def do_test(*, contexts=[], url_contexts=[]):
        cmd = [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
        ]

        expect = []
        for c in contexts:
            cmd.extend(["--context", c])
            expect.append(c)

        for c, url in url_contexts:
            cmd.extend(["--context-url", c, url])
            expect.append(url)

        cmd += [
            "jinja",
            "--output",
            "-",
            "--template",
            CONTEXT_URL_TEMPLATE,
        ]

        p = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )

        assert p.stdout.splitlines() == expect

    # Single URL
    do_test(contexts=[f"{http_server.uri}/context.json"])

    # Multiple URLs
    do_test(
        contexts=[
            f"{http_server.uri}/context.json",
            f"{http_server.uri}/context2.json",
        ]
    )

    # URL rewriting
    do_test(
        url_contexts=[
            (f"{http_server.uri}/context.json", "http://foo/A.json"),
        ]
    )

    # Multiple URL rewriting
    do_test(
        url_contexts=[
            (f"{http_server.uri}/context.json", "http://foo/A.json"),
            (f"{http_server.uri}/context2.json", "http://foo/B.json"),
        ]
    )

    # Mixed
    do_test(
        contexts=[
            f"{http_server.uri}/context.json",
            f"{http_server.uri}/context2.json",
        ],
        url_contexts=[
            (f"{http_server.uri}/context.json", "http://foo/A.json"),
            (f"{http_server.uri}/context2.json", "http://foo/B.json"),
        ],
    )


@pytest.mark.parametrize(
    "file",
    [
        "bad-reference.jsonld",
        "missing-range.ttl",
        "bad-node-kind.ttl",
        "bad-pattern-class.ttl",
        "bad-pattern-integer.ttl",
    ],
)
def test_model_errors(file):
    with pytest.raises(shacl2code.ModelException):
        shacl2code.main(
            [
                "generate",
                "--input",
                str(THIS_DIR / "data" / file),
                "jinja",
                "--output",
                "-",
                "--template",
                str(CONTEXT_TEMPLATE),
            ]
        )


def test_context_contents():
    from rdflib import RDF, OWL, RDFS

    model = rdflib.Graph()
    model.parse(TEST_MODEL)

    with TEST_CONTEXT.open("r") as f:
        context = json.load(f)

    def check_prefix(iri, typ):
        test_prefix = context["@context"]["test"]

        assert iri.startswith(
            test_prefix
        ), f"{typ} '{str(iri)}' does not have correct prefix {test_prefix}"

        name = iri[len(test_prefix) :].lstrip("/")

        return name

    def check_subject(iri, typ):
        name = check_prefix(iri, typ)

        assert name in context["@context"], f"{typ} '{name}' missing from context"

        value = context["@context"][name]
        return name, value

    for c in model.subjects(RDF.type, OWL.Class):
        name, value = check_subject(c, "Class")
        assert value == f"test:{name}", f"Class '{name}' has bad value '{value}'"

    for p in model.subjects(RDF.type, RDF.Property):
        name, value = check_subject(p, "Property")

        assert model.objects(p, RDFS.range), f"Property '{name}' is missing rdfs:range"
        assert isinstance(value, dict), f"Property '{name}' must be a dictionary"

        assert "@id" in value, f"Property '{name}' missing @id"
        assert "@type" in value, f"Property '{name}' missing @type"
        assert (
            value["@id"] == f"test:{name}"
        ), f"Context '{name}' has bad @id '{value['@id']}'"

    for i in model.subjects(RDF.type, OWL.NamedIndividual):
        name = check_prefix(i, "Named Individual")

        assert (
            name not in context
        ), f"Named Individual '{name}' should not be in context"
