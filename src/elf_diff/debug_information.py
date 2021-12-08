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
from elf_diff.source_file import SourceFile
from elf_diff.symbol import Symbol
from elf_diff.binutils import Binutils
from elf_diff.error_handling import warning

from typing import Dict, Optional, Tuple, List
import re
import progressbar  # type: ignore # Make mypy ignore this module
import sys
import os


class CompilationUnit(object):
    def __init__(self, id_: int):
        self.id_: int = id_
        self.directories: Dict[int, str] = {}

        FileInfo = Tuple[int, int, str]  # file_id, dir_id, file_name
        self.files: List[FileInfo] = []
        self.code_file: Optional[str] = None


class DebugInformationCollector(object):
    def __init__(self, symbols: Dict[str, Symbol], source_prefix: Optional[str]):
        self._symbols: Dict[str, Symbol] = symbols
        self._source_prefix: Optional[str] = source_prefix

        self._header_line_regex = re.compile(
            r"\s*<[0-9a-f]+>\s*<[0-9a-f]+>:\s+Abbrev Number:\s*(\d+)\s+\((\w+)\).*"
        )
        self._info_line_regex = re.compile(r"\s*<[0-9a-f]+>\s+(\S+)\s*:\s*(\S.*)")
        self._name_regex = re.compile(r".*\s+(\S+)")
        self._source_file_regex = re.compile(r".*\s+(\S+)")
        self._producer_regex = re.compile(r"\s*\([^\)]+\):\s+(.+)")

        self._header_id: Optional[int] = None
        self._header_tag: Optional[str] = None

        self._name: Optional[str] = None
        self._name_mangled: Optional[str] = None
        self._dwarf_source_id: Optional[int] = None
        self._source_line: Optional[int] = None
        self._source_column: Optional[int] = None
        self._const_expr: bool = False
        self._compilation_unit: Optional[CompilationUnit] = None

        # Maps compilation units to source files by id
        self._source_file_mapping: Dict[
            int, Dict[int, SourceFile]
        ] = {}  # Maps a dwarf source id to an elf_diff SourceFile

        # Maps a source file full path to a compilation unit
        self._files_to_compilation_unit: Dict[str, CompilationUnit] = {}

        self.debug_info_available = False
        self.source_files: Dict[int, SourceFile] = {}

    def getCompilationUnit(self, source_fullpath) -> CompilationUnit:
        if source_fullpath not in self._files_to_compilation_unit.keys():
            raise Exception(
                f"Unable to find compilation unit for source file '{source_fullpath}'"
            )
        return self._files_to_compilation_unit[source_fullpath]

    def _registerSourceFile(
        self, source_path_base: str, source_path_complete: str
    ) -> SourceFile:
        new_source_file = SourceFile(
            path_base=source_path_base, path_complete=source_path_complete
        )
        self.source_files[new_source_file.id_] = new_source_file
        return new_source_file

    def _flushDataSet(self) -> None:
        if self._header_tag == "DW_TAG_compile_unit":
            main_source_file = self._name.replace(
                "\\", "/"
            )  # Make sure the fix all paths
            self._compilation_unit = self.getCompilationUnit(main_source_file)
        elif (self._header_tag == "DW_TAG_variable") or (
            self._header_tag == "DW_TAG_subprogram"
        ):
            if not self._const_expr:
                lookup_name: Optional[str] = None
                if self._name_mangled is not None:
                    lookup_name = self._name_mangled
                elif self._name is not None:
                    lookup_name = self._name

                if lookup_name:
                    if lookup_name in self._symbols.keys():
                        symbol = self._symbols[lookup_name]

                        assert self._dwarf_source_id is not None

                        print(
                            f"c.unit. {self._compilation_unit.id_}: Source id of symbol {lookup_name} is {self._dwarf_source_id}"
                        )

                        # Temporarily store dwarf source id as source_id.
                        # Will be replace later on after all dwarf info has been read.
                        symbol.source_id = self._dwarf_source_id
                        symbol.source_line = self._source_line
                        symbol.source_column = self._source_column
                        symbol.compilation_unit_id = self._compilation_unit.id_
                    else:
                        print(f"Unable to find symbol {lookup_name}")

        self._name = None
        self._name_mangled = None
        self._source_line = None
        self._source_column = None
        self._const_expr = False

    def _removeSourcePrefix(self, filename: str) -> str:
        if self._source_prefix is None:
            return filename

        if filename.startswith(self._source_prefix):
            return filename[len(self._source_prefix) :]
        return filename

    def _processHeaderLine(self, line: str) -> bool:
        header_line_match = re.match(self._header_line_regex, line)
        if header_line_match:
            self._flushDataSet()
            self._header_id = int(header_line_match.group(1))
            self._header_tag = header_line_match.group(2)
            return True
        return False

    def _processInfoLine(self, line: str) -> None:
        info_line_match = re.match(self._info_line_regex, line)
        if info_line_match is None:
            return

        tag: str = info_line_match.group(1)
        add_info: str = info_line_match.group(2)

        if (tag == "DW_AT_linkage_name") or (tag == "DW_AT_MIPS_linkage_name"):
            name_match = re.match(self._name_regex, add_info)
            if name_match is None:
                raise Exception("Undeciferable info line '%s'" % line)
            self._name_mangled = name_match.group(1)
        elif tag == "DW_AT_decl_file":
            self._dwarf_source_id = int(add_info)
        elif tag == "DW_AT_decl_line":
            self._source_line = int(add_info)
        elif tag == "DW_AT_decl_column":
            self._source_column = int(add_info)
        elif tag == "DW_AT_name":
            name_match = re.match(self._name_regex, add_info)
            if name_match is not None:
                self._name = name_match.group(1)
            else:
                self._name = add_info
        elif tag == "DW_AT_const_expr":
            if add_info == "1":
                self._const_expr = True

    def gatherFileInformation(self, filename: str, binutils: Binutils) -> None:
        readelf_output = runSystemCommand(
            [
                binutils.readelf_command,
                "--debug-dump=line",
                filename,
            ]
        )

        files_to_compilation_unit: Dict[str, CompilationUnit] = {}
        compilation_units: Dict[int, CompilationUnit] = {}
        current_compilation_unit: CompilationUnit

        class ReadFileTableLine(object):
            def __init__(self):
                self._regex = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.*)")

            def __call__(self, line: str):
                m = re.match(self._regex, line)
                if m is None:
                    # Start over with expecting directory table of next compilation unit
                    return ReadDirectoryTableHeader()

                file_id: int = int(m.group(1))
                dir_id: int = int(m.group(2))
                file_name: str = m.group(5)

                # print(f"**********************File {file_id} in dir {dir_id}: {file_name}")

                nonlocal current_compilation_unit
                current_compilation_unit.files.append((file_id, dir_id, file_name))

                # dir_id == 0 means system file (use the basename instead of a path in that case)
                if dir_id > 0:
                    file_fullpath = os.path.join(
                        current_compilation_unit.directories[dir_id], file_name
                    ).replace("\\", "/")
                else:
                    file_fullpath = file_name
                files_to_compilation_unit[file_fullpath] = current_compilation_unit

                return self

        class ReadFileTableHeader(object):
            def __init__(self):
                self._skipping_lines: bool = False
                self._additional_lines_to_be_skipped = 1
                self._regex = re.compile(r"^\s*The File Name Table .*")

            def __call__(self, line: str):
                if self._skipping_lines:
                    self._additional_lines_to_be_skipped -= 1
                    if self._additional_lines_to_be_skipped == 0:
                        return ReadFileTableLine()

                if re.match(self._regex, line):
                    self._skipping_lines = True

                return self

        class ReadDirectoryTableLine(object):
            def __init__(self):
                self._regex = re.compile(r"^\s*(\d+)\s+(.*)")

            def __call__(self, line: str):
                m = re.match(self._regex, line)
                if m is None:
                    return ReadFileTableHeader()

                dir_id: int = int(m.group(1))
                dir_name: str = m.group(2).replace("\\", "/")

                nonlocal current_compilation_unit
                current_compilation_unit.directories[dir_id] = dir_name

                # print(f"Directory {dir_id}: {dir_name}")

                return self

        class ReadDirectoryTableHeader(object):
            def __init__(self):
                self._header_found: bool = False
                self._regex = re.compile(r"^\s*The Directory Table .*")

            def __call__(self, line: str):
                if re.match(self._regex, line):
                    nonlocal current_compilation_unit
                    nonlocal compilation_units
                    compilation_unit_id: int = len(compilation_units)
                    current_compilation_unit = CompilationUnit(compilation_unit_id)
                    compilation_units[
                        current_compilation_unit.id_
                    ] = current_compilation_unit
                    return ReadDirectoryTableLine()
                return self

        line_processor = ReadDirectoryTableHeader()

        print("Gathering source file information")
        sys.stdout.flush()

        for line in progressbar.progressbar(readelf_output.splitlines()):
            if line_processor is None:
                break

            # print(type(line_processor).__name__)
            line_processor = line_processor(line)

        for id_, compilation_unit in compilation_units.items():

            source_file_mapping: Dict[int, SourceFile] = {}

            for file in compilation_unit.files:
                dwarf_file_id = file[0]
                dir_id = file[1]
                source_path_base = file[2]

                if dir_id > 0:
                    source_path_complete = (
                        f"{compilation_unit.directories[dir_id]}/{source_path_base}"
                    )
                else:
                    # dir_id == 0 is used for build in files
                    source_path_complete = source_path_base

                source_file = self._registerSourceFile(
                    source_path_base=source_path_base,
                    source_path_complete=source_path_complete,
                )

                source_file_mapping[dwarf_file_id] = source_file

            self._source_file_mapping[id_] = source_file_mapping

        self._files_to_compilation_unit = files_to_compilation_unit

    def replaceSourceFileIds(self):
        # Replace dwarf source ids with elf_diff source ids
        for symbol in self._symbols.values():
            if symbol.source_id is not None:
                if symbol.compilation_unit_id not in self._source_file_mapping.keys():
                    print(
                        f"Can't find compilation unit id {symbol.compilation_unit_id} of symbol {symbol.name}"
                    )
                else:
                    if (
                        symbol.source_id
                        not in self._source_file_mapping[
                            symbol.compilation_unit_id
                        ].keys()
                    ):
                        print(
                            f"Symbol {symbol.name} not listed in compilation unit {symbol.compilation_unit_id}"
                        )
                    else:
                        symbol.source_id = self._source_file_mapping[
                            symbol.compilation_unit_id
                        ][symbol.source_id].id_
            else:
                print("Source id of symbol %s is None" % symbol.name)

    def gatherDebugInformation(self, filename: str, binutils: Binutils) -> None:
        """Try to extract source file and symbol information using readelf.
        Please note this works under the assumption that compilation units are listed in the same order
        in the output of commands
        readelf --debug-dump=line <elf_file>
        readelf --debug-dump=info <elf_file>
        """
        if binutils.readelf_command is None:
            warning(
                "Binutils readelf command unavailable. Unable to gather debug information."
            )
            return

        self.gatherFileInformation(filename, binutils)

        readelf_output = runSystemCommand(
            [
                binutils.readelf_command,
                "--debug-dump=info",
                filename,
            ]
        )

        self.debug_info_available = (
            r"Contents of the .debug_info section:" in readelf_output
        )

        if not self.debug_info_available:
            return

        print("Gathering debug information")
        sys.stdout.flush()

        for line in progressbar.progressbar(readelf_output.splitlines()):
            if self._processHeaderLine(line):
                continue

            self._processInfoLine(line)

        # There might be a last ungoing data set being parsed
        self._flushDataSet()

        self.replaceSourceFileIds()
