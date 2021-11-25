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
import unittest
import re
import os
import sys
from typing import Optional, Union, Type  # pylint: disable=unused-import


class TestCaseWithSubdirs(unittest.TestCase):
    OLD_PWD: Optional[str] = None

    def _getTestShortName(self) -> str:
        # Just take the final portion of the test id after the final period
        test_function_full_id: str = self.id()
        test_name_re = re.compile(r".*\.(\w*)")
        m = test_name_re.match(test_function_full_id)
        if m is None:
            print("Strange test name")
            sys.exit(1)
        return m.group(1)

    @classmethod
    def _setUpScoped(cls, scope, directory):
        # type: (Union[TestCaseWithSubdirs, Type[TestCaseWithSubdirs]], str) -> None
        """Generate and change to a directory that represents either the test or the test class scope"""
        scope.OLD_PWD = os.getcwd()
        if not os.path.exists(directory):
            os.mkdir(directory)
        os.chdir(directory)

    @classmethod
    def _tearDownScoped(cls, scope):
        # type: (Union[TestCaseWithSubdirs, Type[TestCaseWithSubdirs]]) -> None
        """Return to the previous scope"""
        if scope.OLD_PWD is not None:
            os.chdir(scope.OLD_PWD)

    @classmethod
    def setUpClass(cls) -> None:
        """Standard test set up method for class scope"""
        cls._setUpScoped(cls, cls.__name__)

    @classmethod
    def tearDownClass(cls) -> None:
        """Standard test tear down method for class scope"""
        cls._tearDownScoped(cls)

    def setUp(self) -> None:
        """Standard test set up method"""
        test_name: str = self._getTestShortName()
        self.__class__._setUpScoped(self, test_name)

    def tearDown(self) -> None:
        """Standard test tear down method"""
        self.__class__._tearDownScoped(self)
