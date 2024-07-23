# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import re
from contextlib import contextmanager


def foreach_context(contexts):
    for ctx in contexts:
        for name, value in ctx.items():
            yield name, value


class Context(object):
    def __init__(self, contexts=[]):
        self.contexts = [c for c in contexts if c]
        self.__vocabs = []
        self.__expanded_iris = {}
        self.__expanded_ids = {}
        self.__expanded_vocabs = {}
        self.__compacted_iris = {}
        self.__compacted_ids = {}
        self.__compacted_vocabs = {}

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

    def __vocab_key(self):
        if not self.__vocabs:
            return ""

        return self.__vocabs[-1]

    def __get_vocab_contexts(self):
        contexts = []

        for v in self.__vocabs:
            for name, value in foreach_context(self.contexts):
                if (
                    isinstance(value, dict)
                    and value["@type"] == "@vocab"
                    and v == self.expand_iri(value["@id"])
                ):
                    if "@context" in value:
                        contexts.insert(0, value["@context"])

        contexts.extend(self.contexts)

        return contexts

    def __choose_possible(
        self,
        term,
        default,
        contexts,
        *,
        vocab=False,
        base=False,
        exact=False,
        prefix=False,
    ):
        def remove_prefix(_id, value):
            expanded_id = self.expand_iri(_id)
            expanded_value = self.expand_iri(value)

            possible = set()
            if expanded_id.startswith(expanded_value):
                tmp_id = _id[len(expanded_value) :]
                possible.add(tmp_id)
            return possible

        def helper(term):
            possible = set()
            for name, value in foreach_context(contexts):
                if name == "@vocab":
                    if vocab:
                        possible |= remove_prefix(term, value)
                    continue

                if name == "@base":
                    if base:
                        possible |= remove_prefix(term, value)
                    continue

                if isinstance(value, dict):
                    value = value["@id"]

                if term == self.expand_iri(value):
                    if exact and name not in possible:
                        possible.add(name)
                        possible |= helper(name)
                    continue

                if not prefix:
                    continue

                if term.startswith(value) and value.endswith("/"):
                    tmp_id = name + ":" + term[len(value) :].lstrip("/")
                    if tmp_id not in possible:
                        possible.add(tmp_id)
                        possible |= helper(tmp_id)
                    continue

                if term.startswith(value + ":") and self.expand_iri(value).endswith(
                    "/"
                ):
                    tmp_id = name + term[len(value) :]
                    if tmp_id not in possible:
                        possible.add(tmp_id)
                        possible |= helper(tmp_id)
                    continue

            return possible

        possible = helper(term)

        if not possible:
            return default

        # To select from the possible identifiers, choose the one that has the
        # least context (fewest ":"), then the shortest, and finally
        # alphabetically
        possible = list(possible)
        possible.sort(key=lambda p: (p.count(":"), len(p), p))
        return possible[0]

    def compact_iri(self, iri):
        if iri not in self.__compacted_iris:
            self.__compacted_iris[iri] = self.__choose_possible(
                iri,
                iri,
                self.contexts,
                exact=True,
                prefix=True,
            )

        return self.__compacted_iris[iri]

    def compact_id(self, _id):
        if ":" not in _id:
            return _id

        if _id not in self.__compacted_ids:
            self.__compacted_ids[_id] = self.__choose_possible(
                _id,
                _id,
                self.contexts,
                base=True,
                prefix=True,
            )

        return self.__compacted_ids[_id]

    def compact_vocab(self, term, vocab=None):
        with self.vocab_push(vocab):
            v = self.__vocab_key()
            if v in self.__compacted_vocabs and term in self.__compacted_vocabs[v]:
                return self.__compacted_vocabs[v][term]

            compact = self.__choose_possible(
                term,
                None,
                self.__get_vocab_contexts(),
                vocab=True,
                exact=True,
            )
            if compact is not None:
                self.__compacted_vocabs.setdefault(v, {})[term] = self.compact_id(
                    compact
                )
                return compact

        # If unable to compact with a vocabulary, compact as an ID
        return self.compact_id(term)

    def expand_iri(self, iri):
        if iri not in self.__expanded_iris:
            self.__expanded_iris[iri] = self.__expand(
                iri,
                self.contexts,
                exact=True,
                prefix=True,
            )

        return self.__expanded_iris[iri]

    def expand_id(self, _id):
        if _id not in self.__expanded_ids:
            self.__expanded_ids[_id] = self.__expand(
                _id,
                self.contexts,
                base=True,
                prefix=True,
            )

        return self.__expanded_ids[_id]

    def expand_vocab(self, term, vocab=None):
        with self.vocab_push(vocab):
            v = self.__vocab_key()
            if v not in self.__expanded_vocabs or term not in self.__expanded_vocabs[v]:
                value = self.__expand(
                    term,
                    self.__get_vocab_contexts(),
                    vocab=True,
                    exact=True,
                )
                self.__expanded_vocabs.setdefault(v, {})[term] = self.expand_id(value)

        return self.__expanded_vocabs[v][term]

    def __expand(
        self,
        term,
        contexts,
        *,
        base=False,
        exact=False,
        prefix=False,
        vocab=False,
    ):
        def helper(term):
            vocabs = []
            bases = []
            prefixes = []
            exacts = []
            is_short = not re.match(r"[^:]+:", term)

            for name, value in foreach_context(contexts):
                if name == "@vocab":
                    if vocab and is_short:
                        vocabs.append(helper(value))
                    continue

                if name == "@base":
                    if base and is_short:
                        bases.append(value)
                    continue

                if isinstance(value, dict):
                    value = value["@id"]

                if term == name:
                    if exact:
                        exacts.append(helper(value))
                    continue

                if prefix:
                    prefixes.append(name)

            for e in exacts:
                return e

            if ":" in term:
                p, suffix = term.split(":", 1)
                for name in prefixes:
                    if p == name:
                        p = self.expand_iri(p)
                        if p.endswith("/"):
                            return p + suffix

            for value in vocabs + bases:
                return value + term

            return term

        return helper(term)
