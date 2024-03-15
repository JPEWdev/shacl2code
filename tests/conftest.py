#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import pytest
import shutil
import subprocess
import json

from pytest_server_fixtures.http import SimpleHTTPTestServer
from pathlib import Path

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

MODEL_DIR = THIS_DIR / "data" / "model"


@pytest.fixture
def http_server():
    with SimpleHTTPTestServer() as s:
        s.start()
        yield s


@pytest.fixture(scope="session")
def model_server():
    with SimpleHTTPTestServer() as s:
        root = Path(s.document_root)
        for p in MODEL_DIR.iterdir():
            if not p.is_file():
                continue
            shutil.copyfile(p, root / p.name)
        s.start()
        yield s.uri


@pytest.fixture(scope="session")
def test_context_url(model_server):
    yield model_server + "/test-context.json"


@pytest.fixture(scope="session")
def test_jsonschema(model_server, test_context_url):
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            MODEL_DIR / "test.ttl",
            "--context",
            test_context_url,
            "jsonschema",
            "--output",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    yield json.loads(p.stdout)
