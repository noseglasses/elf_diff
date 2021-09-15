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

from elf_diff.binary import Binary
import progressbar
import sys
from difflib import get_close_matches
from difflib import SequenceMatcher


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


class BinaryPairSettings(object):
    def __init__(self, short_name, old_binary_filename, new_binary_filename):

        self.short_name = short_name
        self.old_binary_filename = old_binary_filename
        self.new_binary_filename = new_binary_filename


class SimilarityPair(object):
    def __init__(
        self, old_symbol, new_symbol, symbol_similarity, instructions_similarity
    ):
        self.old_symbol = old_symbol
        self.new_symbol = new_symbol
        self.symbol_similarity = symbol_similarity
        self.instructions_similarity = instructions_similarity
        self.instructions_equal = self.old_symbol.instructionsEqual(self.new_symbol)


class BinaryPair(object):
    def __init__(self, settings, old_binary_filename, new_binary_filename):

        self.settings = settings

        self.old_binary_filename = old_binary_filename
        self.new_binary_filename = new_binary_filename

        symbol_selection_regex_old = self.settings.symbol_selection_regex
        if self.settings.symbol_selection_regex_old is not None:
            symbol_selection_regex_old = self.settings.symbol_selection_regex_old

        symbol_selection_regex_new = self.settings.symbol_selection_regex
        if self.settings.symbol_selection_regex_new is not None:
            symbol_selection_regex_new = self.settings.symbol_selection_regex_new

        symbol_exclusion_regex_old = self.settings.symbol_exclusion_regex
        if self.settings.symbol_exclusion_regex_old is not None:
            symbol_exclusion_regex_old = self.settings.symbol_exclusion_regex_old

        symbol_exclusion_regex_new = self.settings.symbol_exclusion_regex
        if self.settings.symbol_exclusion_regex_new is not None:
            symbol_exclusion_regex_new = self.settings.symbol_exclusion_regex_new

        print("Symbol selection regex:")
        print(f"   old binary: '{symbol_selection_regex_old}'")
        print(f"   new binary: '{symbol_selection_regex_new}'")
        print("Symbol exclusion regex:")
        print(f"   old binary: '{symbol_exclusion_regex_old}'")
        print(f"   new binary: '{symbol_exclusion_regex_new}'")

        print(f"Parsing symbols of old binary ({self.old_binary_filename})")
        self.old_binary = Binary(
            self.settings,
            self.old_binary_filename,
            symbol_selection_regex_old,
            symbol_exclusion_regex_old,
        )
        print(f"Parsing symbols of new binary ({self.new_binary_filename})")
        self.new_binary = Binary(
            self.settings,
            self.new_binary_filename,
            symbol_selection_regex_new,
            symbol_exclusion_regex_new,
        )

        self.prepareSymbols()
        self.summarizeSymbols()

        self.computeSizeChanges()
        self.computeSimilarities()

    def summarizeSymbols(self):
        print("Symbol Statistics:")
        print(f"   old binary ({self.old_binary_filename}):")
        print(
            f"      {len(self.old_symbol_names) + self.old_binary.num_symbols_dropped} total symbol(s)"
        )
        print(f"      {len(self.old_symbol_names)} symbol(s) selected")
        print(f"   new binary ({self.new_binary_filename}):")
        print(
            f"      {len(self.new_symbol_names) + self.new_binary.num_symbols_dropped} total symbol(s)"
        )
        print(f"      {len(self.new_symbol_names)} symbol(s) selected")
        print("")
        print(f"   {len(self.persisting_symbol_names)} persisting symbol(s)")
        print(f"   {len(self.disappeared_symbol_names)} disappeared symbol(s)")
        print(f"   {len(self.new_symbol_names)} new symbol(s)")

    def prepareSymbols(self):

        from elf_diff.auxiliary import listIntersection

        self.old_symbol_names = set(self.old_binary.symbols.keys())
        self.new_symbol_names = set(self.new_binary.symbols.keys())

        self.persisting_symbol_names = listIntersection(
            self.old_symbol_names, self.new_symbol_names
        )
        self.disappeared_symbol_names = sorted(
            self.old_symbol_names - self.new_symbol_names
        )
        self.new_symbol_names = sorted(self.new_symbol_names - self.old_symbol_names)

    def computeSizeChanges(self):
        self.analyseSymbolSizeChanges()
        self.computeNumSymbolsDisappeared()
        self.computeNumSymbolsNew()
        self.computeNumAssembliesDiffer()

    def computeSimilarities(self):
        self.similar_symbols = self.determineSimilarSymbols()

    def determineSimilarSymbols(self):

        n_old_symbol_names = len(self.disappeared_symbol_names)

        if (n_old_symbol_names == 0) or (len(self.new_symbol_names) == 0):
            return []

        symbol_pairs = []

        similarity_threshold = float(self.settings.similarity_threshold)

        print("Detecting symbol similarities...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(n_old_symbol_names)):
            old_symbol_name = self.disappeared_symbol_names[i]
            sys.stdout.flush()

            old_symbol = self.old_binary.symbols[old_symbol_name]

            matching_symbols = get_close_matches(
                old_symbol_name, self.new_symbol_names, n=5, cutoff=similarity_threshold
            )

            for new_symbol_name in matching_symbols:
                new_symbol = self.new_binary.symbols[new_symbol_name]

                symbol_similarity = similar(old_symbol_name, new_symbol_name)

                instructions_similarity = None
                if (old_symbol.instructions is not None) and (
                    new_symbol.instructions is not None
                ):
                    instructions_similarity = similar(
                        old_symbol.instructions, new_symbol.instructions
                    )

                symbol_pairs.append(
                    SimilarityPair(
                        old_symbol=old_symbol,
                        new_symbol=new_symbol,
                        symbol_similarity=symbol_similarity,
                        instructions_similarity=instructions_similarity,
                    )
                )

        # First sort symbol pairs by symbol similarity, then by instruction similarity and finally by size
        # difference
        #
        sorted_symbol_pairs = sorted(
            symbol_pairs,
            key=lambda e: (
                e.symbol_similarity,
                e.instructions_similarity,
                e.new_symbol.size - e.old_symbol.size,
            ),
            reverse=True,
        )

        return sorted_symbol_pairs

    def analyseSymbolSizeChanges(self):

        self.num_symbol_size_changes = 0

        if len(self.persisting_symbol_names) == 0:
            return

        print("Analyzing symbol size changes...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(self.persisting_symbol_names))):
            symbol_name = self.persisting_symbol_names[i]
            old_symbol = self.old_binary.symbols[symbol_name]
            new_symbol = self.new_binary.symbols[symbol_name]
            if old_symbol.size != new_symbol.size:
                self.num_symbol_size_changes += 1

    def computeNumSymbolsDisappeared(self):
        self.num_bytes_disappeared = 0
        self.num_symbols_disappeared = len(self.disappeared_symbol_names)

        if self.num_symbols_disappeared == 0:
            return

        print("Analyzing disappeared symbols...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(self.disappeared_symbol_names))):
            symbol_name = self.disappeared_symbol_names[i]
            symbol = self.old_binary.symbols[symbol_name]
            self.num_bytes_disappeared += symbol.size

    def computeNumSymbolsNew(self):
        self.num_bytes_new = 0
        self.num_symbols_new = len(self.new_symbol_names)

        if self.num_symbols_new == 0:
            return

        print("Analyzing new symbols...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(self.new_symbol_names))):
            symbol_name = self.new_symbol_names[i]
            symbol = self.new_binary.symbols[symbol_name]
            self.num_bytes_new += symbol.size

    def computeNumAssembliesDiffer(self):
        self.num_assemblies_differ = 0

        if len(self.persisting_symbol_names) == 0:
            return

        print("Analyzing assembly differences...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(self.persisting_symbol_names))):
            symbol_name = self.persisting_symbol_names[i]
            old_symbol = self.old_binary.symbols[symbol_name]
            new_symbol = self.new_binary.symbols[symbol_name]

            if not old_symbol.__eq__(new_symbol):
                self.num_assemblies_differ += 1
