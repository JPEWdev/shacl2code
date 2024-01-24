#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import pytest
from pytest_server_fixtures.http import SimpleHTTPTestServer


@pytest.fixture
def http_server():
    with SimpleHTTPTestServer() as s:
        s.start()
        yield s
