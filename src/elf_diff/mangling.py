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
from typing import Optional, Dict, List, Tuple
import os


class Mangling(object):
    def __init__(self, mangling_file: Optional[str]):
        """Init mangling class."""
        self._mangling_file: Optional[str] = mangling_file
        self._mangling: Optional[Dict[str, str]] = None

        self._setupMangling()

    def _setupMangling(self) -> None:
        """Setup the mangling by reading symbols from a mangling file"""
        if self._mangling_file is None:
            return
        if not os.path.isfile(self._mangling_file):
            return
        with open(self._mangling_file, "r") as f:
            lines: List[str] = f.read().splitlines()
            self._mangling = {}
            line_id: int = 0
            # Read line pairs, first line is mangled, second line is demangled symbol
            for line in lines:
                if line_id == 0:
                    mangled_symbol: str = line
                else:
                    demangled_symbol: str = line
                    self._mangling[mangled_symbol] = demangled_symbol
                line_id = (line_id + 1) % 2

            print(
                "Mangling info of "
                + str(len(self._mangling))
                + " symbols read from file '"
                + self._mangling_file
                + "'"
            )

    def demangle(self, symbol_name: str) -> Tuple[str, bool]:
        """Try to demangle a symbol"""
        if self._mangling is None:
            return symbol_name, False
        if symbol_name in self._mangling.keys():
            return self._mangling[symbol_name], True

        return symbol_name, False
