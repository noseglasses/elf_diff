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
from elf_diff.document_explorer import DocumentExplorer, TREE_TRAVERSAL_ALL, StringSink
from elf_diff.settings import Settings
from elf_diff.pair_report_document import ValueTreeNode
from typing import Dict


class TXTExportPairReportPlugin(ExportPairReportPlugin):
    """A plugin class that exports the elf_diff document as a text file"""

    def __init__(self, settings: Settings, plugin_configuration: Dict[str, str]):
        super().__init__(settings, plugin_configuration)

    def export(self, document: ValueTreeNode):
        txt_output: str = DocumentExplorer(
            StringSink, display_values=True
        ).dumpDocumentTree(document=document, tree_traversal_options=TREE_TRAVERSAL_ALL)

        with open(self.getConfigurationParameter("output_file"), "w") as f:
            f.write(txt_output)

    @staticmethod
    def getConfigurationInformation() -> PluginConfigurationInformation:
        """Return plugin configuration information"""
        return [PluginConfigurationKey("output_file", "The text output file")] + super(
            TXTExportPairReportPlugin, TXTExportPairReportPlugin
        ).getConfigurationInformation()
