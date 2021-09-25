#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# -*- mode: python -*-
#
# elf_diff
#
# Copyright (C) 2019  Noseglasses (shinynoseglasses@gmail.com)
#
# This program is free software: you can redistribute it and/or modify it under it under
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

import os
import inspect
import tempfile
from elf_diff.settings import Settings
from elf_diff.mass_report import MassReport
from elf_diff.pair_report import PairReport
from elf_diff.error_handling import warning


def convertHTMLToPDF(html_file, pdf_file):
    try:
        from weasyprint import HTML
    except ImportError:
        warning("Unable to import module weasyprint")
        warning("No pdf export supported")
        return

    HTML(html_file).write_pdf(pdf_file)


def writePairReport(settings):
    if (
        (settings.html_dir is None)
        and (settings.html_file is None)
        and (settings.pdf_file is None)
    ):
        settings.html_dir = "multipage_pair_report"
        print("No output defined. Generating multipage html report.")

    if settings.html_dir:
        multi_page_pair_report = PairReport(settings)
        multi_page_pair_report.single_page = False
        multi_page_pair_report.writeMultiPageHTMLReport()
        print(
            "Multi page html pair report written to directory '"
            + settings.html_dir
            + "'"
        )

    single_page_pair_report = None
    if settings.html_file:
        single_page_pair_report = PairReport(settings)
        single_page_pair_report.single_page = True

        single_page_pair_report.writeSinglePageHTMLReport()
        print("Single page html pair report '" + settings.html_file + "' written")

    if settings.pdf_file:

        if single_page_pair_report is None:
            single_page_pair_report = PairReport(settings)
            single_page_pair_report.single_page = True

        tmp_html_file = (
            tempfile._get_default_tempdir()
            + "/"
            + next(tempfile._get_candidate_names())
            + ".html"
        )

        single_page_pair_report.writeSinglePageHTMLReport(output_file=tmp_html_file)

        convertHTMLToPDF(tmp_html_file, settings.pdf_file)

        os.remove(tmp_html_file)

        print("Single page pdf pair report '" + settings.pdf_file + "' written")


def writeMassReport(settings):

    mass_report = MassReport(settings)
    mass_report.single_page = True

    if settings.html_file:
        mass_report.generate(settings.html_file)
        print("Single page html mass report '" + settings.html_file + "' written")

    if settings.pdf_file:

        tmp_html_file = (
            tempfile._get_default_tempdir()
            + "/"
            + next(tempfile._get_candidate_names())
            + ".html"
        )

        mass_report.generate(tmp_html_file)

        print("Temp report: " + tmp_html_file)

        convertHTMLToPDF(tmp_html_file, settings.pdf_file)

        os.remove(tmp_html_file)

        print("Single page pdf mass report '" + settings.pdf_file + "' written")


def main():

    module_path = os.path.dirname(
        os.path.realpath(inspect.getfile(inspect.currentframe()))
    )
    print("module_path = " + module_path)
    settings = Settings(module_path)

    report_generated = False

    if settings.mass_report or len(settings.mass_report_members) > 0:
        writeMassReport(settings)
        report_generated = True
    elif settings.isFirmwareBinaryDefined():
        writePairReport(settings)
        report_generated = True

    if settings.driver_template_file:
        settings.writeParameterTemplateFile(
            settings.driver_template_file, output_actual_values=report_generated
        )


if __name__ == "__main__":
    # execute only if run as the entry point into the program
    main()
