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

class Symbol(object):
   
   type_function = 1
   type_data = 2
   
   def __init__(self, name):
      self.name = name
      self.instruction_lines = []
      self.size = 0
      self.type = "?"
      
   def addInstructions(self, instruction_line):
      self.instruction_lines.append(instruction_line)
      
   def __eq__(self, other):
      if not self.name == other.name:
         #print "Symbol name differs"
         return False
      
      if not self.size == other.size:
         return False
      
      if not len(self.instruction_lines) == len(other.instruction_lines):
         #print "Instructions differ"
         return False
      
      symbol_diff = [i for i, j in zip(self.instruction_lines, other.instruction_lines) if i != j]
      if len(symbol_diff) > 0:
         #print "Symbols differ"
         return False
      
      #print "Symbols equal"
      return True
   
   def getDifferencesAsString(self, other, indent):
      
      import difflib
      #from difflib_data import *

      diff = difflib.ndiff(self.instruction_lines, other.instruction_lines)
      #print list(diff)
      return indent + ("\n" + indent).join(list(diff))
   
   def getDifferencesAsHTML(self, other, indent):
   
      import difflib
      diff_class = difflib.HtmlDiff(tabsize=3, wrapcolumn=80)
      
      return diff_class.make_table(self.instruction_lines, \
                                   other.instruction_lines, \
                                   fromdesc='Old', \
                                   todesc='New', \
                                   context=True, \
                                   numlines=1000)
   
   def getInstructionsBlock(self, indent):
      return indent + ("\n" + indent).join(self.instruction_lines)
   
   def livesInProgramMemory(self):
      return (self.type != 'B') and (self.type != 'b') and \
             (self.type != 'S') and (self.type != 's')
      
   def parseSignature(self):
      
      import re
      
      symbol_regex = "((([\S]*)?::)?)?(\w+)(\((.*)\))?"
      match = re.match(symbol_regex, self.name)
      if match:
         self.namespace = match.group(3)
         self.actual_name = match.group(4)
         self.parameters = match.group(6)
         self.symbol_parse_success = True
      else:
         self.actual_name = self.name
         self.symbol_parse_success = False
         return
         
      if self.parameters:
         self.symbol_type = Symbol.type_function
      else:
         self.symbol_type = Symbol.type_data
         
   def init(self):
      self.parseSignature()
      
   def wasFunctionRenamed(self, other):
      return self.namespace == other.namespace \
         and self.parameters == other.parameters
   
   def hasFunctionSignatureChanged(self, other):
      return self.namespace == other.namespace \
         and self.klass == other.klass \
         and self.actual_name == other.actual_name
   
   def wasFunctionMoved(self, other):
      return self.actual_name == other.actual_name \
         and self.parameters == other.parameters

   def wasDataMoved(self, other):
      return self.actual_name == other.actual_name \
         and self.size == other.size
      
   def wasDataResized(self, other):
      return self.actual_name == other.actual_name \
         and self.namespace == other.namespace
      
   def wasDataRenamed(self, other):
      return self.namespace == other.namespace \
         and self.size == other.size

   def isSimilar(self, other):
      
      if not (self.symbol_parse_success and other.symbol_parse_success):
         return False
      
      if self.symbol_type == Symbol.type_function:
         if other.symbol_type == Symbol.type_function:
            return   self.wasFunctionRenamed(other) \
                  or self.hasFunctionSignatureChanged(other) \
                  or self.wasFunctionMoved(other)

      elif self.symbol_type == Symbol.type_data:
         if other.symbol_type == Symbol.type_data:
            return   self.wasDataMoved(other) \
                  or self.wasDataResized(other) \
                  or self.wasDataRenamed(other)
      
      return False
