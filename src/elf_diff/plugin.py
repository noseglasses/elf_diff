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
import importlib
import importlib.util


class Plugin(object):
    def __init__(self, settings, plugin_configuration):
        self.settings = settings
        self.plugin_configuration = plugin_configuration

    def pluginUnrecoverableError(self, msg):
        unrecoverableError("Plugin %s: %s" % (type(self).__name__, msg))

    def getConfigurationParameter(self, name):
        if name not in self.plugin_configuration.keys():
            self.pluginUnrecoverableError("Lacking parameter '%s'" % name)

        return self.plugin_configuration[name]

    def getPluginLocation(self):
        return getDirectoryThatStoresModule(self)

    def log(self, msg):
        if not (
            ("quiet" in self.plugin_configuration.keys())
            and self.plugin_configuration["quiet"]
        ):
            print(msg)


class ExportPairReportPlugin(Plugin):
    def export(self, document):
        pass


plugin_types = [ExportPairReportPlugin]

REGISTERED_PLUGINS = {}

for plugin_type in plugin_types:
    REGISTERED_PLUGINS[plugin_type] = []


def importPluginClass(directory, name):
    module_name, _, class_name = name.rpartition(".")
    module = importlib.import_module(module_name)
    class_ = getattr(module, class_name)

    if class_ is None:
        warning(
            "Unable to import plugin class '%s' from directory '%s'" % (name, directory)
        )
        return None

    return class_


def registerPluginClass(settings, class_, plugin_configuration):
    for plugin_type in plugin_types:
        if issubclass(class_, plugin_type):
            REGISTERED_PLUGINS[plugin_type].append(
                class_(settings, plugin_configuration)
            )


def registerPlugin(settings, plugin_object):
    class_ = type(plugin_object)
    sucessfully_registered = False
    for plugin_type in plugin_types:
        if issubclass(class_, plugin_type):
            REGISTERED_PLUGINS[plugin_type].append(plugin_object)
            sucessfully_registered = True
    return sucessfully_registered


def loadPluginObject(plugin_path, class_name):
    spec = importlib.util.spec_from_file_location("elf_diff.user_plugin", plugin_path)
    plugin_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin_module)
    return getattr(plugin_module, class_name)


def getRegisteredPlugins(plugin_type):
    return REGISTERED_PLUGINS[plugin_type]


def registerPluginsFromCommandLine(settings):
    if (not settings.load_plugin) or (len(settings.load_plugin) == 0):
        return

    print(
        "Registering %s plugin(s) defined at command line:"
        % (str(len(settings.load_plugin)))
    )

    for plugin_definition in settings.load_plugin:
        tokens = plugin_definition.split(";")
        if len(tokens) < 2:
            warning("Ignoring strange load_plugin definition '%s'" % plugin_definition)
            continue
        path = tokens[0]
        class_name = tokens[1]

        print(
            "   module '%s', class '%s', %s configuration params"
            % (path, class_name, (len(tokens) - 2))
        )

        plugin_configuration = {}
        for param_tokens in tokens[2:]:
            key, value = param_tokens.split("=")
            if (not key) or (not value):
                warning(
                    "Ignoring strange key value pair '%s' in plugin definition '%s'"
                    % (param_tokens, plugin_definition)
                )
                continue
            plugin_configuration[key] = value

        plugin_class = None
        try:
            plugin_class = loadPluginObject(path, class_name)
        except Exception as e:
            warning("Unable to load plugin class: %s" % e)
            continue

        registerPluginClass(settings, plugin_class, plugin_configuration)
