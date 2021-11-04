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
from elf_diff.error_handling import warning, unrecoverableError
from elf_diff.auxiliary import getDirectoryThatStoresModule
from elf_diff.settings import Settings
import importlib
import importlib.util
from typing import List, Type, Dict, Optional


class PluginConfigurationKey(object):
    def __init__(self, name: str, description: str, is_optional: bool = False):
        self.name = name
        self.description = description
        self.is_optional = is_optional


PluginConfigurationInformation = List[PluginConfigurationKey]


class Plugin(object):
    """An elf_diff plugin"""

    def __init__(self, settings: Settings, plugin_configuration: Dict[str, str]):
        self._settings: Settings = settings
        self._plugin_configuration: Dict[str, str] = plugin_configuration

        self.validateConfiguration()

    def validateConfiguration(self) -> None:
        """Validate the configuration supplied to the plugin"""
        configuration_information: PluginConfigurationInformation = type(
            self
        ).getConfigurationInformation()
        config_keys: Dict[str, PluginConfigurationKey] = {}
        for config_key in configuration_information:
            config_keys[config_key.name] = config_key

        for config_key_encountered, value in self._plugin_configuration.items():
            if config_key_encountered not in config_keys.keys():
                self.pluginUnrecoverableError(
                    "Unexpected configuration entry '%s = %s' encountered"
                    % (config_key_encountered, value)
                )

    def pluginUnrecoverableError(self, msg: str) -> None:
        """Flag an unrecoverable error in plugin scope"""
        unrecoverableError("Plugin %s: %s" % (type(self).__name__, msg))

    def isConfigurationParameterAvailable(self, name: str) -> bool:
        """Return True if the configuration parameter is available, False otherwise"""
        return name in self._plugin_configuration.keys()

    def getConfigurationParameter(self, name: str) -> str:
        """Returns the value of a configuration parameter or throw an error if unavailable"""
        if name not in self._plugin_configuration.keys():
            self.pluginUnrecoverableError("Lacking parameter '%s'" % name)

        return self._plugin_configuration[name]

    def getModulePath(self) -> str:
        """Return the directory that holds the plugin module"""
        return getDirectoryThatStoresModule(self)

    def log(self, msg: str) -> None:
        """Output a log message in plugin scope"""
        if not (
            ("quiet" in self._plugin_configuration.keys())
            and self._plugin_configuration["quiet"]
        ):
            print("Plugin %s: %s" % (type(self).__name__, msg))

    @staticmethod
    def getConfigurationInformation() -> PluginConfigurationInformation:
        """Returns plugin configuration information"""
        return [
            PluginConfigurationKey(
                name="quiet", description="Disables plugin logging", is_optional=True
            )
        ]


class ExportPairReportPlugin(Plugin):
    """A pair report plugin that exports the document tree"""

    def export(self, document):
        pass


PLUGIN_TYPES = [ExportPairReportPlugin]

REGISTERED_PLUGINS = {}

for plugin_type in PLUGIN_TYPES:
    REGISTERED_PLUGINS[plugin_type] = []


def registerPluginClass(
    settings: Settings, class_, plugin_configuration: Dict[str, str]
) -> None:
    """Register a plugin by providing its plugin class and configuration parameters"""
    for plugin_type in PLUGIN_TYPES:
        if issubclass(class_, plugin_type):
            REGISTERED_PLUGINS[plugin_type].append(
                class_(settings, plugin_configuration)
            )


def registerPlugin(settings: Settings, plugin_object) -> bool:
    """Register a plugin object"""
    class_ = type(plugin_object)
    sucessfully_registered = False
    for plugin_type in PLUGIN_TYPES:
        if issubclass(class_, plugin_type):
            REGISTERED_PLUGINS[plugin_type].append(plugin_object)
            sucessfully_registered = True
    return sucessfully_registered


def loadPluginClass(plugin_path: str, class_name: str) -> Type:
    """Load a plugin class with given name from a module with given path"""
    spec = importlib.util.spec_from_file_location("elf_diff.user_plugin", plugin_path)
    plugin_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin_module)
    return getattr(plugin_module, class_name)


def getRegisteredPlugins(plugin_type: Type) -> List:
    """Return a list of registered plugin objects of a given type"""
    return REGISTERED_PLUGINS[plugin_type]


def registerPluginsFromCommandLine(settings: Settings) -> None:
    """Register any plugins that are defined via command line switches"""
    if (not settings.load_plugin) or (len(settings.load_plugin) == 0):
        return

    print(
        "Registering %s plugin(s) defined at command line:"
        % (str(len(settings.load_plugin)))
    )

    for plugin_definition in settings.load_plugin:
        tokens: List(str) = plugin_definition.split(";")
        if len(tokens) < 2:
            warning("Ignoring strange load_plugin definition '%s'" % plugin_definition)
            continue
        path: str = tokens[0]
        class_name: str = tokens[1]

        print(
            "   module '%s', class '%s', %s configuration params"
            % (path, class_name, (len(tokens) - 2))
        )

        plugin_configuration: Dict[str, str] = {}
        for param_tokens in tokens[2:]:
            key, value = param_tokens.split("=")
            if (not key) or (not value):
                warning(
                    "Ignoring strange key value pair '%s' in plugin definition '%s'"
                    % (param_tokens, plugin_definition)
                )
                continue
            plugin_configuration[key] = value

        plugin_class: Optional(Type) = None
        try:
            plugin_class = loadPluginClass(path, class_name)
        except Exception as e:
            warning("Unable to load plugin class: %s" % e)
            continue

        registerPluginClass(settings, plugin_class, plugin_configuration)
