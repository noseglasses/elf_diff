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

from elf_diff.error_handling import warning
from elf_diff.symbol import getSymbolType, Symbol
from elf_diff.settings import Settings
from elf_diff.mangling import Mangling
from elf_diff.source_file import SourceFile
from elf_diff.instruction_collector import InstructionCollector
from elf_diff.symbol_sizes import SymbolSizes
from elf_diff.symbol_selection import SymbolSelection
from elf_diff.binary_file_format import determineBinaryFileFormat
from elf_diff.symbol_extractor import SymbolExtractor

import os
from typing import Optional, Dict, List


class Binary(object):
    def __init__(
        self,
        settings: Settings,
        filename: str,
        symbol_selection_regex: Optional[str] = None,
        symbol_exclusion_regex: Optional[str] = None,
        mangling: Optional[Mangling] = None,
        source_prefix: Optional[List[str]] = None,
    ):
        """Init binary object."""
        self._settings: Settings = settings

        self.filename: str = filename
        self._verifyFilename()

        self._symbol_selection = SymbolSelection(
            symbol_selection_regex, symbol_exclusion_regex
        )

        self._mangling: Optional[Mangling] = mangling

        self._source_prefix: Optional[List[str]] = source_prefix

        self.symbol_sizes = SymbolSizes(filename, settings.binutils)

        if self.symbol_sizes is None:
            warning(
                "Unable to determine resource consumptions. Is the proper size utility used?"
            )
            self._binutils.is_functional = False

        self.file_format: Optional[str] = determineBinaryFileFormat(
            filename=filename, binutils=settings.binutils
        )

        self.debug_info_available: bool = False
        self.source_files: Dict[int, SourceFile] = {}
        self.symbols: Dict[str, Symbol] = {}
        self.num_symbols_dropped: int = 0

        self._initSymbols()

    def _verifyFilename(self):
        if not self.filename:
            raise Exception("No binary filename defined")
        if not os.path.isfile(self.filename):
            raise Exception(f"Unable to find filename {self.filename}")

    def _extractSymbols(self) -> None:
        """Extract symbols from the elf binary"""

        symbol_type = getSymbolType(self._settings.language)
        symbol_extractor = SymbolExtractor(
            binutils=self._settings.binutils,
            symbol_type=symbol_type,
            mangling=self._mangling,
            symbol_selection=self._symbol_selection,
            source_prefix=self._source_prefix,
        )
        symbol_extractor.extractSymbols(self.filename)

        self.symbols = symbol_extractor.symbols
        self.num_symbols_dropped = symbol_extractor.num_symbols_dropped
        self.source_files = symbol_extractor.source_files

        self.debug_info_available = symbol_extractor.debug_info_available

    def _gatherSymbolInstructions(self) -> None:
        """Gather the instructions associated with a symbol"""
        instruction_collector = InstructionCollector(symbols=self.symbols)
        instruction_collector.gatherSymbolInstructions(
            filename=self.filename,
            file_format=self.file_format,
            binutils=self._settings.binutils,
        )

        self.instructions_available: bool = len(instruction_collector.symbols) > 0

        if instruction_collector.n_instruction_lines == 0:
            warning(f"Unable to read assembly from binary '{self.filename}'.")

    def _initSymbols(self) -> None:
        """Parse symbols from the binary"""
        self._extractSymbols()
        self._gatherSymbolInstructions()

        for symbol_name_mangled in sorted(self.symbols.keys()):
            symbol = self.symbols[symbol_name_mangled]
            symbol.init()
