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
from elf_diff.source_file import SourceFile

from typing import Type, Optional, Dict, List, Tuple
import re
import progressbar  # type: ignore # Make mypy ignore this module
import sys


class SymbolExtractor(object):
    def __init__(
        self,
        binutils: Binutils,
        symbol_type: Type,
        mangling: Optional[Mangling],
        symbol_selection: SymbolSelection,
        source_prefix: Optional[List[str]],
    ):
        self._binutils = binutils
        self._symbol_type = symbol_type
        self._mangling = mangling
        self._symbol_selection = symbol_selection
        self._source_prefix = source_prefix

        self.symbols: Dict[str, Symbol] = {}
        self.num_symbols_dropped: int = 0
        self.source_files: Dict[int, SourceFile] = {}
        self._file_to_id: Dict[str, int] = {}

        self.debug_info_available: bool = False

    def _readNMOutput(self, filename: str, extra_flags: List[str]) -> str:
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

        cmd += extra_flags

        cmd.append(filename)

        return runSystemCommand(cmd)

    def _removeSourcePrefix(self, filename: str) -> str:
        if self._source_prefix is None:
            return filename

        for prefix in self._source_prefix:
            if filename.startswith(prefix):
                return filename[len(prefix) :]
        return filename

    def _generateSymbol(
        self,
        symbol_name: str,
        symbol_name_mangled: str,
        symbol_name_is_demangled: bool,
    ) -> Optional[Symbol]:
        """Generate a symbol based on a symbol name but only if the symbol is intented to be selected."""
        if self._symbol_selection.isSymbolSelected(symbol_name):
            return self._symbol_type(
                symbol_name,
                symbol_name_mangled,
                symbol_name_is_demangled,
            )
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
        nm_output_mangled: str = self._readNMOutput(
            filename=filename, extra_flags=["--line-numbers"]
        )
        nm_output_demangled: str = self._readNMOutput(
            filename=filename, extra_flags=["-C"]
        )

        self.num_symbols_dropped = 0
        nm_regex_mangled = re.compile(
            r"^[0-9A-Fa-f]+\s([0-9A-Fa-f]+)\s(\w)\s([^\t]+)(\t(.+))?"
        )
        nm_regex_demangled = re.compile(r"^[0-9A-Fa-f]+\s([0-9A-Fa-f]+)\s(\w)\s(.+)")
        file_line_number_regex = re.compile(r"(.*):(\d+)")
        print("Extracting symbols")
        sys.stdout.flush()
        lines_mangled = nm_output_mangled.splitlines()
        lines_demangled = nm_output_demangled.splitlines()
        for line_mangled, line_demangled in progressbar.progressbar(
            zip(lines_mangled, lines_demangled), max_value=len(lines_mangled)
        ):
            nm_match_mangled = re.match(nm_regex_mangled, line_mangled)
            nm_match_demangled = re.match(nm_regex_demangled, line_demangled)

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

                source_filename: Optional[str] = None
                line_number: Optional[int] = None
                if nm_match_mangled.group(4) is not None:
                    file_and_line_number = nm_match_mangled.group(5)
                    file_and_line_number_match = re.match(
                        file_line_number_regex, file_and_line_number
                    )
                    if file_and_line_number_match:
                        source_filename = file_and_line_number_match.group(1).replace(
                            "\\", "/"
                        )
                        line_number = int(file_and_line_number_match.group(2))

                        if (source_filename is not None) and (
                            source_filename not in self.source_files.keys()
                        ):
                            source_filename_wo_prefix = self._removeSourcePrefix(
                                source_filename
                            )
                            new_source_file = SourceFile(
                                source_filename, source_filename_wo_prefix
                            )
                            self.source_files[new_source_file.id_] = new_source_file
                            self._file_to_id[source_filename] = new_source_file.id_

                if symbol_name_mangled not in self.symbols.keys():
                    new_symbol: Optional[Symbol] = self._generateSymbol(
                        symbol_name,
                        symbol_name_mangled,
                        symbol_name_is_demangled,
                    )
                    if new_symbol is not None:
                        new_symbol.size = int(symbol_size_str)
                        new_symbol.type_ = symbol_type

                        if source_filename is not None:
                            source_id = self._file_to_id[source_filename]
                            new_symbol.source_id = source_id
                            new_symbol.source_line = line_number

                        self.symbols[new_symbol.name_mangled] = new_symbol
                    # else:
                    #    print(f"Skipping symbol {symbol_name_mangled}")
                else:
                    self.symbols[symbol_name_mangled].size = int(symbol_size_str)
                    self.symbols[symbol_name_mangled].type_ = symbol_type

        if len(self.source_files.keys()) > 0:
            self.debug_info_available = True
