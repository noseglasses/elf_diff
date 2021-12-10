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

from elf_diff_test.test_in_subdirs import TestCaseWithSubdirs
from elf_diff_test.elf_diff_execution import ElfDiffExecutionMixin
from elf_diff_test.test_binaries import getTestBinary

import os


class TestSymbolMigration(ElfDiffExecutionMixin, TestCaseWithSubdirs):
    def test_symbol_migration(self):
        html_dir = "migration_test_multi_page_pair_report"
        output_file = os.path.join(html_dir, "index.html")
        self.runSimpleTestBase(
            args=[
                ("html_dir", html_dir),
                ("old_source_prefix", "/home/flo/Documents/elf_diff/tests/src/old/"),
                ("new_source_prefix", "/home/flo/Documents/elf_diff/tests/src/new/"),
            ],
            old_binary_filename=getTestBinary(
                "x86_64", "migration_test", "debug", "old"
            ),
            new_binary_filename=getTestBinary(
                "x86_64", "migration_test", "debug", "new"
            ),
            output_file=output_file,
        )
