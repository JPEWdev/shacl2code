#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import List

import pytest

from testfixtures.httpserver import HTTPTestServer


def _network_available() -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect(("8.8.8.8", 53))
        return True
    except OSError:
        return False


def pytest_collection_modifyitems(items: List[pytest.Item]) -> None:
    if _network_available():
        return
    skip = pytest.mark.skip(reason="no network connection")
    for item in items:
        if item.get_closest_marker("network"):
            item.add_marker(skip)


THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

DATA_DIR = THIS_DIR / "data"
MODEL_DIR = DATA_DIR / "model"


@pytest.fixture
def http_server():
    with HTTPTestServer() as s:
        s.start()
        yield s


@pytest.fixture(scope="session")
def model_server():
    with HTTPTestServer() as s:
        for p in MODEL_DIR.iterdir():
            if not p.is_file():
                continue
            shutil.copyfile(p, s.document_root / p.name)
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


@pytest.fixture(scope="function")
def test_timezone():
    try:
        current_tz = os.environ["TZ"]
    except KeyError:
        current_tz = None

    os.environ["TZ"] = "TST+02"
    time.tzset()

    try:
        yield
    finally:
        if current_tz is None:
            del os.environ["TZ"]
        else:
            os.environ["TZ"] = current_tz
        time.tzset()


@pytest.fixture(scope="session")
def test_jsonschema_additional_props(model_server, test_context_url):
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            MODEL_DIR / "test.ttl",
            "--context",
            test_context_url,
            "jsonschema",
            "--use-additional-properties",
            "--output",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    yield json.loads(p.stdout)


@pytest.fixture(scope="session")
def roundtrip(tmp_path_factory, model_server):
    outfile = tmp_path_factory.mktemp("roundtrip") / "roundtrip.json"
    with (DATA_DIR / "roundtrip.json").open("r") as f:
        data = f.read()

    data = data.replace("@CONTEXT_URL@", model_server + "/test-context.json")

    with outfile.open("w") as f:
        f.write(data)

    yield outfile
