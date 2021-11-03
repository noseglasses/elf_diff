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

from elf_diff.plugin import ExportPairReportPlugin


class TestExportPairReportPlugin(ExportPairReportPlugin):
    def __init__(self, settings, plugin_configuration):
        super().__init__(settings, plugin_configuration)

    def export(
        self, document
    ):  # pylint: disable=arguments-differ # There's no visible reason why pylint warns here
        print("Test plugin configuration:")
        for key, value in self.plugin_configuration.items():
            print("   %s = %s" % (key, value))
