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
    PluginConfigurationInformation,
    PluginConfigurationKey,
)
from elf_diff.settings import Settings
from elf_diff.pair_report_document import ValueTreeNode
from typing import Dict


class TestExportPairReportPlugin(ExportPairReportPlugin):
    def __init__(self, settings: Settings, plugin_configuration: Dict[str, str]):
        super().__init__(settings, plugin_configuration)

    def export(
        self, document: ValueTreeNode
    ):  # pylint: disable=arguments-differ # There's no visible reason why pylint warns here
        print("Test plugin configuration:")
        for key, value in self._plugin_configuration.items():
            print("   %s = %s" % (key, value))

    @staticmethod
    def getConfigurationInformation() -> PluginConfigurationInformation:
        """Return plugin configuration information"""
        return [
            PluginConfigurationKey(
                "magic_words",
                "Important words",
                is_optional=True,
                default="Hocus pocus",
            )
        ] + super(
            TestExportPairReportPlugin, TestExportPairReportPlugin
        ).getConfigurationInformation()
