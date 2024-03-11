#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import pytest
import itertools
from shacl2code.model import common_prefix


@pytest.mark.parametrize(
    "data,expected",
    [
        ([], ""),
        (["abc", "cde"], ""),
        (["abc", "abc"], "abc"),
        (["abc", "abcd"], "abc"),
        (["abc1", "abc2"], "abc"),
        (["abc", "abc", "abc"], "abc"),
        (["abc1", "abc", "abc"], "abc"),
        (["abc1", "abc2", "abc"], "abc"),
        (["abc1", "abc2", "abc3"], "abc"),
        (["abc1", "abc1", "abc"], "abc"),
        (["abc1", "abc1", "abc2"], "abc"),
    ],
)
def test_common_prefix(data, expected):
    for p in itertools.permutations(data):
        result = common_prefix(*p)
        assert result == expected, f"{p!r}: Got {result}, expected {expected}"
