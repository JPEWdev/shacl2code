#! /usr/bin/env python3
#
# Copyright (c) 2026 Joshua Watt
#
# SPDX-License-Identifier: MIT
"""General utility functions"""


def convert_version_string(s):
    """
    Converts a version string into a tuple. The version is split by the "."
    character, and any part that can be converted to a base-10 positive integer
    is converted, otherwise it is left as a string.
    """
    if not s:
        return tuple()

    result = []
    for part in s.split("."):
        try:
            if not part.startswith("+"):
                i = int(part, 10)
                if i >= 0:
                    result.append(i)
                    continue

        except ValueError:
            pass

        result.append(part)

    return tuple(result)
