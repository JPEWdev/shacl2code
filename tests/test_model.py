#
# Copyright (c) 2026 Joshua Watt
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest

import rdflib

import shacl2code.model

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent


@pytest.fixture(scope="session")
def model():
    g = rdflib.Graph()
    g.parse(THIS_DIR / "data" / "model" / "test.ttl")
    return shacl2code.model.Model(g)


def test_model_ontology(model):
    assert len(model.classes) > 0
    assert len(model.ontologies) == 1

    for c in model.classes:
        assert c.ontology is model.ontologies[0]
        for i in c.named_individuals:
            assert i.ontology is model.ontologies[0]
