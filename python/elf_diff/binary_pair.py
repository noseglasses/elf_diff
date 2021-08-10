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
import progressbar
import sys

class BinaryPairSettings(object):
   
   def __init__(self, short_name, old_binary_filename, new_binary_filename):
      
      self.short_name = short_name
      self.old_binary_filename = old_binary_filename
      self.new_binary_filename = new_binary_filename
      
class SimilarityPair(object):
   def __init__(self, old_symbol, new_symbol, similarity_measure):
      self.old_symbol = old_symbol
      self.new_symbol = new_symbol
      self.similarity_measure = similarity_measure
      
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
      
      n_old_symbol_names = len(self.disappeared_symbol_names)
      similarity_threshold = float(self.settings.similarity_threshold)
      
      print("Detecting symbol similarities...")
      sys.stdout.flush()
      for i in progressbar.progressbar(range(n_old_symbol_names)):
         old_symbol_name = self.disappeared_symbol_names[i]
         old_symbol = self.old_binary.symbols[old_symbol_name]
         for new_symbol_name in self.new_symbol_names:
            new_symbol = self.new_binary.symbols[new_symbol_name]
            similarity_measure = old_symbol.getSimilarityMeasure(new_symbol)
            if similarity_measure >= similarity_threshold:
               symbol_pairs.append(
                  SimilarityPair(
                     old_symbol = old_symbol, 
                     new_symbol = new_symbol, 
                     similarity_measure = similarity_measure
                  )
               )
      # First sort symbol pairs by their similarity measures then by size 
      # difference
      #               
      sorted_symbol_pairs = sorted(symbol_pairs, key = lambda e: (e.similarity_measure, e.new_symbol.size - e.old_symbol.size), reverse = True)
                                
      return sorted_symbol_pairs
   
   def computeNumSymbolsPersisting(self):
      
      self.num_symbol_size_changes = 0
      print("Detecting persisting symbols...")
      sys.stdout.flush()
      for i in progressbar.progressbar(range(len(self.persisting_symbol_names))):
         symbol_name = self.persisting_symbol_names[i]
         old_symbol = self.old_binary.symbols[symbol_name]
         new_symbol = self.new_binary.symbols[symbol_name]
         if old_symbol.size != new_symbol.size:
            self.num_symbol_size_changes += 1
   
   def computeNumSymbolsDisappeared(self):
      self.num_bytes_disappeared = 0
      self.num_symbols_disappeared = len(self.disappeared_symbol_names)
      print("Detecting disappeared symbols...")
      sys.stdout.flush()
      for i in progressbar.progressbar(range(len(self.disappeared_symbol_names))):
         symbol_name = self.disappeared_symbol_names[i]
         symbol = self.old_binary.symbols[symbol_name]
         self.num_bytes_disappeared += symbol.size
         
   def computeNumSymbolsNew(self):
      self.num_bytes_new = 0
      self.num_symbols_new = len(self.new_symbol_names)
      print("Detecting new symbols...")
      sys.stdout.flush()
      for i in progressbar.progressbar(range(len(self.new_symbol_names))):
         symbol_name = self.new_symbol_names[i]
         symbol = self.new_binary.symbols[symbol_name]
         self.num_bytes_new += symbol.size
   
   def computeNumAssembliesDiffer(self):
      self.num_assemblies_differ = 0
      print("Detecting assembly differences...")
      sys.stdout.flush()
      for i in progressbar.progressbar(range(len(self.persisting_symbol_names))):
         symbol_name = self.persisting_symbol_names[i]
         old_symbol = self.old_binary.symbols[symbol_name]
         new_symbol = self.new_binary.symbols[symbol_name]
         
         if not old_symbol.__eq__(new_symbol):
            self.num_assemblies_differ += 1
