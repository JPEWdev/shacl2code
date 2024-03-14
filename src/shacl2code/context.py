# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT


class Context(object):
    from contextlib import contextmanager

    def __init__(self, contexts=[]):
        self.contexts = [c for c in contexts if c]
        self.__vocabs = []
        self.__expanded = {}
        self.__compacted = {}

    @contextmanager
    def vocab_push(self, vocab):
        if not vocab:
            yield self
            return

        self.__vocabs.append(vocab)
        try:
            yield self
        finally:
            self.__vocabs.pop()

    def __get_vocab_contexts(self):
        contexts = []

        for v in self.__vocabs:
            for ctx in self.contexts:
                # Check for vocabulary contexts
                for name, value in ctx.items():
                    if (
                        isinstance(value, dict)
                        and value["@type"] == "@vocab"
                        and v == self.__expand(value["@id"], self.contexts)
                    ):
                        contexts.insert(0, value["@context"])

        return contexts

    def compact(self, _id):
        return self.__compact_contexts(_id)

    def compact_vocab(self, _id, vocab=None):
        with self.vocab_push(vocab):
            if not self.__vocabs:
                v = ""
            else:
                v = self.__vocabs[-1]

            return self.__compact_contexts(_id, v, self.__get_vocab_contexts())

    def __compact_contexts(self, _id, v="", apply_vocabs=False):
        if v not in self.__compacted or _id not in self.__compacted[v]:
            if apply_vocabs:
                contexts = self.__get_vocab_contexts() + self.contexts
            else:
                contexts = self.contexts

            self.__compacted.setdefault(v, {})[_id] = self.__compact(
                _id,
                contexts,
                apply_vocabs,
            )
        return self.__compacted[v][_id]

    def __compact(self, _id, contexts, apply_vocabs):
        def remove_prefix(_id, value):
            possible = set()
            if _id.startswith(value):
                tmp_id = _id[len(value) :]
                possible.add(tmp_id)
                possible |= collect_possible(tmp_id)
            return possible

        def collect_possible(_id):
            possible = set()
            for ctx in contexts:
                for name, value in ctx.items():
                    if name == "@vocab":
                        if apply_vocabs:
                            possible |= remove_prefix(_id, value)
                    elif name == "@base":
                        possible |= remove_prefix(_id, value)
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

    def is_relative(self, _id):
        import re

        return not re.match(r"[^:]+:", _id)

    def __expand_contexts(self, _id, v="", apply_vocabs=False):
        if v not in self.__expanded or _id not in self.__expanded[v]:
            if apply_vocabs:
                contexts = self.__get_vocab_contexts() + self.contexts

                # Apply contexts
                for ctx in contexts:
                    for name, value in ctx.items():
                        if name == "@vocab":
                            _id = value + _id
            else:
                contexts = self.contexts

            for ctx in contexts:
                for name, value in ctx.items():
                    if name == "@base" and self.is_relative(_id):
                        _id = value + _id

            self.__expanded.setdefault(v, {})[_id] = self.__expand(_id, contexts)

        return self.__expanded[v][_id]

    def expand(self, _id):
        return self.__expand_contexts(_id)

    def expand_vocab(self, _id, vocab=""):
        with self.vocab_push(vocab):
            if not self.__vocabs:
                v = ""
            else:
                v = self.__vocabs[-1]

            return self.__expand_contexts(_id, v, True)

    def __expand(self, _id, contexts):
        for ctx in contexts:
            if ":" not in _id:
                if _id in ctx:
                    if isinstance(ctx[_id], dict):
                        return self.__expand(ctx[_id]["@id"], contexts)
                    return self.__expand(ctx[_id], contexts)
                continue

            prefix, suffix = _id.split(":", 1)
            if prefix not in ctx:
                continue

            return self.__expand(prefix, contexts) + suffix

        return _id
