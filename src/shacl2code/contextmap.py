#! /usr/bin/env python3
#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import typing
from dataclasses import dataclass


@dataclass
class Context:
    context: typing.Dict
    url: str


class ContextMap(object):
    def __init__(self, contexts):
        self.contexts = []
        self.urls = []
        for ctx in contexts:
            self.contexts.append(ctx.context.get("@context", {}))
            self.urls.append(ctx.url)

        self.map = {}
        self.expanded = {}

    def __expand(self, _id):
        if _id in self.expanded:
            return self.expanded[_id]

        for ctx in self.contexts:
            if not ctx:
                continue

            if ":" not in _id:
                if _id in ctx:
                    if isinstance(ctx[_id], dict):
                        return self.__expand(ctx[_id]["@id"])
                    self.expanded[_id] = self.__expand(ctx[_id])
                    return self.expanded[_id]
                continue

            prefix, suffix = _id.split(":", 1)
            if prefix not in ctx:
                continue

            self.expanded[_id] = self.__expand(prefix) + suffix
            return self.expanded[_id]

        return _id

    def add_id(self, _id, vocab=""):
        if vocab in self.map and _id in self.map[vocab]:
            return self.map[vocab][_id]

        compact = self.__compact_id(_id, vocab)
        if compact != _id:
            self.map.setdefault(vocab, {})[_id] = compact
        return compact

    def __compact_id(self, _id, vocab):
        if not self.contexts:
            return _id

        contexts = self.contexts[:]

        for ctx in self.contexts:
            # Check for vocabulary contexts
            for name, value in ctx.items():
                if (
                    isinstance(value, dict)
                    and value["@type"] == "@vocab"
                    and vocab == self.__expand(value["@id"])
                ):
                    contexts.insert(0, value["@context"])

        def collect_possible(_id):
            possible = set()
            for ctx in contexts:
                for name, value in ctx.items():
                    if name == "@vocab":
                        if _id.startswith(value):
                            tmp_id = _id[len(value) :]
                            possible.add(tmp_id)
                            possible |= collect_possible(tmp_id)
                    else:
                        if isinstance(value, dict):
                            value = value["@id"]

                        if _id == value:
                            possible.add(name)
                            possible |= collect_possible(name)
                        elif _id.startswith(value):
                            tmp_id = name + ":" + _id[len(value) :].lstrip("/")
                            possible.add(tmp_id)
                            possible |= collect_possible(tmp_id)

            return possible

        possible = collect_possible(_id)
        if not possible:
            return _id

        # To select from the possible identifiers, choose the one that has the
        # least context (fewest ":"), then the shortest, and finally
        # alphabetically
        possible = list(possible)
        possible.sort(key=lambda p: (p.count(":"), len(p), p))

        return possible[0]

    def compact(self, _id, context=""):
        if context in self.map and _id in self.map[context]:
            return self.map[context][_id]
        return _id

    def expand(self, _id, context=""):
        for k, v in self.map[context].items():
            if v == _id:
                return k
        return _id
