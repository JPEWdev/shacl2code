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
        "idfoostring": {
            "@id": "idfoo:string",
            "@type": "http://www.w3.org/2001/XMLSchema#string",
        },
    },
]

BASE_CONTEXT = [
    {
        "@base": "http://bar/",
    },
]


@pytest.mark.parametrize(
    "context,compact_id,expand_id",
    [
        (TEST_CONTEXTS, "nonexist", "nonexist"),
        (TEST_CONTEXTS, "foo", "http://bar/"),
        (TEST_CONTEXTS, "foo:baz", "http://bar/baz"),
        (TEST_CONTEXTS, "foobat", "http://bar/bat"),
        (TEST_CONTEXTS, "idfoo", "http://idbar/"),
        (TEST_CONTEXTS, "idfoobat", "http://idbar/bat"),
        (TEST_CONTEXTS, "foo:prefix/value", "http://bar/prefix/value"),
        (TEST_CONTEXTS, "value", "value"),
        (TEST_CONTEXTS, "v", "http://bar/vocab"),
        (TEST_CONTEXTS, "idfoostring", "http://idbar/string"),
        (BASE_CONTEXT, "foo", "http://bar/foo"),
        (BASE_CONTEXT, "_:foo", "_:foo"),
        (BASE_CONTEXT, ":foo", "http://bar/:foo"),
        (BASE_CONTEXT, "http:foo", "http:foo"),
        (BASE_CONTEXT, ":", "http://bar/:"),
        (BASE_CONTEXT, "http://foo/bar", "http://foo/bar"),
    ],
)
def test_expand_compact(context, compact_id, expand_id):
    ctx = Context(context)

    # Test expansion
    assert ctx.expand(compact_id) == expand_id

    # Test compaction
    assert ctx.compact(expand_id) == compact_id


@pytest.mark.parametrize(
    "context,compact_id,expand_id,expand_vocab,vocab",
    [
        (
            TEST_CONTEXTS,
            "value",
            "value",
            "http://bar/prefix/value",
            "http://bar/vocab",
        ),
        (
            TEST_CONTEXTS,
            "http://foo/bar",
            "http://foo/bar",
            "http://bar/prefix/http://foo/bar",
            "http://bar/vocab",
        ),
    ],
)
def test_expand_compact_vocab(context, compact_id, expand_id, expand_vocab, vocab):
    ctx = Context(context)

    # Test expansion
    assert ctx.expand(compact_id) == expand_id

    # Test compaction
    assert ctx.compact(expand_id) == compact_id

    # Test vocab expansion
    assert ctx.expand_vocab(compact_id, vocab) == expand_vocab

    # Test vocab push
    with ctx.vocab_push(vocab):
        assert ctx.expand_vocab(compact_id) == expand_vocab
        assert ctx.compact_vocab(expand_vocab) == compact_id
        # Pushed vocab should not affect regular expansion
        assert ctx.expand(compact_id) == expand_id

    assert ctx.expand_vocab(compact_id, vocab) == expand_vocab
    assert ctx.compact_vocab(expand_vocab, vocab) == compact_id

    # Vocab with no pushed or specified context is equivalent to base
    assert ctx.expand_vocab(compact_id) == expand_id
    assert ctx.compact_vocab(expand_id) == compact_id


@pytest.mark.parametrize(
    "context,compact_id,expand_id,expand_vocab,vocab",
    [
        (BASE_CONTEXT, "http://bar/foo", "http://bar/foo", None, None),
    ],
)
def test_expand(context, compact_id, expand_id, expand_vocab, vocab):
    """
    This tests expansion edge cases without checking if the compaction will
    reverse back
    """
    ctx = Context(context)
    if expand_vocab is None:
        expand_vocab = expand_id

    # Test expansion
    assert ctx.expand(compact_id) == expand_id

    # Test vocab expansion
    assert ctx.expand_vocab(compact_id, vocab) == expand_vocab

    # Test vocab push
    with ctx.vocab_push(vocab):
        assert ctx.expand_vocab(compact_id) == expand_vocab
        # Pushed vocab should not affect regular expansion
        assert ctx.expand(compact_id) == expand_id
