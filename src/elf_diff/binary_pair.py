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

from elf_diff.binary import Binary
from elf_diff.binary import Mangling
from elf_diff.auxiliary import setIntersection
from elf_diff.symbol import Symbol
from elf_diff.settings import Settings
from elf_diff.binary_pair_settings import BinaryPairSettings

import progressbar  # type: ignore # Make mypy ignore this module
import sys
from difflib import get_close_matches
from difflib import SequenceMatcher
from typing import List, Optional


def similar(a: str, b: str) -> float:
    """Return the similarity ratio of two strings"""
    return SequenceMatcher(None, a, b).ratio()


class SimilarityPair(object):
    def __init__(
        self,
        old_symbol: Symbol,
        new_symbol: Symbol,
        signature_similarity: float,
        instruction_similarity: float,
    ):
        """Initialize similarity pair object."""
        self.old_symbol = old_symbol
        self.new_symbol = new_symbol
        self.signature_similarity = signature_similarity
        self.instruction_similarity = instruction_similarity
        self.instructions_equal = self.old_symbol.instructionsEqual(self.new_symbol)


class BinaryPair(object):
    def __init__(self, settings: Settings, pair_settings: BinaryPairSettings):
        """Initialize binary pair object."""
        self.settings: Settings = settings

        self.pair_settings: BinaryPairSettings = pair_settings

        symbol_selection_regex_old: str = (
            self.settings.symbol_selection_regex_old
            or self.settings.symbol_selection_regex
        )
        symbol_selection_regex_new: str = (
            self.settings.symbol_selection_regex_new
            or self.settings.symbol_selection_regex
        )

        symbol_exclusion_regex_old: str = (
            self.settings.symbol_exclusion_regex_old
            or self.settings.symbol_exclusion_regex
        )
        symbol_exclusion_regex_new: str = (
            self.settings.symbol_exclusion_regex_new
            or self.settings.symbol_exclusion_regex
        )

        print("Symbol selection regex:")
        print(f"   old binary: '{symbol_selection_regex_old}'")
        print(f"   new binary: '{symbol_selection_regex_new}'")
        print("Symbol exclusion regex:")
        print(f"   old binary: '{symbol_exclusion_regex_old}'")
        print(f"   new binary: '{symbol_exclusion_regex_new}'")

        print(
            f"Parsing symbols of old binary ({self.pair_settings.old_binary_filename})"
        )
        self.old_binary = Binary(
            self.settings,
            self.pair_settings.old_binary_filename,
            symbol_selection_regex_old,
            symbol_exclusion_regex_old,
            mangling=Mangling(settings.old_mangling_file),
            source_prefix=settings.old_source_prefix or settings.source_prefix,
        )
        print(
            f"Parsing symbols of new binary ({self.pair_settings.new_binary_filename})"
        )
        self.new_binary = Binary(
            self.settings,
            self.pair_settings.new_binary_filename,
            symbol_selection_regex_new,
            symbol_exclusion_regex_new,
            mangling=Mangling(settings.new_mangling_file),
            source_prefix=settings.new_source_prefix or settings.source_prefix,
        )

        self._verifyBinaryCompatibility()

        self._prepareSymbols()

        self._computeSizeChanges()

        self.persisting_symbol_names: List[str]

        self.similar_symbols: List[SimilarityPair] = []
        if not settings.skip_symbol_similarities:
            self._computeSimilarities()

        self.debug_info_available: bool = (
            self.new_binary.debug_info_available
            and self.old_binary.debug_info_available
        )
        self.migrated_symbol_names: List[str] = []
        if self.debug_info_available:
            self._determineMigratedSymbols()

        self._summarizeSymbols()

    def _verifyBinaryCompatibility(self) -> None:
        """Verify that both binaries are compatibility"""
        if self.old_binary.file_format != self.new_binary.file_format:
            raise Exception(
                "Binary formats incompatible. Old: %s, new: %s"
                % (self.old_binary.file_format, self.new_binary.file_format)
            )

    def _summarizeSymbols(self) -> None:
        """Print a summary of the symbols detected"""
        print("Symbol Statistics:")
        print(f"   old binary ({self.pair_settings.old_binary_filename}):")
        print(
            f"      {len(self.old_symbol_names) + self.old_binary.num_symbols_dropped} total symbol(s)"
        )
        print(f"      {len(self.old_symbol_names)} symbol(s) selected")
        print(f"   new binary ({self.pair_settings.new_binary_filename}):")
        print(
            f"      {len(self.new_symbol_names) + self.new_binary.num_symbols_dropped} total symbol(s)"
        )
        print(f"      {len(self.new_symbol_names)} symbol(s) selected")
        print("")

        if self.debug_info_available:
            migrated_symbols_info = f" ({len(self.migrated_symbol_names)} migrated)"
        else:
            migrated_symbols_info = ""

        print(
            f"   {len(self.persisting_symbol_names)} persisting symbol(s){migrated_symbols_info}"
        )
        print(f"   {len(self.disappeared_symbol_names)} disappeared symbol(s)")
        print(f"   {len(self.new_symbol_names)} new symbol(s)")

    def _preparePersistingSymbols(self) -> None:
        persisting_candidates = setIntersection(
            self.old_symbol_names, self.new_symbol_names
        )
        if not self.settings.skip_persisting_same_size:
            self.persisting_symbol_names = persisting_candidates
            return

        self.persisting_symbol_names = []
        for persisting_symbol_name in persisting_candidates:
            old_symbol = self.old_binary.symbols[persisting_symbol_name]
            new_symbol = self.new_binary.symbols[persisting_symbol_name]

            if old_symbol.size == new_symbol.size:
                continue

            self.persisting_symbol_names.append(persisting_symbol_name)

    def _prepareSymbols(self) -> None:
        """Prepare symbols"""
        self.old_symbol_names = set(self.old_binary.symbols.keys())
        self.new_symbol_names = set(self.new_binary.symbols.keys())

        self._preparePersistingSymbols()

        self.disappeared_symbol_names = sorted(
            self.old_symbol_names - self.new_symbol_names
        )
        self.appeared_symbol_names = sorted(
            self.new_symbol_names - self.old_symbol_names
        )

    def _computeSizeChanges(self) -> None:
        """Compute the size changes of symbols from old and new binary"""
        self.analyseSymbolSizeChanges()
        self.computeNumSymbolsDisappeared()
        self.computeNumSymbolsAppeared()
        self.computeNumSymbolsWithInstructionDifferences()

    def _determineMigratedSymbols(self) -> None:
        for persisting_symbol_name in self.persisting_symbol_names:
            old_symbol = self.old_binary.symbols[persisting_symbol_name]
            new_symbol = self.new_binary.symbols[persisting_symbol_name]

            if (old_symbol.source_id is None) or (new_symbol.source_id is None):
                continue

            old_source_file_wo_prefix = self.old_binary.source_files[
                old_symbol.source_id
            ].path_wo_prefix
            new_source_file_wo_prefix = self.new_binary.source_files[
                new_symbol.source_id
            ].path_wo_prefix

            if old_source_file_wo_prefix != new_source_file_wo_prefix:
                self.migrated_symbol_names.append(old_symbol.name_mangled)

    def _computeSimilarities(self) -> None:
        """Compute the similarity rations of symbols from old and new binary"""
        self.similar_symbols = self.determineSimilarSymbols()

    def determineSimilarSymbols(self) -> List[SimilarityPair]:
        """Find pairs of symbols from old and new binary that are similar"""
        n_disappeared_symbol_names: int = len(self.disappeared_symbol_names)

        if (n_disappeared_symbol_names == 0) or (len(self.new_symbol_names) == 0):
            return []

        symbol_pairs: List[SimilarityPair] = []

        similarity_threshold = float(self.settings.similarity_threshold)

        print("Detecting symbol similarities...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(n_disappeared_symbol_names)):
            old_symbol_name: str = self.disappeared_symbol_names[i]
            sys.stdout.flush()

            old_symbol: Symbol = self.old_binary.symbols[old_symbol_name]

            matching_symbols: List[str] = get_close_matches(
                old_symbol_name, self.new_symbol_names, n=5, cutoff=similarity_threshold
            )

            for new_symbol_name in matching_symbols:
                new_symbol: Symbol = self.new_binary.symbols[new_symbol_name]

                signature_similarity: float = similar(old_symbol_name, new_symbol_name)

                instruction_similarity: Optional[float] = None
                if (old_symbol.instructions is not None) and (
                    new_symbol.instructions is not None
                ):
                    instruction_similarity = similar(
                        old_symbol.instructions, new_symbol.instructions
                    )

                symbol_pairs.append(
                    SimilarityPair(
                        old_symbol=old_symbol,
                        new_symbol=new_symbol,
                        signature_similarity=signature_similarity,
                        instruction_similarity=instruction_similarity,
                    )
                )

        # First sort symbol pairs by symbol similarity, then by instruction similarity and finally by size
        # difference
        #
        sorted_symbol_pairs: List[SimilarityPair] = sorted(
            symbol_pairs,
            key=lambda e: (
                e.signature_similarity,
                e.instruction_similarity,
                e.new_symbol.size - e.old_symbol.size,
            ),
            reverse=True,
        )

        return sorted_symbol_pairs

    def analyseSymbolSizeChanges(self) -> None:
        """Determine the number of symbol size changes"""
        self.num_symbol_size_changes: int = 0

        if len(self.persisting_symbol_names) == 0:
            return

        print("Analyzing symbol size changes...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(self.persisting_symbol_names))):
            symbol_name: str = self.persisting_symbol_names[i]
            old_symbol: Symbol = self.old_binary.symbols[symbol_name]
            new_symbol: Symbol = self.new_binary.symbols[symbol_name]
            if old_symbol.size != new_symbol.size:
                self.num_symbol_size_changes += 1

    def computeNumSymbolsDisappeared(self) -> None:
        """Determine the number of disappeared symbols"""
        self.num_bytes_disappeared: int = 0
        self.num_symbols_disappeared: int = len(self.disappeared_symbol_names)

        if self.num_symbols_disappeared == 0:
            return

        print("Analyzing disappeared symbols...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(self.disappeared_symbol_names))):
            symbol_name: str = self.disappeared_symbol_names[i]
            symbol: Symbol = self.old_binary.symbols[symbol_name]
            self.num_bytes_disappeared += symbol.size

    def computeNumSymbolsAppeared(self):
        """Determine the number of appeared symbols"""
        self.num_bytes_appeared: int = 0
        self.num_symbols_appeared: int = len(self.appeared_symbol_names)

        if self.num_symbols_appeared == 0:
            return

        print("Analyzing appeared symbols...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(self.appeared_symbol_names))):
            symbol_name: str = self.appeared_symbol_names[i]
            symbol: Symbol = self.new_binary.symbols[symbol_name]
            self.num_bytes_appeared += symbol.size

    def computeNumSymbolsWithInstructionDifferences(self):
        """Determine the number of symbols with instruction differences between new and old version"""
        self.num_symbols_with_instruction_differences: int = 0

        if len(self.persisting_symbol_names) == 0:
            return

        print("Analyzing instruction differences...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(self.persisting_symbol_names))):
            symbol_name: str = self.persisting_symbol_names[i]
            old_symbol: Symbol = self.old_binary.symbols[symbol_name]
            new_symbol: Symbol = self.new_binary.symbols[symbol_name]

            if not old_symbol.__eq__(new_symbol):
                self.num_symbols_with_instruction_differences += 1
