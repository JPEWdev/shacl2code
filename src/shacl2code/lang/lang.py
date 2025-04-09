#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from pathlib import Path

LANGUAGES = {}

TEMPLATE_DIR = Path(__file__).parent / "templates"


def language(name):
    def inner(cls):
        LANGUAGES[name] = cls
        return cls

    return inner
