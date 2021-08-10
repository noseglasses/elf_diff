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
      self.instructions = ""
      for instruction_line in self.instruction_lines:
         self.instructions += "".join(instruction_line.split())
   
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
         
   def getSimilarityMeasure(self, other):
         
      if self.symbol_type != other.symbol_type:
         return 0.0
      
      num_measures_applying = 0
      sum_common_measures = 0
      
      indiv_measures = {}
      
      # To compute the similarity measure take the arithmetic mean of
      # all those values that are defined for at least one of the symbols.
      
      for prop in self.props:
         self_value = getattr(self, prop)
         other_value = getattr(other, prop)
         # Count a match if one of the two symbols has the value
         if (self_value is not None) or (other_value is not None):
            num_measures_applying += 1
         if self_value is not None:
            if other_value is not None:
               indiv_measures[prop] = similar(self_value, other_value)
               sum_common_measures += indiv_measures[prop]
               
      if (len(self.instructions) != 0) or (len(other.instructions) != 0):
         num_measures_applying += 1
         indiv_measures["instructions"] = similar(self.instructions, other.instructions)
         sum_common_measures += indiv_measures["instructions"]
            
      if num_measures_applying == 0:
         similarity_measure = 0.0
      else:
         similarity_measure = float(sum_common_measures)/float(num_measures_applying)
      
      #print(f"{self.name} <-> {other.name}: {similarity_measure}")
      #for key, value in indiv_measures.items():
      #   print(f"   {key}: {value}")
      
      return similarity_measure
      
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
   if language == "c++":
      return CppSymbol
   
   return None
