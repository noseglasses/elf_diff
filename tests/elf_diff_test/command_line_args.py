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
import sys
import argparse

from .elf_diff_execution import usePackagedElfDiff, useElfDiffFromDevelopmentTree


def processCommandLineArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--test_installed_package",
        action="store_true",
        help="Add this flag to enable testing using an installed elf_diff package",
    )
    parser.add_argument(
        "-c",
        "--enable_code_coverage",
        action="store_true",
        help="Add this flag to enable coverage generation",
    )
    parser.add_argument(
        "-t", "--test_case", action="append", help="Run a given test case"
    )

    args, unittest_args = parser.parse_known_args()

    # Now set the sys.argv to the unittest_args (leaving sys.argv[0] alone)
    sys.argv[1:] = unittest_args

    if args.test_installed_package is True:
        usePackagedElfDiff()
    else:
        useElfDiffFromDevelopmentTree(args.enable_code_coverage)

    return args
