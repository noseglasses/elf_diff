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
     
class FunctionSimilarity(object):
   def __init__(self, symbol1, symbol2):
      self.symbol1 = symbol1
      self.symbol2 = symbol2
      self.renamed = False
      self.moved = False
      self.signatureChanged = False
      
   def wasFunctionRenamed(self):
      # Class methods must live in the same namespace or class names must match
      if (self.symbol1.class_name is not None) and (self.symbol2.class_name is not None):
         return ((self.symbol1.namespace == self.symbol2.namespace) \
              or (self.symbol1.class_name == self.symbol2.class_name)) \
            and self.symbol1.arguments == self.symbol2.arguments

      return self.symbol1.namespace == self.symbol2.namespace \
         and self.symbol1.arguments == self.symbol2.arguments

   def hasFunctionSignatureChanged(self):
      return self.symbol1.namespace == self.symbol2.namespace \
         and self.symbol1.full_name == self.symbol2.full_name

   def wasFunctionMoved(self):
      return self.symbol1.full_name == self.symbol2.full_name \
         and self.symbol1.arguments == self.symbol2.arguments
     
   def check(self):
      self.renamed = self.wasFunctionRenamed()
      self.moved = self.wasFunctionMoved()
      self.signatureChanged = self.hasFunctionSignatureChanged()
      return self.renamed or self.signatureChanged or self.moved
     
   def report(self):
      print(f"Function symbol similarity of {self.symbol1.name} and {self.symbol2.name}")
      if self.renamed:
         print("   renamed")
      if self.moved:
         print("   moved")
      if self.signatureChanged:
         print("   signature changed")

class DataSimilarity(object):
   def __init__(self, symbol1, symbol2):
      self.symbol1 = symbol1
      self.symbol2 = symbol2
      self.renamed = False
      self.moved = False
      self.resized = False

   def wasDataMoved(self):
      return self.symbol1.full_name == self.symbol2.full_name \
         and self.symbol1.size == self.symbol2.size
      
   def wasDataResized(self):
      return self.symbol1.full_name == self.symbol2.full_name \
         and self.symbol1.namespace == self.symbol2.namespace
      
   def wasDataRenamed(self):
      return self.symbol1.namespace == self.symbol2.namespace \
         and self.symbol1.size == self.symbol2.size
         
   def check(self):
      self.renamed = self.wasDataRenamed()
      self.moved = self.wasDataMoved()
      self.resized = self.wasDataResized()
      return self.moved or self.resized or self.renamed
     
   def report(self):
      print(f"Data symbol similarity of {self.symbol1.name} and {self.symbol2.name}")
      if self.renamed:
         print("   renamed")
      if self.moved:
         print("   moved")
      if self.resized:
         print("   resized")
         
class Symbol(object):
   
   type_function = 1
   type_data = 2
   
   def __init__(self, name):
      self.name = name
      self.namespace = None
      self.class_name = None
      self.instruction_lines = []
      self.size = 0
      self.type = "?"
      
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
             
   def getArgumentsPortion(self):
      closing_bracket_found = False
      n = 0
      lower_brace_pos = None
      upper_brace_pos = None
      for i in reversed(range(len(self.name))):
         if (not closing_bracket_found) and (self.name[i] == ')'):
            closing_bracket_found = True
            upper_brace_pos = i
            n = 1
            continue
         if self.name[i] == '(':
            n -= 1
            if n == 0:
               lower_brace_pos = i
               break
         elif self.name[i] == ')':
            n += 1
            
      if lower_brace_pos is not None:
         arguments = self.name[lower_brace_pos + 1:upper_brace_pos]
         rest = self.name[:lower_brace_pos]
         #print(f"{self.name} -> rest = {rest}, arguments = {arguments}")
         return rest, arguments
      
      return None, None
      
   def parseSignature(self):
      
      import re
      
      namespace_regex = "((([\S]*)?::)?)?(.+)"
      
      rest, arguments = self.getArgumentsPortion()
      if rest is not None:
         self.arguments = arguments
         self.symbol_type = Symbol.type_function
      else:
         rest = self.name
         self.symbol_type = Symbol.type_data
         
      # Try to split up the possibly namespaced name 
      match = re.match(namespace_regex, rest)
      if match:
         self.namespace = match.group(3)
         name_in_class = match.group(4)
      else:
         name_in_class = rest
         
      # Check if the symbol lives within a class 
      class_sep_pos = name_in_class.rfind('::')
      if class_sep_pos >= 0:
         self.full_name = name_in_class[class_sep_pos + 2 :]
         self.class_name = name_in_class[:class_sep_pos]
      else: 
         self.full_name = name_in_class
         
   def init(self):
      self.parseSignature()
         
   def getSimilarity(self, other):
         
      if self.symbol_type != other.symbol_type:
         return None
      
      similarity = None
      if self.symbol_type == Symbol.type_function:
         similarity = FunctionSimilarity(self, other)
         if similarity.check() == True:
            return similarity

      elif self.symbol_type == Symbol.type_data:
         similarity = DataSimilarity(self, other)
         if similarity.check() == True:
            return similarity
      
      return None
      
   def propertiesEqual(self, other):
      props = [
         "name",
         "full_name",
         "arguments",
         "namespace"
         "class_name"
      ]
      
      for prop in props:
         self_arg = getattr(self, prop)
         other_arg = getattr(other, prop)
         if self_arg != other_arg:
            return False
         
      return True
