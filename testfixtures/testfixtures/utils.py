#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import pytest


def parametrize(names, data):
    params = []
    for d in data:
        params.append(d[1:])

    ids = []
    for idx, d in enumerate(data):
        ids.append(f"{idx + 1}/{len(data)}: {d[0]}")

    return pytest.mark.parametrize(names, params, ids=ids)
