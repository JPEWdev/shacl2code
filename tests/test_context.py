#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import pytest
import json
import subprocess
from shacl2code.context import Context

TEST_CONTEXTS = [
    {
        "root": "http://root/",
        "rootPrefix1": "root:prefix1/",
        "rootPrefix2": "rootPrefix1:prefix2/",
        "rootTerminal1": "root:terminal",
        "rootTerminal2": "rootTerminal1:terminal2",
        "idProperty": {
            "@id": "root:property",
            "@type": "@id",
        },
        "vocabProperty": {
            "@type": "@vocab",
            "@id": "root:vocab",
            "@context": {
                "@vocab": "root:vocabPrefix/",
            },
        },
        "rootVocabProperty": {
            "@type": "@vocab",
            "@id": "root:rootVocab",
        },
        "named": "root:named",
    }
]

BASE_CONTEXT = [
    {
        "@base": "http://base/",
    },
]


@pytest.mark.parametrize(
    "extra_contexts,compact",
    [
        ([], "nonexist"),
        ([], "root"),
        ([], "rootPrefix1"),
        ([], "rootPrefix2"),
        # Test a "Hidden" prefix where the prefix itself doesn't have a
        # trailing "/", but it aliases a prefix which does
        ([{"h": "rootPrefix2"}], "h:a"),
        ([], "rootPrefix2:test"),
        ([], "rootPrefix2:test/suffix"),
        ([], "rootTerminal1"),
        ([], "rootTerminal1:suffix"),
        ([], "rootTerminal2"),
        ([], "rootTerminal2:suffix"),
        ([], "idProperty"),
        ([], "vocabProperty"),
        ([], "named"),
        ([], "named:suffix"),
        ([], "named/suffix"),
        ([], "_:blank"),
        ([], "http:url"),
    ],
)
def test_expand_compact(extra_contexts, compact):
    def test_context(contexts, compact):
        ctx = Context(TEST_CONTEXTS + contexts)
        root_vocab = ctx.expand_iri("rootVocabProperty")
        vocab = ctx.expand_iri("vocabProperty")

        data = {
            "@context": TEST_CONTEXTS + contexts,
            "@id": compact,
            "_:key": {
                "@id": "_:id",
                compact: "foo",
            },
            "_:value": compact,
            "rootVocabProperty": compact,
            "vocabProperty": compact,
        }

        p = subprocess.run(
            ["npm", "exec", "--", "jsonld-cli", "expand", "-"],
            input=json.dumps(data),
            stdout=subprocess.PIPE,
            encoding="utf-8",
            check=True,
        )
        result = json.loads(p.stdout)[0]

        expand_id = result["@id"]
        for k in result["_:key"][0].keys():
            if k == "@id":
                continue
            expand_iri = k
            break
        else:
            expand_iri = compact

        expand_root_vocab = result["http://root/rootVocab"][0]["@id"]
        expand_vocab = result["http://root/vocab"][0]["@id"]

        assert result["_:value"][0]["@value"] == compact

        def check(actual, expected, desc):
            if actual != expected:
                print(json.dumps(data, indent=2))
                assert False, f"{desc} failed: {actual!r} != {expected!r}"

        check(ctx.expand_iri(compact), expand_iri, "Expand IRI")
        check(ctx.expand_id(compact), expand_id, "Expand ID")
        check(ctx.expand_vocab(compact, vocab), expand_vocab, "Expand vocab")
        check(ctx.expand_vocab(compact, None), expand_root_vocab, "Expand no vocab")
        check(
            ctx.expand_vocab(compact, root_vocab),
            expand_root_vocab,
            "Expand root vocab",
        )

        check(ctx.compact_iri(expand_iri), compact, "Compact IRI")
        check(ctx.compact_id(expand_id), compact, "Compact ID")
        check(ctx.compact_vocab(expand_vocab, vocab), compact, "Compact vocab")
        check(ctx.compact_vocab(expand_root_vocab, None), compact, "Compact no vocab")
        check(
            ctx.compact_vocab(expand_root_vocab, root_vocab),
            compact,
            "Compact root vocab",
        )

    test_context(extra_contexts, compact)
    test_context(BASE_CONTEXT + extra_contexts, compact)
