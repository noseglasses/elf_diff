# -*- coding: utf-8 -*-

# -*- mode: python -*-
#
# elf_diff
#
# Copyright (C) 2021  Noseglasses (shinynoseglasses@gmail.com)
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with along with
# this program. If not, see <http://www.gnu.org/licenses/>.
#

from elf_diff.plugin import (
    ExportPairReportPlugin,
    PluginConfigurationKey,
    PluginConfigurationInformation,
)
from elf_diff.document_explorer import (
    generateDictionary,
    TREE_TRAVERSAL_ALL,
    GeneratorOptions,
)
from elf_diff.settings import Settings
from elf_diff.pair_report_document import ValueTreeNode
import json
from typing import Dict


class JSONExportPairReportPlugin(ExportPairReportPlugin):
    """A plugin class that exports the elf_diff document as JSON"""

    def __init__(self, settings: Settings, plugin_configuration: Dict[str, str]):
        super().__init__(settings, plugin_configuration)

    def export(
        self, document: ValueTreeNode
    ) -> None:  # pylint: disable=arguments-differ # There's no visible reason why pylint warns here
        """Export the elf_diff document as JSON"""
        generator_options = GeneratorOptions(enforce_names_alpha=False)
        dict_: dict = generateDictionary(
            document,
            tree_traversal_options=TREE_TRAVERSAL_ALL,
            generator_options=generator_options,
        )

        json_output: str = json.dumps(dict_, sort_keys=True, indent=4)

        with open(self.getConfigurationParameter("output_file"), "w") as f:
            f.write(json_output)

    @staticmethod
    def getConfigurationInformation() -> PluginConfigurationInformation:
        """Return plugin configuration information"""
        return [PluginConfigurationKey("output_file", "The JSON output file")] + super(
            JSONExportPairReportPlugin, JSONExportPairReportPlugin
        ).getConfigurationInformation()
