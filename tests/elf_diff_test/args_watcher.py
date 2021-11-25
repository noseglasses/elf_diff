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
from elf_diff.settings import PARAMETERS

from typing import (  # pylint: disable=unused-import
    List,
    Tuple,
    Optional,
    Set,
)  # pylint: disable=unused-import

ArgsPair = Tuple[str, Optional[str]]
ArgsList = List[ArgsPair]


class ElfDiffCommandLineArgsWatcher(object):
    """This class watches about all command line arguments being tested"""

    def __init__(self):
        self.args_available: Set[
            str
        ] = ElfDiffCommandLineArgsWatcher._prepareArgsAvailable()
        self.args_tested: Set[str] = set()

    @staticmethod
    def _prepareArgsAvailable() -> Set[str]:
        args_available = set()
        for parameter in PARAMETERS:
            args_available.add(parameter.name)
        return args_available

    def considerArgUnsed(self, key: str) -> None:
        self.args_tested.add(key)

    def testIfAllArgsUsedAtLeastOnce(self) -> None:
        """Test if all elf_diff command line args are at least used once while testing"""
        print("Args available: " + str(len(self.args_available)))
        print("Args tested: " + str(len(self.args_tested)))
        args_not_tested: Set[str] = self.args_available - self.args_tested

        if len(args_not_tested) > 0:
            print("Command line args not tested:")
            for arg_not_tested in sorted(args_not_tested):
                print(f"   {arg_not_tested}")

        assert len(args_not_tested) == 0

        print("All elf_diff command lines tested.")

    def printArgs(self) -> None:
        """Print all command line arguments"""
        print("Command line args available:")
        for arg in sorted(self.args_available):
            print(f"   {arg}")

    def printTestSkeletons(self) -> None:
        """Print test skeleton functions"""
        for arg in sorted(self.args_available):
            print(f"   def test_{arg}(self):")
            print("       pass")
            print("")
