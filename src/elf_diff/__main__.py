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
from elf_diff.pair_report_document import generateDocument, ValueTreeNode
from elf_diff.plugin import Plugin, ExportPairReportPlugin, getActivePlugins
from elf_diff.default_plugins import activatePlugins, listDefaultPlugins
from elf_diff.document_explorer import getDocumentStructureDocString
from elf_diff.deprecated.mass_report import writeMassReport
from elf_diff.formatted_output import SEPARATOR
import elf_diff.error_handling as error_handling
import os
import inspect
import sys
import traceback
from typing import Optional, List

RETURN_CODE_UNRECOVERABLE_ERROR = 1
RETURN_CODE_WARNINGS_OCCURRED = 2

# Unicode characters cause problems with encoding on Windows
if os.name == "nt":
    CHECKERED_FLAG = ""
    PLEADING_FACE = ":-("
    CLOUD_WITH_RAIN = ""
    HOT_BEVERAGE = "hot coffee"
    WARNING = "Warning: "
    ERROR = "Error: "

else:
    CHECKERED_FLAG = "\U0001F3C1"
    PLEADING_FACE = "\U0001F97A"
    CLOUD_WITH_RAIN = "\U0001F327"
    HOT_BEVERAGE = "\u2615"
    WARNING = "\u26A0"
    ERROR = "\u26A0"


def exportDocument(settings: Settings) -> None:

    activatePlugins(settings)

    plugins: List[Plugin] = getActivePlugins(ExportPairReportPlugin)

    if len(plugins) == 0:
        return

    document: ValueTreeNode = generateDocument(settings)
    assert document

    for plugin in plugins:
        if isinstance(plugin, ExportPairReportPlugin):
            plugin.export(document)


def errorOutput(
    settings: Settings, exception: Exception, force_stacktrace: bool = False
):
    if force_stacktrace or (not settings) or settings.debug:
        print(SEPARATOR)
        print("")
        print(traceback.format_exc())
    else:
        print("")

    print(
        f"""\
{SEPARATOR}
 elf_diff is unconsolable {PLEADING_FACE} Something went wrong {CLOUD_WITH_RAIN}
{SEPARATOR}

 {ERROR} {exception}

{SEPARATOR}
 Don't let this take you down! Have a nice {HOT_BEVERAGE} and start over.
{SEPARATOR}
"""
    )


def processChoices(settings: Settings) -> None:
    """Process any relevant choices in the settings"""
    if settings.list_default_plugins:
        print("\n%s" % listDefaultPlugins())


def main():
    settings: Optional(Settings) = None
    try:
        module_path: str = os.path.dirname(
            os.path.realpath(inspect.getfile(inspect.currentframe()))
        )
        settings = Settings(module_path)

        processChoices(settings)

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
    except Exception as exception:
        errorOutput(settings, exception, force_stacktrace=True)
        sys.exit(RETURN_CODE_UNRECOVERABLE_ERROR)
    else:
        print(f"{CHECKERED_FLAG} Done.")

    if error_handling.WARNINGS_OCCURRED:
        print(f"{WARNING} Watch out! Warnings occurred.")
        sys.exit(RETURN_CODE_WARNINGS_OCCURRED)


if __name__ == "__main__":
    # execute only if run as the entry point into the program
    main()
