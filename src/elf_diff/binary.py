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

from elf_diff.error_handling import unrecoverableError
from elf_diff.error_handling import warning
from elf_diff.symbol import getSymbolType

import re
import os
import subprocess  # nosec # silence bandid warning


SOURCE_CODE_START_TAG = "...ED_SOURCE_START..."
SOURCE_CODE_END_TAG = "...ED_SOURCE_END..."


def preHighlightSourceCode(src):
    """Tag the start and end of source code in order to allow it to be replaced by some sort of tag"""
    return "%s%s%s" % (SOURCE_CODE_START_TAG, src, SOURCE_CODE_END_TAG)


class Mangling(object):
    def __init__(self, mangling_file):
        """Init mangling class."""
        self.mangling_file = mangling_file
        self.mangling = None

        self.setupMangling()

    def setupMangling(self):
        if self.mangling_file is None:
            return
        if not os.path.isfile(self.mangling_file):
            return
        with open(self.mangling_file, "r") as f:
            lines = f.read().splitlines()
            self.mangling = {}
            line_id = 0
            # Read line pairs, first line is mangled, second line is demangled symbol
            for line in lines:
                if line_id == 0:
                    mangled_symbol = line
                else:
                    demangled_symbol = line
                    self.mangling[mangled_symbol] = demangled_symbol
                line_id = (line_id + 1) % 2

            print(
                "Mangling info of "
                + str(len(self.mangling))
                + " symbols read from file '"
                + self.mangling_file
                + "'"
            )

    def demangle(self, symbol_name):
        if self.mangling is None:
            return symbol_name, False
        if symbol_name in self.mangling.keys():
            return self.mangling[symbol_name], True

        return symbol_name, False


class Binary(object):
    def __init__(
        self,
        settings,
        filename,
        symbol_selection_regex=None,
        symbol_exclusion_regex=None,
        mangling=None,
    ):
        """Init binary object."""
        self.settings = settings
        self.filename = filename
        self.symbol_type = getSymbolType(settings.language)

        self.mangling = mangling
        self.binutils_work = True

        self.text_size = 0
        self.data_size = 0
        self.bss_size = 0
        self.overall_size = 0
        self.progmem_size = 0
        self.static_ram_size = 0

        self.symbol_selection_regex = symbol_selection_regex
        self.symbol_selection_regex_compiled = None
        if symbol_selection_regex is not None:
            self.symbol_selection_regex_compiled = re.compile(symbol_selection_regex)

        self.symbol_exclusion_regex = symbol_exclusion_regex
        self.symbol_exclusion_regex_compiled = None
        if symbol_exclusion_regex is not None:
            self.symbol_exclusion_regex_compiled = re.compile(symbol_exclusion_regex)

        if not self.filename:
            unrecoverableError("No binary filename defined")

        if not os.path.isfile(self.filename):
            unrecoverableError(
                "Unable to find filename {filename}".format(filename=filename)
            )

        self.symbols = {}
        self.num_symbols_dropped = 0

        self.parseSymbols()

    def readObjdumpOutput(self):

        cmd = [self.settings.objdump_command, "-drwCS", self.filename]
        proc = subprocess.Popen(  # nosec # silence bandid warning
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        o, e = proc.communicate()  # pylint: disable=unused-variable

        output = o.decode("utf8")
        # error = e.decode('utf8')

        return output

    def readNMOutput(self):

        cmd = [
            self.settings.nm_command,
            "--print-size",
            "--size-sort",
            "--radix=d",
            "-C",
            self.filename,
        ]
        proc = subprocess.Popen(  # nosec # silence bandid warning
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )  # nosec # silence bandid warning

        o, e = proc.communicate()  # pylint: disable=unused-variable

        output = o.decode("utf8")
        # error = e.decode('utf8')

        return output

    def readSizeOutput(self):

        cmd = [self.settings.size_command, self.filename]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        o, e = proc.communicate()  # pylint: disable=unused-variable

        output = o.decode("utf8")
        # error = e.decode('utf8')

        return output

    def addSymbol(self, symbol):
        symbol.init()

        self.symbols[symbol.name] = symbol

    def isSymbolSelected(self, symbol_name):
        if self.symbol_exclusion_regex_compiled is not None:
            if re.match(self.symbol_exclusion_regex_compiled, symbol_name):
                return False

        if self.symbol_selection_regex_compiled is None:
            return True

        if re.match(self.symbol_selection_regex_compiled, symbol_name):
            return True

        return False

    def determineSymbolSizes(self):

        size_output = self.readSizeOutput()

        size_re = re.compile(r"^\s*([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)")
        sizes_sucessfully_determined = False
        for line in size_output.splitlines():
            size_match = re.match(size_re, line)
            if size_match:
                self.text_size = int(size_match.group(1))
                self.data_size = int(size_match.group(2))
                self.bss_size = int(size_match.group(3))
                self.overall_size = int(size_match.group(4))

                self.progmem_size = self.text_size + self.data_size
                self.static_ram_size = self.data_size + self.bss_size

                sizes_sucessfully_determined = True

                break

        if not sizes_sucessfully_determined:
            warning(
                "Unable to determine resource consumptions. Is the proper size utility used?"
            )
            self.binutils_work = False

    def generateSymbol(self, symbol_name, symbol_name_is_demangled):
        if self.isSymbolSelected(symbol_name):
            # print("Considering symbol " + symbol_name)
            return self.symbol_type(symbol_name, symbol_name_is_demangled)
        # print("Ignoring symbol " + symbol_name)
        return None

    def demangle(self, symbol_name_with_mangling_state_unknown):
        symbol_name_demangled, was_demangled = self.mangling.demangle(
            symbol_name_with_mangling_state_unknown
        )

        if was_demangled:
            return symbol_name_demangled, True  # is demangled

        if self.binutils_work:
            return (
                symbol_name_with_mangling_state_unknown,
                True,
            )  # Binutils work, so we expect demangling having already taken place

        return (
            symbol_name_with_mangling_state_unknown,
            False,
        )  # Neither explicit demangling, nor binutils demangling worked

    def gatherSymbolInstructions(self):

        objdump_output = self.readObjdumpOutput()

        # print("Output:")
        # print("%s" % (objdump_output))

        header_line_re = re.compile("^(0x)?[0-9A-Fa-f]+ <(.+)>:")
        instruction_line_re = re.compile(
            r"^\s*[0-9A-Fa-f]+:\s*((?:\s*[0-9a-fA-F]{2})+)\s+(.*)\s*"
        )

        cur_symbol = None
        n_symbols = 0
        n_instruction_lines = 0
        self.instructions_available = False

        for line in objdump_output.splitlines():

            header_match = re.match(header_line_re, line)
            if header_match:
                if cur_symbol:
                    self.addSymbol(cur_symbol)
                    n_symbols += 1

                symbol_name_with_mangling_state_unknown = header_match.group(2)

                symbol_name, symbol_name_is_demangled = self.demangle(
                    symbol_name_with_mangling_state_unknown
                )
                cur_symbol = self.generateSymbol(symbol_name, symbol_name_is_demangled)

                if cur_symbol is None:
                    self.num_symbols_dropped += 1
            else:
                instruction_line_match = re.match(instruction_line_re, line)
                if cur_symbol:
                    if instruction_line_match:
                        # print("Found instruction line \'%s\'" % (instruction_line_match.group(0)))
                        cur_symbol.addInstructions(instruction_line_match.group(2))
                        n_instruction_lines = n_instruction_lines + 1
                    else:
                        if (len(line) > 0) and (not line.isspace()):
                            cur_symbol.addInstructions(preHighlightSourceCode(line))

        if cur_symbol:
            self.addSymbol(cur_symbol)

        if n_instruction_lines == 0:
            warning(
                "Unable to read assembly from binary {filename}.".format(
                    filename=self.filename
                )
            )
            warning("Do you use the correct binutils version?")
            warning("Please check the --bin_dir and --bin_prefix settings.")
            self.binutils_work = False
        else:
            self.instructions_available = True

    def gatherSymbolProperties(self):
        nm_output = self.readNMOutput()

        self.num_symbols_dropped = 0
        nm_regex = re.compile(r"^[0-9A-Fa-f]+\s([0-9A-Fa-f]+)\s(\w)\s(.+)")
        for line in nm_output.splitlines():
            nm_match = re.match(nm_regex, line)

            if nm_match:
                symbol_size_str = nm_match.group(1)
                symbol_type = nm_match.group(2)

                symbol_name_with_mangling_state_unknown = nm_match.group(3)
                symbol_name, symbol_name_is_demangled = self.demangle(
                    symbol_name_with_mangling_state_unknown
                )

                if symbol_name not in self.symbols.keys():

                    data_symbol = self.generateSymbol(
                        symbol_name, symbol_name_is_demangled
                    )
                    if data_symbol is not None:
                        data_symbol.size = int(symbol_size_str)
                        data_symbol.type = symbol_type
                        self.addSymbol(data_symbol)
                    else:
                        self.num_symbols_dropped += 1
                else:
                    self.symbols[symbol_name].size = int(symbol_size_str)
                    self.symbols[symbol_name].type = symbol_type

    def parseSymbols(self):

        self.determineSymbolSizes()
        self.gatherSymbolInstructions()
        self.gatherSymbolProperties()
