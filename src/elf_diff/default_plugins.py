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
    activatePluginByType,
    ACTIVE_PLUGINS,
    ExportPairReportPlugin,
    activatePluginsFromCommandLine,
)
from elf_diff.error_handling import warning
from elf_diff.plugins.export.html.plugin import HTMLExportPairReportPlugin
from elf_diff.plugins.export.pdf.plugin import PDFExportPairReportPlugin
from elf_diff.plugins.export.yaml.plugin import YAMLExportPairReportPlugin
from elf_diff.plugins.export.json.plugin import JSONExportPairReportPlugin
from elf_diff.plugins.export.txt.plugin import TXTExportPairReportPlugin
from elf_diff.plugins.export.xml.plugin import XMLExportPairReportPlugin
from elf_diff.settings import Settings
from typing import Dict, Type, List

DEFAULT_PLUGIN_TYPES: Dict[str, Type] = {
    "html_export": HTMLExportPairReportPlugin,
    "pdf_export": PDFExportPairReportPlugin,
    "yaml_export": YAMLExportPairReportPlugin,
    "json_export": JSONExportPairReportPlugin,
    "txt_export": TXTExportPairReportPlugin,
    "xml_export": XMLExportPairReportPlugin,
}


def activateDefaultPlugin(
    settings: Settings, plugin_type: Type, plugin_configuration: Dict[str, str]
) -> None:
    if plugin_type not in DEFAULT_PLUGIN_TYPES.values():
        raise Exception(
            f"Attempting to activate an unregistered default plugin '{plugin_type.__name__}'"
        )
    activatePluginByType(settings, plugin_type, plugin_configuration)


def activateDefaultPlugins(settings: Settings) -> None:

    if settings.html_dir:
        plugin_configuration = {"output_dir": settings.html_dir, "single_page": "False"}
        activateDefaultPlugin(
            settings, HTMLExportPairReportPlugin, plugin_configuration
        )

    if settings.html_file:
        plugin_configuration = {
            "output_file": settings.html_file,
            "single_page": "True",
        }
        activateDefaultPlugin(
            settings, HTMLExportPairReportPlugin, plugin_configuration
        )

    if settings.pdf_file:
        plugin_configuration = {"output_file": settings.pdf_file}
        activateDefaultPlugin(settings, PDFExportPairReportPlugin, plugin_configuration)

    if settings.yaml_file:
        plugin_configuration = {"output_file": settings.yaml_file}
        activateDefaultPlugin(
            settings, YAMLExportPairReportPlugin, plugin_configuration
        )

    if settings.json_file:
        plugin_configuration = {"output_file": settings.json_file}
        activateDefaultPlugin(
            settings, JSONExportPairReportPlugin, plugin_configuration
        )

    if settings.txt_file:
        plugin_configuration = {"output_file": settings.txt_file}
        activateDefaultPlugin(settings, TXTExportPairReportPlugin, plugin_configuration)

    if settings.xml_file:
        plugin_configuration = {"output_file": settings.xml_file}
        activateDefaultPlugin(settings, XMLExportPairReportPlugin, plugin_configuration)


def listDefaultPlugins() -> str:
    output: str = "Default plugins:\n"
    for alias, plugin_type in DEFAULT_PLUGIN_TYPES.items():
        configuration_information = plugin_type.getConfigurationInformation()
        output += f"{alias}:\n"
        for k in sorted(
            configuration_information,
            key=lambda configuration_key: configuration_key.name,
        ):
            if k.is_optional:
                optional_info = " (optional)"
            else:
                optional_info = ""
            output += f"   {k.name}{optional_info}: {k.description}\n"
    return output


def fallbackIfNoPluginsRegistered(settings: Settings) -> None:
    if len(ACTIVE_PLUGINS[ExportPairReportPlugin]) == 0:
        settings.html_dir = "multipage_pair_report"
        print("No exports defined. Falling back to generating multipage html report.")

        plugin_configuration: Dict[str, str] = {
            "output_dir": settings.html_dir,
            "single_page": "False",
        }
        activatePluginByType(settings, HTMLExportPairReportPlugin, plugin_configuration)


def activateDefaultPluginsFromCommandLine(settings: Settings) -> None:
    """Register any plugins that are defined via command line switches"""
    if (not settings.load_default_plugin) or (len(settings.load_default_plugin) == 0):
        return

    print(
        "Registering %s default plugin(s) defined at command line:"
        % (str(len(settings.load_default_plugin)))
    )

    for plugin_definition in settings.load_default_plugin:
        tokens: List[str] = plugin_definition.split(";")
        if len(tokens) < 1:
            warning(
                "Ignoring strange load_default_plugin definition '%s'"
                % plugin_definition
            )
            continue
        plugin_alias: str = tokens[0]

        print(
            "   '%s': %s configuration parameters" % (plugin_alias, (len(tokens) - 1))
        )

        plugin_configuration: Dict[str, str] = {}
        for param_tokens in tokens[1:]:
            key, value = param_tokens.split("=")
            if (not key) or (not value):
                warning(
                    "Ignoring strange key value pair '%s' in plugin definition '%s'"
                    % (param_tokens, plugin_definition)
                )
                continue
            print(f"      {key} = '{value}'")
            plugin_configuration[key] = value

        if plugin_alias not in DEFAULT_PLUGIN_TYPES.keys():
            warning(f"Unable to load unknown default plugin: {plugin_alias}")
            continue
        plugin_type = DEFAULT_PLUGIN_TYPES[plugin_alias]

        activatePluginByType(settings, plugin_type, plugin_configuration)


def activatePlugins(settings: Settings) -> None:
    activateDefaultPlugins(settings)
    activatePluginsFromCommandLine(settings)
    activateDefaultPluginsFromCommandLine(settings)
    fallbackIfNoPluginsRegistered(settings)
