#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from .common import BasicJinjaRender
from .lang import language, TEMPLATE_DIR

import re
import keyword


def varname(*name):
    name = str("_".join(name)).replace("@", "_")
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    while keyword.iskeyword(name):
        name = name + "_"
    return name


@language("jsonschema")
class JsonSchemaRender(BasicJinjaRender):
    HELP = "JSON Schema"

    def __init__(self, args):
        super().__init__(args, TEMPLATE_DIR / "jsonschema.j2")
        self.__render_args = {
            "schema_title": args.title,
            "schema_id": args.id,
            "allow_elided_lists": args.allow_elided_lists,
        }

    @classmethod
    def get_arguments(cls, parser):
        super().get_arguments(parser)

        parser.add_argument("--title", help="Schema title")
        parser.add_argument("--id", help="Schema ID")
        parser.add_argument(
            "--allow-elided-lists",
            action="store_true",
            help="Allow lists to be elided if they only contain a single element",
        )

    def get_extra_env(self):
        return {
            "varname": varname,
        }

    def get_additional_render_args(self):
        return self.__render_args
