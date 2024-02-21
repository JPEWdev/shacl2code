#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from .common import BasicJinjaRender
from .lang import language, TEMPLATE_DIR


@language("jsonschema")
class JsonSchemaRender(BasicJinjaRender):
    HELP = "JSON Schema"

    def __init__(self, args):
        super().__init__(args, TEMPLATE_DIR / "jsonschema.j2")
        self.__schema_title = args.title
        self.__schema_id = args.id

    @classmethod
    def get_arguments(cls, parser):
        super().get_arguments(parser)

        parser.add_argument("--title", help="Schema title")
        parser.add_argument("--id", help="Schema ID")

    def get_additional_render_args(self):
        return {
            "schema_title": self.__schema_title,
            "schema_id": self.__schema_id,
        }
