#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import socket
import subprocess
import sys
import tempfile
import time

from pathlib import Path
from contextlib import closing


def get_ephemeral_port(host):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, 0))
        return s.getsockname()[1]


class HTTPTestServer(object):
    def __init__(self):
        self.p = None
        self.temp_dir = None

    def start(self):
        assert self.p is None, "Server already started"

        self.host = "127.0.0.1"
        self.port = get_ephemeral_port(self.host)
        self.p = subprocess.Popen(
            [sys.executable, "-m", "http.server", "--bind", self.host, str(self.port)],
            cwd=self.document_root,
        )
        self.uri = f"http://{self.host}:{self.port}"

        # Wait for server to start
        start_time = time.monotonic()
        while time.monotonic() < start_time + 30:
            assert self.p.poll() is None
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                try:
                    s.connect((self.host, self.port))
                    return

                except ConnectionRefusedError:
                    continue

        # Timeout
        self.p.terminate()
        self.p.wait()
        assert False, "Timeout waiting for server to be ready"

    def stop(self):
        if self.p is None:
            return

        self.p.terminate()
        self.p.wait()

    def __enter__(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        return self

    def __exit__(self, typ, value, tb):
        self.stop()
        self.temp_dir.cleanup()
        self.temp_dir = None

    @property
    def document_root(self):
        return Path(self.temp_dir.name)
