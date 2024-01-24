#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

LANGUAGES = {}


def language(name):
    def inner(cls):
        global LANGUAGES
        LANGUAGES[name] = cls
        return cls

    return inner
