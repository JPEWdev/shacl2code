#
# Copyright © 2024, Oracle and/or its affiliates
#
# SPDX-License-Identifier: MIT

from .common import BasicJinjaRender
from .lang import language, TEMPLATE_DIR

import re
import keyword


def export(name):
    # export converts the shacl name into an exportable go type name
    name_list = name.split('_')
    for i in range(0,len(name_list)):
        name_list[i] = name_list[i][0].upper() + name_list[i][1:]
    return ''.join(name_list)


@language("golang")
class GolangRender(BasicJinjaRender):
    HELP = "Go Language Bindings"

    def __init__(self, args):
        super().__init__(args, TEMPLATE_DIR / "golang.j2")

    def get_extra_env(self):
        return {
                "export": export,
                }
