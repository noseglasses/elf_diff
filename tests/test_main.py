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
import sys
import unittest
import os

# Add the directory of this module to the python search path
# in order to find modules from package elf_diff_test"
module_dir = os.path.dirname(sys.modules[__name__].__file__)
sys.path.append(module_dir)

from elf_diff_test.module_search_path import addDevelElfDiffModuleSearchPath
from elf_diff_test.command_line_args import processCommandLineArgs

if __name__ == "__main__":
    args = processCommandLineArgs()

    # Make elf_diff modules importable
    addDevelElfDiffModuleSearchPath()

    # Import and run any test_cases found in subdirectory
    loader = unittest.TestLoader()

    all_tests = False

    if args.test_case is None:
        tests = loader.discover(os.path.join(module_dir, "test_cases"))
    else:
        test_modules = ["test_cases.%s" % test_case for test_case in args.test_case]
        tests = loader.loadTestsFromNames(test_modules)

    test_runner = unittest.runner.TextTestRunner()
    test_runner.run(tests)
