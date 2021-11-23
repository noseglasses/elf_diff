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
from elf_diff.symbol import Symbol
from elf_diff.system_command import runSystemCommand
from elf_diff.mangling import Mangling
from elf_diff.symbol_selection import SymbolSelection
from elf_diff.binutils import Binutils

from typing import Type, Optional, Dict, List, Tuple
import re


class SymbolExtractor(object):
    def __init__(
        self,
        binutils: Binutils,
        symbol_type: Type,
        mangling: Optional[Mangling],
        symbol_selection: SymbolSelection,
    ):
        self._binutils = binutils
        self._symbol_type = symbol_type
        self._mangling = mangling
        self._symbol_selection = symbol_selection

        self.symbols: Dict[str, Symbol] = {}
        self.num_symbols_dropped = 0

    def _readNMOutput(self, filename: str, demangle: bool) -> str:
        """Read the output of the nm command applied to the binary"""
        if self._binutils.nm_command is None:
            raise Exception(
                "Binutils nm command unavailable. Unable to extract symbols."
            )

        cmd: List[str] = [
            self._binutils.nm_command,
            "--print-size",
            "--size-sort",
            "--radix=d",
        ]

        if demangle:
            cmd.append("-C")

        cmd.append(filename)

        return runSystemCommand(cmd)

    def _generateSymbol(
        self,
        symbol_name: str,
        symbol_name_mangled: str,
        symbol_name_is_demangled: bool,
    ) -> Optional[Symbol]:
        """Generate a symbol based on a symbol name but only if the symbol is intented to be selected."""
        if self._symbol_selection.isSymbolSelected(symbol_name):
            # print("Considering symbol " + symbol_name)
            return self._symbol_type(
                symbol_name,
                symbol_name_mangled,
                symbol_name_is_demangled,
            )
        # print("Ignoring symbol " + symbol_name)
        self.num_symbols_dropped += 1
        return None

    def _demangle(
        self, symbol_name_with_mangling_state_unknown: str
    ) -> Tuple[str, bool]:
        """Try to demangle a symbol name"""
        if self._mangling is not None:
            symbol_name_demangled: str
            was_demangled: bool
            symbol_name_demangled, was_demangled = self._mangling.demangle(
                symbol_name_with_mangling_state_unknown
            )

            if was_demangled:
                return symbol_name_demangled, True  # is demangled

        if self._binutils.is_functional:
            return (
                symbol_name_with_mangling_state_unknown,
                True,
            )  # Binutils work, so we expect demangling having already taken place

        return (
            symbol_name_with_mangling_state_unknown,
            False,
        )  # Neither explicit demangling, nor binutils demangling worked

    def extractSymbols(self, filename: str) -> None:
        """Gather the properties of a symbol"""
        nm_output_mangled: str = self._readNMOutput(filename=filename, demangle=False)
        nm_output_demangled: str = self._readNMOutput(filename=filename, demangle=True)

        self.num_symbols_dropped = 0
        nm_regex = re.compile(r"^[0-9A-Fa-f]+\s([0-9A-Fa-f]+)\s(\w)\s(.+)")
        for line_mangled, line_demangled in zip(
            nm_output_mangled.splitlines(), nm_output_demangled.splitlines()
        ):
            nm_match_mangled = re.match(nm_regex, line_mangled)
            nm_match_demangled = re.match(nm_regex, line_demangled)

            if nm_match_mangled and nm_match_demangled:
                symbol_size_str: str = nm_match_mangled.group(1)
                symbol_type: str = nm_match_mangled.group(2)

                symbol_name_mangled: str = nm_match_mangled.group(3)
                symbol_name_with_mangling_state_unknown: str = nm_match_demangled.group(
                    3
                )

                symbol_name: str
                symbol_name_is_demangled: bool
                (
                    symbol_name,
                    symbol_name_is_demangled,
                ) = self._demangle(symbol_name_with_mangling_state_unknown)

                if symbol_name_mangled not in self.symbols.keys():
                    new_symbol: Optional[Symbol] = self._generateSymbol(
                        symbol_name,
                        symbol_name_mangled,
                        symbol_name_is_demangled,
                    )
                    if new_symbol is not None:
                        new_symbol.size = int(symbol_size_str)
                        new_symbol.type_ = symbol_type
                        self.symbols[new_symbol.name_mangled] = new_symbol
                else:
                    self.symbols[symbol_name_mangled].size = int(symbol_size_str)
                    self.symbols[symbol_name_mangled].type_ = symbol_type
