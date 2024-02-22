#! /usr/bin/env python3
#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import typing
from dataclasses import dataclass
from .context import Context


@dataclass
class ContextData:
    context: typing.Dict
    url: str


class UrlContext(Context):
    def __init__(self, contexts=[]):
        super().__init__([c.context.get("@context", {}) for c in contexts])
        self.urls = []
        for ctx in contexts:
            self.urls.append(ctx.url)
