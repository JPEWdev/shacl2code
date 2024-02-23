#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import pytest
from shacl2code.context import Context

TEST_CONTEXTS = [
    {
        "foo": "http://bar/",
        "foobat": "foo:bat",
        "idfoo": {
            "@id": "http://idbar/",
            "@type": "@id",
        },
        "idfoobat": {
            "@id": "idfoo:bat",
            "@type": "@id",
        },
        "v": {
            "@type": "@vocab",
            "@id": "foo:vocab",
            "@context": {
                "@vocab": "foo:prefix/",
            },
        },
    },
]


@pytest.mark.parametrize(
    "in_id,out_id,vocab",
    [
        ("nonexist", "nonexist", None),
        ("http://bar/", "foo", None),
        ("http://bar/baz", "foo:baz", None),
        ("http://bar/bat", "foobat", None),
        ("http://idbar/", "idfoo", None),
        ("http://idbar/bat", "idfoobat", None),
        ("http://bar/prefix/value", "foo:prefix/value", None),
        ("http://bar/prefix/value", "value", "http://bar/vocab"),
        ("http://bar/vocab", "v", None),
    ],
)
def test_compact(in_id, out_id, vocab):
    ctx = Context(TEST_CONTEXTS)

    result = ctx.compact(in_id, vocab)
    assert result == out_id, f"Expected {out_id}, got {result}"


@pytest.mark.parametrize(
    "in_id,out_id,vocab",
    [
        ("nonexist", "nonexist", None),
        ("foo", "http://bar/", None),
        ("foo:baz", "http://bar/baz", None),
        ("foobat", "http://bar/bat", None),
        ("idfoo", "http://idbar/", None),
        ("idfoobat", "http://idbar/bat", None),
        ("foo:prefix/value", "http://bar/prefix/value", None),
        ("value", "http://bar/prefix/value", "http://bar/vocab"),
        ("value", "value", None),
        ("v", "http://bar/vocab", None),
    ],
)
def test_expand(in_id, out_id, vocab):
    ctx = Context(TEST_CONTEXTS)

    result = ctx.expand(in_id, vocab)
    assert result == out_id, f"Expected {out_id}, got {result}"
