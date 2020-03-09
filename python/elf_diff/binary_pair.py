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

from elf_diff.binary import Binary

class BinaryPairSettings(object):
   
   def __init__(self, short_name, old_binary_filename, new_binary_filename):
      
      self.short_name = short_name
      self.old_binary_filename = old_binary_filename
      self.new_binary_filename = new_binary_filename
      
class BinaryPair(object):
            
   def __init__(self, settings, old_binary_filename, new_binary_filename):
      
      self.settings = settings
      
      self.old_binary_filename = old_binary_filename
      self.new_binary_filename = new_binary_filename
      
      self.old_binary = Binary(self.settings, self.old_binary_filename)
      self.new_binary = Binary(self.settings, self.new_binary_filename)
      
      self.prepareMeasures()
         
   def prepareMeasures(self):
      
      from elf_diff.auxiliary import listIntersection
      
      self.old_symbol_names = set(self.old_binary.symbols.keys())
      self.new_symbol_names = set(self.new_binary.symbols.keys())

      self.persisting_symbol_names = listIntersection(self.old_symbol_names, self.new_symbol_names)
      self.disappeared_symbol_names = sorted(self.old_symbol_names - self.new_symbol_names)
      self.new_symbol_names = sorted(self.new_symbol_names - self.old_symbol_names)
      
      self.similar_symbols = self.determineSimilarSymbols()
      
      self.computeNumSymbolsPersisting()
      self.computeNumSymbolsDisappeared()
      self.computeNumSymbolsNew()
      
      self.computeNumAssembliesDiffer()
      
   def determineSimilarSymbols(self):
      
      import operator
      
      symbol_pairs = []
      
      for old_symbol_name in self.disappeared_symbol_names:
         old_symbol = self.old_binary.symbols[old_symbol_name]
         for new_symbol_name in self.new_symbol_names:
            new_symbol = self.new_binary.symbols[new_symbol_name]
      
            if old_symbol.isSimilar(new_symbol):
               symbol_pairs.append([old_symbol, new_symbol])
                                
                                
      # First sort symbol pairs by size difference
      #
      diff_by_symbol_pair = {}
      for i in range(0, len(symbol_pairs)):
         symbol_pair = symbol_pairs[i]
         
         old_symbol = symbol_pair[0]
         new_symbol = symbol_pair[1]
               
         difference = new_symbol.size - old_symbol.size
         
         diff_by_symbol_pair[i] = difference
         
      sorted_by_diff = sorted(diff_by_symbol_pair.items(), key=operator.itemgetter(1), reverse=True)  
      
      sorted_symbol_pairs = []
      for symbol_tuple in sorted_by_diff:
         index = symbol_tuple[0]
         sorted_symbol_pairs.append(symbol_pairs[index])
                                
      return sorted_symbol_pairs
   
   def computeNumSymbolsPersisting(self):
      
      self.num_symbol_size_changes = 0
      for symbol_name in self.persisting_symbol_names:
         old_symbol = self.old_binary.symbols[symbol_name]
         new_symbol = self.new_binary.symbols[symbol_name]
         if old_symbol.size != new_symbol.size:
            self.num_symbol_size_changes += 1
   
   def computeNumSymbolsDisappeared(self):
      self.num_bytes_disappeared = 0
      self.num_symbols_disappeared = len(self.disappeared_symbol_names)
      for symbol_name in self.disappeared_symbol_names:
         symbol = self.old_binary.symbols[symbol_name]
         self.num_bytes_disappeared += symbol.size
         
   def computeNumSymbolsNew(self):
      self.num_bytes_new = 0
      self.num_symbols_new = len(self.new_symbol_names)
      for symbol_name in self.new_symbol_names:
         symbol = self.new_binary.symbols[symbol_name]
         self.num_bytes_new += symbol.size
   
   def computeNumAssembliesDiffer(self):
      self.num_assemblies_differ = 0
      for symbol_name in self.persisting_symbol_names:
         old_symbol = self.old_binary.symbols[symbol_name]
         new_symbol = self.new_binary.symbols[symbol_name]
         
         if not old_symbol.__eq__(new_symbol):
            self.num_assemblies_differ += 1
