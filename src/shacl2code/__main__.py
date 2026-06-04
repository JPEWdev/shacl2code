#! /usr/bin/env python3
#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT
"""Entry point for running shacl2code as a module (python -m shacl2code)"""

import sys

from . import main

if __name__ == "__main__":
    sys.exit(main())
