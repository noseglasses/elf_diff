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

from elf_diff.html import postHighlightSourceCodeRemoveTags
from elf_diff.html import postHighlightSourceCode
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()
 
class Symbol(object):
   
   type_function = 1
   type_data = 2
   
   def __init__(self, name):
      self.name = name
      self.instruction_lines = []
      self.size = 0
      self.type = "?"
      
   def init(self):
      #self.instructions_hash = hash(tuple(self.instruction_lines))
      pass
   
   def addInstructions(self, instruction_line):
      self.instruction_lines.append(instruction_line)
      
   def __eq__(self, other):
      if not self.name == other.name:
         #print("Symbol name differs")
         return False
      
      if not self.size == other.size:
         return False
      
      if not len(self.instruction_lines) == len(other.instruction_lines):
         #print("Instructions differ")
         return False
      
      symbol_diff = [i for i, j in zip(self.instruction_lines, other.instruction_lines) if i != j]
      if len(symbol_diff) > 0:
         #print("Symbols differ")
         return False
      
      #print("Symbols equal")
      return True
   
   def getDifferencesAsString(self, other, indent):
      
      import difflib
      #from difflib_data import *

      diff = difflib.ndiff(self.instruction_lines, other.instruction_lines)
      #print list(diff)
      return postHighlightSourceCodeRemoveTags(indent + ("\n" + indent).join(list(diff)))
   
   def getDifferencesAsHTML(self, other, indent):
   
      import difflib
      diff_class = difflib.HtmlDiff(tabsize=3, wrapcolumn=200)
      
      diff_table = diff_class.make_table(self.instruction_lines, \
                                   other.instruction_lines, \
                                   fromdesc='Old', \
                                   todesc='New', \
                                   context=True, \
                                   numlines=1000)
   
      return postHighlightSourceCode(diff_table)
   
   def getInstructionsBlock(self, indent):
      return indent + ("\n" + indent).join(self.instruction_lines)
   
   def livesInProgramMemory(self):
      return (self.type != 'B') and (self.type != 'b') and \
             (self.type != 'S') and (self.type != 's')
          
class CppSymbol(Symbol):
   props = [
      "namespace",
      "full_name",
      "template_parameters",
      "arguments",
   ]
   
   def __init__(self, name):
      super(CppSymbol, self).__init__(name)
      
      self.initProps()
      self.name = name
      
   def initProps(self):
      for prop in self.props:
         setattr(self, prop, None)
             
   def __getArgumentsPortion(self, input_str, opening_brace, closing_brace):
      closing_bracket_found = False
      n = 0
      lower_brace_pos = None
      upper_brace_pos = None
      for i in reversed(range(len(input_str))):
         if (not closing_bracket_found) and (input_str[i] == closing_brace):
            closing_bracket_found = True
            upper_brace_pos = i
            n = 1
            continue
         if input_str[i] == opening_brace:
            n -= 1
            if n == 0:
               lower_brace_pos = i
               break
         elif input_str[i] == closing_brace:
            n += 1
            
      if lower_brace_pos is not None:
         arguments = input_str[lower_brace_pos + 1:upper_brace_pos]
         rest = input_str[:lower_brace_pos]
         #print(f"{input_str} -> rest = {rest}, arguments = {arguments}")
         return rest, arguments
      
      return None, None
      
   def __parseSignature(self):
      
      rest, self.arguments = self.__getArgumentsPortion(self.name, "(", ")")
      if rest is not None:
         self.symbol_type = Symbol.type_function
      else:
         rest = self.name
         self.symbol_type = Symbol.type_data
         
      # Check if the symbol lives within a class or namespace.
      # We cannot distinguish between those two as from a naming perspective both are equal.
      namespace_sep_pos = rest.rfind("::")
      if namespace_sep_pos >= 0:
         self.full_name = rest[namespace_sep_pos + 2 :]
         full_namespace = rest[:namespace_sep_pos]
         
         self.namespace, self.template_parameters = self.__getArgumentsPortion(full_namespace, "<", ">")
         if self.namespace is None:
            self.namespace = full_namespace
      else: 
         self.full_name = rest
         
   def init(self):
      self.__parseSignature()
      super(CppSymbol, self).init()
          
   class __CppFunctionSimilarity(object):
      def __init__(self, symbol1, symbol2):
         self.symbol1 = symbol1
         self.symbol2 = symbol2
         self.renamed = False
         self.moved = False
         self.signatureChanged = False
         
      def __wasFunctionRenamed(self):
         # Class methods must live in the same namespace or class names must match
         if (self.symbol1.namespace is not None) and (self.symbol2.namespace is not None):
            return (self.symbol1.namespace == self.symbol2.namespace) \
               and self.symbol1.arguments == self.symbol2.arguments

         return self.symbol1.namespace == self.symbol2.namespace \
            and self.symbol1.arguments == self.symbol2.arguments

      def __hasFunctionSignatureChanged(self):
         return self.symbol1.namespace == self.symbol2.namespace \
            and self.symbol1.full_name == self.symbol2.full_name

      def __wasFunctionMoved(self):
         return self.symbol1.full_name == self.symbol2.full_name \
            and self.symbol1.arguments == self.symbol2.arguments
      
      def check(self):
         self.renamed = self.__wasFunctionRenamed()
         self.moved = self.__wasFunctionMoved()
         self.signatureChanged = self.__hasFunctionSignatureChanged()
         return self.renamed or self.signatureChanged or self.moved
      
      def report(self):
         print(f"Function symbol similarity of {self.symbol1.name} and {self.symbol2.name}")
         if self.renamed:
            print("   renamed")
         if self.moved:
            print("   moved")
         if self.signatureChanged:
            print("   signature changed")

   class __CppDataSimilarity(object):
      def __init__(self, symbol1, symbol2):
         self.symbol1 = symbol1
         self.symbol2 = symbol2
         self.renamed = False
         self.moved = False
         self.resized = False

      def __wasDataMoved(self):
         return self.symbol1.full_name == self.symbol2.full_name \
            and self.symbol1.size == self.symbol2.size
         
      def __wasDataResized(self):
         return self.symbol1.full_name == self.symbol2.full_name \
            and self.symbol1.namespace == self.symbol2.namespace
         
      def __wasDataRenamed(self):
         return self.symbol1.namespace == self.symbol2.namespace \
            and self.symbol1.size == self.symbol2.size
            
      def check(self):
         self.renamed = self.__wasDataRenamed()
         self.moved = self.__wasDataMoved()
         self.resized = self.__wasDataResized()
         return self.moved or self.resized or self.renamed
      
      def report(self):
         print(f"Data symbol similarity of {self.symbol1.name} and {self.symbol2.name}")
         if self.renamed:
            print("   renamed")
         if self.moved:
            print("   moved")
         if self.resized:
            print("   resized")
         
   def getSimilarityRatio(self, other):
         
      if self.symbol_type != other.symbol_type:
         return 0.0
      
      sum_values = 0
      sum_values_matching = 0
      
      indiv_sims = {}
      
      for prop in self.props:
         self_value = getattr(self, prop)
         if self_value is not None:
            other_value = getattr(other, prop)
            sum_values += 1
            if other_value is not None:
               indiv_sims[prop] = similar(self_value, other_value)
               sum_values_matching += indiv_sims[prop]
               
      if len(self.instruction_lines) != 0:
         sum_values += 1
         #if self.instructions_hash == other.instructions_hash:
         #   sum_values_matching += 1
         #else:
         indiv_sims["instructions"] = similar(self.instruction_lines, other.instruction_lines)
         sum_values_matching += indiv_sims["instructions"]
            
      if sum_values == 0:
         similarity_ratio = 0.0
      else:
         similarity_ratio = float(sum_values_matching)/float(sum_values)
      
      #print(f"{self.name} <-> {other.name}: {similarity_ratio}")
      #for key, value in indiv_sims.items():
      #   print(f"   {key}: {value}")
      
      return similarity_ratio
      
   def propertiesEqual(self, other):
      for prop in self.props:
         self_arg = getattr(self, prop)
         other_arg = getattr(other, prop)
         if self_arg != other_arg:
            return False
         
      return True
   
   def getProperties(self):
      self_props = {}
      for prop in self.props:
         self_props[prop] = getattr(self, prop)
      return self_props
   
def getSymbolType(language):
   if language == "cpp":
      return CppSymbol
   
   return None
