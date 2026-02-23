#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from typing import TypeVar, Callable

LANGUAGES = {}

TEMPLATE_DIR = Path(__file__).parent / "templates"

T = TypeVar("T", bound=type)


def language(name: str) -> Callable[[T], T]:
    def inner(cls: T) -> T:
        LANGUAGES[name] = cls
        return cls

    return inner
