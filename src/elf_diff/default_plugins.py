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
    registerPluginClass,
    REGISTERED_PLUGINS,
    ExportPairReportPlugin,
    registerPluginsFromCommandLine,
)
from elf_diff.plugins.export.html.plugin import HTMLExportPairReportPlugin
from elf_diff.plugins.export.pdf.plugin import PDFExportPairReportPlugin
from elf_diff.plugins.export.yaml.plugin import YAMLExportPairReportPlugin
from elf_diff.plugins.export.json.plugin import JSONExportPairReportPlugin
from elf_diff.plugins.export.txt.plugin import TXTExportPairReportPlugin


def registerDefaultPlugins(settings):

    if settings.html_dir:
        plugin_configuration = {"output_dir": settings.html_dir, "single_page": False}
        registerPluginClass(settings, HTMLExportPairReportPlugin, plugin_configuration)

    if settings.html_file:
        plugin_configuration = {"output_file": settings.html_file, "single_page": True}
        registerPluginClass(settings, HTMLExportPairReportPlugin, plugin_configuration)

    if settings.pdf_file:
        plugin_configuration = {"output_file": settings.pdf_file}
        registerPluginClass(settings, PDFExportPairReportPlugin, plugin_configuration)

    if settings.yaml_file:
        plugin_configuration = {"output_file": settings.yaml_file}
        registerPluginClass(settings, YAMLExportPairReportPlugin, plugin_configuration)

    if settings.json_file:
        plugin_configuration = {"output_file": settings.json_file}
        registerPluginClass(settings, JSONExportPairReportPlugin, plugin_configuration)

    if settings.txt_file:
        plugin_configuration = {"output_file": settings.txt_file}
        registerPluginClass(settings, TXTExportPairReportPlugin, plugin_configuration)


def fallbackIfNoPluginsRegistered(settings):
    if len(REGISTERED_PLUGINS[ExportPairReportPlugin]) == 0:
        settings.html_dir = "multipage_pair_report"
        print("No output defined. Generating multipage html report.")

        plugin_configuration = {"output_dir": settings.html_dir, "single_page": False}
        registerPluginClass(settings, HTMLExportPairReportPlugin, plugin_configuration)


def registerPlugins(settings):
    registerDefaultPlugins(settings)
    registerPluginsFromCommandLine(settings)
    fallbackIfNoPluginsRegistered(settings)
