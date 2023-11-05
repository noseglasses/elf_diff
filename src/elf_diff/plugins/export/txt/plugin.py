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
    DocumentExplorer,
    TREE_TRAVERSAL_ALL,
    StringSink,
    GeneratorOptions,
)
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
        ).dumpDocumentTree(
            document=document,
            tree_traversal_options=TREE_TRAVERSAL_ALL,
            generator_options=GeneratorOptions(enforce_names_alpha=False),
        )

        with open(self.getConfigurationParameter("output_file"), "w") as f:
            f.write(txt_output)

    @staticmethod
    def getConfigurationInformation() -> PluginConfigurationInformation:
        """Return plugin configuration information"""
        return [PluginConfigurationKey("output_file", "The text output file")] + super(
            TXTExportPairReportPlugin, TXTExportPairReportPlugin
        ).getConfigurationInformation()


class TXTExportStatisticsPlugin(ExportPairReportPlugin):
    """A plugin class that exports statistics about the difference of two elf files as a text file"""

    def __init__(self, settings: Settings, plugin_configuration: Dict[str, str]):
        super().__init__(settings, plugin_configuration)

    def export(self, document: ValueTreeNode):
        files_differ = (
            (document.statistics.overall.delta.resource_consumption.code != 0)
            or (document.statistics.overall.delta.resource_consumption.text != 0)
            or (document.statistics.overall.delta.resource_consumption.data != 0)
            or (document.statistics.overall.delta.resource_consumption.static_ram != 0)
            or (document.statistics.overall.delta.resource_consumption.bss != 0)
            or (len(document.symbols.disappeared) > 0)
            or (len(document.symbols.appeared) > 0)
            or (len(document.symbols.similar) > 0)
            or (len(document.symbols.migrated) > 0)
        )

        with open(self.getConfigurationParameter("output_file"), "w") as f:
            f.write(
                f"""\
Statistics of elf_diff comparison of files
    old: {document.files.input.old.binary_path}
    new: {document.files.input.new.binary_path}

Difference in resource consumption:
    code:        {document.statistics.overall.delta.resource_consumption.code} bytes
    text:        {document.statistics.overall.delta.resource_consumption.text} bytes
    data:        {document.statistics.overall.delta.resource_consumption.data} bytes
    static ram:  {document.statistics.overall.delta.resource_consumption.static_ram} bytes
    bss:         {document.statistics.overall.delta.resource_consumption.bss} bytes

Symbol statistics:
    old:         {len(document.symbols.old)}
    new:         {len(document.symbols.new)}
    persisting:  {len(document.symbols.persisting)}
    disappeared: {len(document.symbols.disappeared)}
    appeared:    {len(document.symbols.appeared)}
    similar:     {len(document.symbols.similar)}
    migrated:    {len(document.symbols.migrated)}

"""
            )
            if not files_differ:
                f.write("No significant differences.")
            else:
                f.write("Files differ.")

    @staticmethod
    def getConfigurationInformation() -> PluginConfigurationInformation:
        """Return plugin configuration information"""
        return [
            PluginConfigurationKey("output_file", "The statistics text output file")
        ] + super(
            TXTExportStatisticsPlugin, TXTExportStatisticsPlugin
        ).getConfigurationInformation()
