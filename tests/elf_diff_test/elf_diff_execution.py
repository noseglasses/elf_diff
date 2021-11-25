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
from .args_watcher import ArgsList
from .test_binaries import TESTING_DIR, getTestBinary
from .subprocess import runSubprocess

import abc
import os
import sys
import typing
from typing import List, Optional

ELF_DIFF_START: List[str] = []


def usePackagedElfDiff():
    global ELF_DIFF_START
    ELF_DIFF_START = [sys.executable, "-m", "elf_diff"]


def useElfDiffFromDevelopmentTree(use_code_coverage: bool):
    global ELF_DIFF_START
    bin_dir: str = os.path.join(TESTING_DIR, "..", "bin")
    if use_code_coverage:
        print("Running with coverage testing")
        ELF_DIFF_START = [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "--branch",
            "--parallel-mode",  # Creates individual .coverage* files for each run
            os.path.join(bin_dir, "elf_diff"),
        ]
    else:
        ELF_DIFF_START = [sys.executable, os.path.join(bin_dir, "elf_diff")]


# As mypy rants about mixin base classes not featuring specific methods,
# we simply define a mock class that is only used during type checking
if typing.TYPE_CHECKING:

    class _Mock(object):
        def _getTestShortName(self) -> str:
            pass

        def assertTrue(self, expr, msg=None):
            pass

    _Base = _Mock
else:
    _Base = object


class ElfDiffExecutionMixin(_Base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # forwards all unused arguments
        self.default_args: ArgsList = [("debug", None)]
        self.expected_return_code: int = 0

    @abc.abstractmethod
    def prepareArgs(self, args: ArgsList) -> List[str]:
        output_args: List[str] = []
        for args_tuple in args:
            key: str = args_tuple[0]
            value: Optional[str] = args_tuple[1]

            self.registerArgUsed(key, value)

            output_args.append(f"--{key}")
            if value is not None:
                output_args.append(value)

        return output_args

    @abc.abstractmethod
    def registerArgUsed(self, key: str, value: Optional[str]) -> None:
        pass

    def runElfDiff(self, args: ArgsList, expected_return_code=0) -> None:
        """Runs elf diff with a given set of arguments

        args: Arguments are given as name value pair tuples. Flag argmuments require None type values
        """
        test_name: str = super()._getTestShortName()
        prepared_args: List[str] = self.prepareArgs(args)
        (output, error) = runSubprocess(  # pylint: disable=unused-variable
            test_name=test_name,
            cmd=ELF_DIFF_START + prepared_args,
            expected_return_code=expected_return_code,
        )

    def runSimpleTestBase(
        self,
        args: Optional[ArgsList] = None,
        old_binary_filename=getTestBinary("x86_64", "test", "debug", "old"),
        new_binary_filename=getTestBinary("x86_64", "test", "debug", "new"),
        output_file=None,
    ):
        """Runs a simple test with a set of arguments"""
        actual_args: ArgsList = args or []
        actual_args += self.default_args
        actual_args.append(("old_binary_filename", old_binary_filename))
        actual_args.append(("new_binary_filename", new_binary_filename))
        self.runElfDiff(
            args=actual_args, expected_return_code=self.expected_return_code
        )
        if output_file is not None:
            super().assertTrue(os.path.isfile(output_file))

    def runSimpleTest(self, args: Optional[ArgsList] = None):
        """Runs a simple test with a set of arguments"""
        args = args or []
        html_file = "single_page_report.html"
        actual_args = args
        actual_args.append(("html_file", html_file))
        self.runSimpleTestBase(args=actual_args, output_file=html_file)

    def runSimpleTest2(self, args: Optional[ArgsList] = None):
        """Runs a simple test with a set of arguments"""
        args = args or []
        html_file = "single_page_report.html"
        actual_args = args
        actual_args.append(("html_file", html_file))
        self.runSimpleTestBase(
            args=actual_args,
            old_binary_filename=getTestBinary("x86_64", "test2", "debug", "old"),
            new_binary_filename=getTestBinary("x86_64", "test2", "debug", "new"),
            output_file=html_file,
        )

    def runSimpleTestArm(self, args: Optional[ArgsList] = None):
        """Runs a simple test with a set of arguments"""
        args = args or []
        html_file = "single_page_report.html"
        actual_args = args
        actual_args.append(("html_file", html_file))
        self.runSimpleTestBase(
            args=actual_args,
            old_binary_filename=getTestBinary("arm", "test", "release", "old"),
            new_binary_filename=getTestBinary("arm", "test", "release", "new"),
            output_file=html_file,
        )

    def runSimpleTestGhs(self, args: Optional[ArgsList] = None):
        """Runs a simple test with a set of arguments"""
        args = args or []
        html_file = "single_page_report.html"
        actual_args = args
        actual_args.append(("html_file", html_file))
        self.runSimpleTestBase(
            args=actual_args,
            old_binary_filename=getTestBinary("ghs", "test", "release", "old"),
            new_binary_filename=getTestBinary("ghs", "test", "release", "new"),
            output_file=html_file,
        )
