# -*- coding: utf-8 -*-

# -*- mode: python -*-
#
# elf_diff
#
# Copyright (C) 2019  Noseglasses (shinynoseglasses@gmail.com)
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

from elf_diff.settings import Settings
from elf_diff.pair_report_document import generateDocument
from elf_diff.plugin import ExportPairReportPlugin, getRegisteredPlugins
from elf_diff.default_plugins import registerPlugins
from elf_diff.document_explorer import getDocumentStructureDocString
from elf_diff.deprecated.mass_report import writeMassReport
import elf_diff.error_handling as error_handling
import os
import inspect
import sys
import traceback
from typing import Optional


def exportDocument(settings):

    registerPlugins(settings)

    plugins = getRegisteredPlugins(ExportPairReportPlugin)

    if len(plugins) == 0:
        return

    document = generateDocument(settings)
    assert document

    for plugin in plugins:
        plugin.export(document)


def errorOutput():
    separator = "═" * 80
    if (not settings) or settings.debug:
        print(separator)
        print("")
        print(traceback.format_exc())
    else:
        print("")

    pleading_face = "\U0001F97A"
    cloud_with_rain = "\U0001F327"
    hot_beverage = "\u2615"
    warning = "\u26A0"

    print(
        f"""\
{separator}
 elf_diff is unconsolable {pleading_face} but something went wrong {cloud_with_rain}
{separator}

 {warning} {e}

{separator}
 Don't let this take you down! Have a nice {hot_beverage} and start over.
{separator}
"""
    )


def main():
    errors_occurred = False
    settings: Optional(Settings) = None
    try:
        module_path = os.path.dirname(
            os.path.realpath(inspect.getfile(inspect.currentframe()))
        )
        settings = Settings(module_path)

        report_generated = False

        if settings.dump_document_structure:
            print("\n%s" % getDocumentStructureDocString(settings))

        if settings.mass_report or len(settings.mass_report_members) > 0:
            writeMassReport(settings)
            report_generated = True
        elif settings.isFirmwareBinaryDefined():
            exportDocument(settings)
            report_generated = True

        if settings.driver_template_file:
            settings.writeParameterTemplateFile(
                settings.driver_template_file, output_actual_values=report_generated
            )
    except Exception as e:

        errorOutput()
        errors_occurred = True
        sys.exit(1)
    else:
        chequered_flag = "\U0001F3C1"
        print(f"{chequered_flag} Done.")

    if error_handling.WARNINGS_OCCURRED:
        warning = "\u26A0"
        print(f"{warning} Watch out! Warnings occurred.")
        sys.exit(1)


if __name__ == "__main__":
    # execute only if run as the entry point into the program
    main()
