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

import unittest
import os
import inspect
import sys

bin_path = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))
sys.path.append(bin_path + "/../src")

from elf_diff.symbol import Symbol
from elf_diff.symbol import CppSymbol


class TestCppSymbol(unittest.TestCase):
    class __RAIITestAux(object):
        def __init__(self, master_test):
            self.master_test = master_test
            for prop in CppSymbol.props:
                setattr(self, prop, None)

        def run(self):

            # Establisch symbol name
            self.name = ""

            if self.namespace is not None:
                self.name = self.namespace

            if self.template_parameters is not None:
                self.name += "<" + self.template_parameters + ">"

            if self.namespace is not None:
                self.name += "::"

            self.name += self.full_name

            if self.arguments is not None:
                self.name += "(" + self.arguments + ")"

            s = CppSymbol(self.name)
            s.init()

            self.master_test.assertTrue(s.symbol_type == self.symbol_type)

            if not s.propertiesEqual(self):
                s_props = s.getProperties()
                print(f"{self.name} Properties mismatch")
                for key, value in s_props.items():
                    self_value = getattr(self, key)
                    print(f"   {key}: expected {self_value}, actual {value}")

            self.master_test.assertTrue(s.propertiesEqual(self))

    def setUp(self):
        self.template_parameters = "std::size_t, std::vector<int>"

    def __dataSymbolTest(self):
        t = self.__RAIITestAux(self)
        t.symbol_type = Symbol.type_data
        return t

    def __functionSymbolTest(self):
        t = self.__dataSymbolTest()
        t.symbol_type = Symbol.type_function
        return t

    def __simpleDataTest(self):
        p = self.__dataSymbolTest()
        p.full_name = "a"
        return p

    def simpleDataTest(self):
        self.__simpleDataTest().run()

    def testDataInNamespace(self):
        p = self.__simpleDataTest()
        p.namespace = "n"
        p.run()

    def testDataInClassInNamespace(self):
        p = self.__simpleDataTest()
        p.namespace = "n::c"
        p.run()

    def testDataInTemplateClass(self):
        p = self.__simpleDataTest()
        p.namespace = "c"
        p.template_parameters = self.template_parameters
        p.run()

    def testSimpleFunction(self):
        p = self.__functionSymbolTest()
        p.full_name = "f"
        p.arguments = ""
        p.run()

    def __simpleFunctionWithSimpleArgs(self):
        p = self.__functionSymbolTest()
        p.full_name = "f"
        p.arguments = "int, double"
        return p

    def __simpleFunctionWithTemplateArg(self):
        p = self.__functionSymbolTest()
        p.full_name = "f"
        p.arguments = "std::vector<int>, double"
        return p

    def __simpleFunctionWithTemplateArgWithBraces(self):
        p = self.__functionSymbolTest()
        p.full_name = "f"
        p.arguments = "std::array<int, (foo)3>, double"
        return p

    def __getFunctionTests(self):
        return [
            self.__simpleFunctionWithSimpleArgs(),
            self.__simpleFunctionWithTemplateArg(),
            self.__simpleFunctionWithTemplateArgWithBraces(),
        ]

    def testSimpleFunctions(self):
        for test in self.__getFunctionTests():
            test.run()

    def testFunctionsInNamespaces(self):
        for test in self.__getFunctionTests():
            test.namespace = "n"
            test.run()

    def testFunctionsInClassesInNamespaces(self):
        tests = self.__getFunctionTests()
        for test in tests:
            test.namespace = "n::c"
            test.run()

    def testFunctionsInTemplateClasses(self):
        tests = self.__getFunctionTests()
        for test in tests:
            test.namespace = "c"
            test.template_parameters = self.template_parameters
            test.run()

    def testFunctionsInTemplateClassesInNamespaces(self):
        tests = self.__getFunctionTests()
        for test in tests:
            test.namespace = "n::c"
            test.template_parameters = self.template_parameters
            test.run()


if __name__ == "__main__":
    unittest.main()
