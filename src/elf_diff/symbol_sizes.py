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
from elf_diff.system_command import runSystemCommand
from elf_diff.binutils import Binutils
from elf_diff.error_handling import warning

import re


class SymbolSizes(object):
    def __init__(self, filename: str, binutils: Binutils):
        self.text_size: int = 0
        self.data_size: int = 0
        self.bss_size: int = 0
        self.overall_size: int = 0

        self.progmem_size: int = 0
        self.static_ram_size: int = 0

        self.initialize(filename=filename, binutils=binutils)

    def initialize(self, filename: str, binutils: Binutils) -> None:
        """Determine the sizes of symbols"""
        if binutils.size_command is None:
            warning("No binutils size command available. Unable to read symbol sizes")
            return

        size_output: str = runSystemCommand([binutils.size_command, filename])

        size_re = re.compile(r"^\s*([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)")
        for line in size_output.splitlines():
            size_match = re.match(size_re, line)
            if size_match:
                self.text_size = int(size_match.group(1))
                self.data_size = int(size_match.group(2))
                self.bss_size = int(size_match.group(3))
                self.overall_size = int(size_match.group(4))

                self.progmem_size = self.text_size + self.data_size
                self.static_ram_size = self.data_size + self.bss_size
                break
