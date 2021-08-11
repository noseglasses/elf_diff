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
from elf_diff.report import Report
from elf_diff.binary_pair import BinaryPair
import elf_diff.html as html
from elf_diff.error_handling import unrecoverableError
from elf_diff.auxiliary import formatMemChange
from elf_diff.git import gitRepoInfo
from elf_diff.symbol import Symbol
import progressbar
import sys
import difflib
      
class PairReport(Report):
   
   html_template_file = "pair_report_template.html"
   
   def __init__(self, settings):
      
      self.settings = settings
      
      self.validateSettings()
      
      self.binary_pair = BinaryPair(settings, settings.old_binary_filename, \
                                              settings.new_binary_filename)
   def getReportBasename(self):
      return "pair_report"
      
   def validateSettings(self):
      if not self.settings.old_binary_filename:
         unrecoverableError("No old binary filename defined")
               
      if not self.settings.new_binary_filename:
         unrecoverableError("No new binary filename defined")
         
   def generatePersistingSymbolsTableHTML(self):
      
      table_html = ""
      table_visible = False
      size_delta = 0
      
      if len(self.binary_pair.persisting_symbol_names) == 0:
         return [table_html, table_visible, html.highlightNumber(size_delta)]
      
      old_binary = self.binary_pair.old_binary
      new_binary = self.binary_pair.new_binary
      
      import operator
      
      diff_by_symbol = {}
      for symbol_name in self.binary_pair.persisting_symbol_names:
         old_symbol = old_binary.symbols[symbol_name]
         new_symbol = new_binary.symbols[symbol_name]
         
         difference = new_symbol.size - old_symbol.size
         
         diff_by_symbol[symbol_name] = difference
         
      sorted_by_diff = sorted(diff_by_symbol.items(), key=operator.itemgetter(1), reverse=True)
          
      print("Rendering persisting symbols HTML table...")
      sys.stdout.flush()
      for i in progressbar.progressbar(range(len(sorted_by_diff))):
         symbol_tuple = sorted_by_diff[i]
         
         symbol_name = symbol_tuple[0]
         
         old_symbol = old_binary.symbols[symbol_name]
         new_symbol = new_binary.symbols[symbol_name]
         
         if new_symbol.livesInProgramMemory():
            size_delta += new_symbol.size - old_symbol.size
         
         if old_symbol.size != new_symbol.size:
            symbol_name_html = html.escapeString(symbol_name)
            table_html += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n" % ( \
                              html.generateSymbolTableEntry(symbol_name_html), \
                              new_symbol.type, \
                              html.formatNumber(old_symbol.size), \
                              html.formatNumber(new_symbol.size), \
                              html.formatNumberDelta(old_symbol.size, new_symbol.size))
            
      if size_delta != 0:
         table_visible = True
            
      return [table_html, table_visible, html.highlightNumber(size_delta)]
      
   def generateDisappearedSymbolsTableHTML(self):
      
      table_html = ""
      overal_symbol_size = 0
      table_visible = "invisible"
      
      if len(self.binary_pair.disappeared_symbol_names) == 0:
         return [table_html, table_visible, html.highlightNumber(-overal_symbol_size)]  
      
      old_binary = self.binary_pair.old_binary
      
      symbols_sorted = sorted(self.binary_pair.disappeared_symbol_names, \
                                key=lambda symbol_name: old_binary.symbols[symbol_name].size, \
                                reverse = True)
                                
      print("Rendering disappeared symbols HTML table...")
      sys.stdout.flush()
      for i in progressbar.progressbar(range(len(symbols_sorted))):
         symbol_name = symbols_sorted[i]
         symbol_name_html = html.escapeString(symbol_name)
         symbol = old_binary.symbols[symbol_name]
         
         if symbol.symbol_type == Symbol.type_data:
            symbol_representation = symbol_name_html
         else:
            symbol_representation = html.generateSymbolTableEntry(symbol_name_html)
         
         table_html += "<tr><td>%s</td><td>%s</td><td>%s</td></tr>\n" % ( \
                              symbol_representation, \
                              symbol.type, \
                              html.formatNumber(symbol.size))
         
         if symbol.livesInProgramMemory():
            overal_symbol_size += symbol.size
            
      if len(self.binary_pair.disappeared_symbol_names) != 0:
         table_visible = True
            
      return [table_html, table_visible, html.highlightNumber(-overal_symbol_size)]  
   
   def generateNewSymbolsTableHTML(self):
      
      table_html = ""
      table_visible = "invisible"
      overal_symbol_size = 0
      
      if len(self.binary_pair.new_symbol_names) == 0:
         return [table_html, table_visible, html.highlightNumber(overal_symbol_size)]
           
      new_binary = self.binary_pair.new_binary
      
      symbols_sorted = sorted(self.binary_pair.new_symbol_names, \
                                key=lambda symbol_name: new_binary.symbols[symbol_name].size, \
                                reverse = True)
                                
      print("Rendering new symbols HTML table...")
      sys.stdout.flush()
      for i in progressbar.progressbar(range(len(symbols_sorted))):
         symbol_name = symbols_sorted[i]
         symbol_name_html = html.escapeString(symbol_name)
         symbol = new_binary.symbols[symbol_name]
         
         if symbol.symbol_type == Symbol.type_data:
            symbol_representation = symbol_name_html
         else:
            symbol_representation = html.generateSymbolTableEntry(symbol_name_html)
            
         table_html += "<tr><td>%s</td><td>%s</td><td>%s</td></tr>\n" % ( \
                              symbol_representation, \
                              symbol.type, \
                              html.formatNumber(symbol.size))
         
         if symbol.livesInProgramMemory():
            overal_symbol_size += symbol.size
            
      if len(self.binary_pair.new_symbol_names) != 0:
         table_visible = True
            
      return [table_html, table_visible, html.highlightNumber(overal_symbol_size)]
      
   def generateSimilarSymbolsTableHTML(self):
           
      table_html = ""
      table_visible = "invisible"
      
      if len(self.binary_pair.similar_symbols) == 0:
         return [table_html, table_visible, len(self.binary_pair.similar_symbols)]
         
      index = 0
      print("Rendering similar symbols HTML table...")
      sys.stdout.flush()
      for i in progressbar.progressbar(range(len(self.binary_pair.similar_symbols))):
         symbol_pair = self.binary_pair.similar_symbols[i]
         
         index = index + 1
         
         old_symbol_name = html.escapeString(symbol_pair.old_symbol.name)
         new_symbol_name = html.escapeString(symbol_pair.new_symbol.name)
         
         old_highlighted_symbol_name = html.diffStringsSource(symbol_pair.old_symbol.name, symbol_pair.new_symbol.name)
         new_highlighted_symbol_name = html.diffStringsTarget(symbol_pair.old_symbol.name, symbol_pair.new_symbol.name)
         if (symbol_pair.old_symbol.symbol_type == Symbol.type_data) or symbol_pair.instructions_equal:
            old_symbol_representation = old_highlighted_symbol_name
            new_symbol_representation = new_highlighted_symbol_name
            table_index = str(index)
         else:
            old_symbol_representation = html.generateSymbolTableEntryLight(old_symbol_name, old_highlighted_symbol_name)
            new_symbol_representation = html.generateSymbolTableEntryLight(new_symbol_name, new_highlighted_symbol_name)
            table_index = html.generateSimilarSymbolTableEntry(str(index))
         
         instructions_similarity_str = "N/A"
         if symbol_pair.instructions_similarity is not None:
            instructions_similarity_str = "{:.1f}".format(symbol_pair.instructions_similarity*100.0)
         
         table_html += "<tr><td>%s</td><td>%s<br>%s</td><td><p>%s</p><p>%s</p></td><td><p>%s</p><p>%s</p></td><td>%s</td><td>%s</td><td>%s</td></tr>\n" % ( \
                              table_index, \
                              old_symbol_representation, \
                              new_symbol_representation, \
                              symbol_pair.old_symbol.type, \
                              symbol_pair.new_symbol.type, \
                              html.formatNumber(symbol_pair.old_symbol.size), \
                              html.formatNumber(symbol_pair.new_symbol.size), \
                              html.formatNumberDelta(symbol_pair.old_symbol.size, symbol_pair.new_symbol.size), \
                              "{:.1f}".format(symbol_pair.symbol_similarity*100.0), \
                              instructions_similarity_str)
      
      if len(self.binary_pair.similar_symbols) != 0:
         table_visible = True
      
      return [table_html, table_visible, len(self.binary_pair.similar_symbols)]
   
   def generatePersistingSymbolDetailsHTML(self):
      
      if len(self.binary_pair.persisting_symbol_names) == 0:
         return ""
         
      old_binary = self.binary_pair.old_binary
      new_binary = self.binary_pair.new_binary
      
      symbols_listed = False
      
      html_lines = []
            
      print("Rendering persisting symbols details HTML...")
      sys.stdout.flush()
      for i in progressbar.progressbar(range(len(self.binary_pair.persisting_symbol_names))):
         symbol_name = self.binary_pair.persisting_symbol_names[i]
         
         old_symbol = old_binary.symbols[symbol_name]
         new_symbol = new_binary.symbols[symbol_name]
         
         if (old_symbol.symbol_type == Symbol.type_data) or (new_symbol.symbol_type == Symbol.type_data):
            continue
         
         symbol_name_html = html.escapeString(symbol_name)
         
         if not old_symbol.__eq__(new_symbol):
            
            symbol_differences = old_symbol.getDifferencesAsHTML(new_symbol, "   ")
            
            if old_symbol.size == new_symbol.size:
               size_info = "size unchanged"
            else:
               size_info = formatMemChange("size", old_symbol.size, new_symbol.size)
               
            title_line = "<{header}>{title} ({size_info})</{header}>".format( \
                              header = self.settings.symbols_html_header, \
                              title = html.generateSymbolDetailsTitle(symbol_name_html), \
                              size_info = size_info)
                              
            html_lines.append(html.formatMonospace(title_line))
            html_lines.append(symbol_differences)
            
            symbols_listed = True
            
      if not symbols_listed:
         return "No persisting functions or no symbol changes"
            
      return "\n".join(html_lines)
   
   def generateDisappearedSymbolDetailsHTML(self):
   
      if len(self.binary_pair.disappeared_symbol_names) == 0:
         return ""
      
      symbols_listed = False
      
      html_lines = []
      
      print("Rendering disappeared symbols details HTML...")
      sys.stdout.flush()
      for i in progressbar.progressbar(range(len(self.binary_pair.disappeared_symbol_names))):
         symbol_name = self.binary_pair.disappeared_symbol_names[i]
         symbol = self.binary_pair.old_binary.symbols[symbol_name]
         
         if (symbol.symbol_type == Symbol.type_data):
            continue
            
         symbol_name_html = html.escapeString(symbol_name)
         
         title_line = "<%s>%s: %d bytes</%s>" % ( \
                                              self.settings.symbols_html_header, \
                                              html.generateSymbolDetailsTitle(symbol_name_html), \
                                              symbol.size, \
                                              self.settings.symbols_html_header)
         html_lines.append(html.formatMonospace(title_line))
         
         html_lines.append("<pre>")
         html_lines.append(symbol.getInstructionsBlockEscaped(""))
         html_lines.append("</pre>")
            
         symbols_listed = True
            
      if not symbols_listed:
         return "No functions disappeared"
         
      return "\n".join(html_lines)
      
   def generateNewSymbolDetailsHTML(self):
   
      if len(self.binary_pair.new_symbol_names) == 0:
         return ""
      
      symbols_listed = False
      
      html_lines = []
      
      print("Rendering new symbols details HTML...")
      sys.stdout.flush()
      for i in progressbar.progressbar(range(len(self.binary_pair.new_symbol_names))):
         symbol_name = self.binary_pair.new_symbol_names[i]
         symbol = self.binary_pair.new_binary.symbols[symbol_name]
         
         if symbol.symbol_type == Symbol.type_data:
            continue
         
         symbol_name_html = html.escapeString(symbol_name)
         
         title_line = "<%s>%s: %d bytes</%s>" % ( \
                                              self.settings.symbols_html_header, \
                                              html.generateSymbolDetailsTitle(symbol_name_html), \
                                              symbol.size, \
                                              self.settings.symbols_html_header)
         
         html_lines.append(html.formatMonospace(title_line))
                                              
         html_lines.append("<pre>")
         html_lines.append(symbol.getInstructionsBlockEscaped(""))
         html_lines.append("</pre>")
            
         symbols_listed = True
            
      if not symbols_listed:
         return "No new functions"
            
      return "\n".join(html_lines)
   
   def generateSimilarSymbolDetailsHTML(self):
   
      if len(self.binary_pair.similar_symbols) == 0:
         return ""
      
      symbols_listed = False
      
      html_lines = []
      
      index = 0;
      print("Rendering similar symbols details HTML...")
      sys.stdout.flush()
      for i in progressbar.progressbar(range(len(self.binary_pair.similar_symbols))):
         symbol_pair = self.binary_pair.similar_symbols[i]
         
         index = index + 1
         
         if (symbol_pair.old_symbol.symbol_type == Symbol.type_data) or (symbol_pair.new_symbol.symbol_type == Symbol.type_data) or symbol_pair.instructions_equal:
            continue
         
         old_symbol_name_html = html.escapeString(symbol_pair.old_symbol.name)
         new_symbol_name_html = html.escapeString(symbol_pair.new_symbol.name)
         
         old_symbol_representation = html.diffStringsSource(symbol_pair.old_symbol.name, symbol_pair.new_symbol.name)
         new_symbol_representation = html.diffStringsTarget(symbol_pair.old_symbol.name, symbol_pair.new_symbol.name)
         
         if symbol_pair.old_symbol.size == symbol_pair.new_symbol.size:
            size_info = "size unchanged"
         else:
            size_info = formatMemChange("size", symbol_pair.old_symbol.size, symbol_pair.new_symbol.size)
            
         instruction_similarity_string = ""
         if symbol_pair.instructions_similarity is not None:
            instruction_similarity_string = ", instr. sim.: {:.1f} %".format(symbol_pair.instructions_similarity*100.0)
            
         title_line = "<%s>Similar pair %s (%s) (sym. sim.: %s %%%s)</%s>" % ( \
                                          self.settings.symbols_html_header, \
                                          html.generateSimilarSymbolDetailsTitle(str(index)), \
                                          size_info, \
                                          "{:.1f}".format(symbol_pair.symbol_similarity*100.0), \
                                          instruction_similarity_string, \
                                          self.settings.symbols_html_header)
            
         html_lines.append(html.formatMonospace(title_line))
                                          
         old_title = "<p>Old: %s<br>" % (html.generateSymbolDetailsTitleWithRepresentation(old_symbol_name_html, old_symbol_representation))                                    
         new_title = "New: %s</p>" % (html.generateSymbolDetailsTitleWithRepresentation(new_symbol_name_html, new_symbol_representation))
                                          
         html_lines.append(html.formatMonospace(old_title))
         html_lines.append(html.formatMonospace(new_title))
         
         symbol_differences = symbol_pair.old_symbol.getDifferencesAsHTML(symbol_pair.new_symbol, "   ")
         html_lines.append("%s" % (symbol_differences))
         
         symbols_listed = True
            
      if not symbols_listed:
         return "No similar functions or no implementation changes"
         
      return "\n".join(html_lines)
   
   def configureJinjaKeywords(self, skip_details):
      
      import datetime
      
      old_binary = self.binary_pair.old_binary
      new_binary = self.binary_pair.new_binary
      
      # If we generate a pdf files, we skip the details
      #
      if skip_details:
         details_visibility = False
         persisting_symbol_details_html = ""
         disappeared_symbol_details_html = ""
         new_symbol_details_html = ""
         similar_symbol_details_html = ""
      else:
         details_visibility = True
         persisting_symbol_details_html = self.generatePersistingSymbolDetailsHTML()
         disappeared_symbol_details_html = self.generateDisappearedSymbolDetailsHTML()
         new_symbol_details_html = self.generateNewSymbolDetailsHTML()
         similar_symbol_details_html = self.generateSimilarSymbolDetailsHTML()
      
      if self.settings.project_title:
         doc_title = html.escapeString(self.settings.project_title)
      else:
         doc_title = "ELF Binary Comparison"
         
      [persisting_symbols_table, persisting_symbols_table_visible, persisting_symbols_delta] = self.generatePersistingSymbolsTableHTML()
      [disappeared_symbols_table, disappeared_symbols_table_visible, disappeared_symbols_size] = self.generateDisappearedSymbolsTableHTML()
      [new_symbols_table, new_symbols_table_visible, new_symbols_size] = self.generateNewSymbolsTableHTML()
      [similar_symbols_table, similar_symbols_table_visible, num_similar_symbols] = self.generateSimilarSymbolsTableHTML()
      
      if self.settings.build_info == "":
         build_info_visible = False
      else:
         build_info_visible = True
         
      binary_details_visible = False
      if self.settings.old_binary_info == "":
         old_binary_info_visible = False
      else:
         old_binary_info_visible = True
         binary_details_visible = True
         
      if self.settings.new_binary_info == "":
         new_binary_info_visible = False
      else:
         new_binary_info_visible = True
         binary_details_visible = True
      
      return {
          "page_title" : u"ELF Binary Comparison - (c) 2019 by noseglasses"
         ,"doc_title" : doc_title   
         ,"elf_diff_repo_base" : self.settings.repo_path
         ,"old_binary_file" : html.escapeString(self.settings.old_alias)
         ,"new_binary_file" : html.escapeString(self.settings.new_alias)
         
         ,"code_size_old_overall" : str(old_binary.progmem_size)
         ,"code_size_new_overall" : str(new_binary.progmem_size)
         ,"code_size_change_overall" : html.formatNumberDelta(old_binary.progmem_size, new_binary.progmem_size)
         ,"static_ram_old_overall" : str(old_binary.static_ram_size)
         ,"static_ram_new_overall" : str(new_binary.static_ram_size)
         ,"static_ram_change_overall" : html.formatNumberDelta(old_binary.static_ram_size, new_binary.static_ram_size)
         ,"text_size_old_overall" : str(old_binary.text_size)
         ,"text_size_new_overall" : str(new_binary.text_size)
         ,"text_size_change_overall" : html.formatNumberDelta(old_binary.text_size, new_binary.text_size)
         ,"data_size_old_overall" : str(old_binary.data_size)
         ,"data_size_new_overall" : str(new_binary.data_size)
         ,"data_size_change_overall" : html.formatNumberDelta(old_binary.data_size, new_binary.data_size)
         ,"bss_size_old_overall" : str(old_binary.bss_size)
         ,"bss_size_new_overall" : str(new_binary.bss_size)
         ,"bss_size_change_overall" : html.formatNumberDelta(old_binary.bss_size, new_binary.bss_size)
         
         ,"total_symbols_old" : str(len(old_binary.symbols.keys()))
         ,"total_symbols_new" : str(len(new_binary.symbols.keys()))
                  
         ,"num_persisting_symbols" : str(len(self.binary_pair.persisting_symbol_names))
         ,"num_disappeared_symbols" : str(self.binary_pair.num_symbols_disappeared)
         ,"num_new_symbols" : str(self.binary_pair.num_symbols_new)
         ,"num_similar_symbols" : str(num_similar_symbols)
         
         ,"persisting_symbols_table_visible" : persisting_symbols_table_visible
         ,"disappeared_symbols_table_visible" : disappeared_symbols_table_visible
         ,"new_symbols_table_visible" : new_symbols_table_visible
         ,"similar_symbols_table_visible" : similar_symbols_table_visible
         
         ,"persisting_symbols_table" : persisting_symbols_table
         ,"disappeared_symbols_table" : disappeared_symbols_table
         ,"new_symbols_table" : new_symbols_table
         ,"similar_symbols_table" : similar_symbols_table
         
         ,"persisting_symbols_delta" : persisting_symbols_delta
         ,"disappeared_symbols_size" : disappeared_symbols_size
         ,"new_symbols_size" : new_symbols_size
         
         ,"details_visibility" : details_visibility
         
         ,"persisting_symbol_details_html" : persisting_symbol_details_html
         ,"disappeared_symbol_details_html" : disappeared_symbol_details_html
         ,"new_symbol_details_html" : new_symbol_details_html
         ,"similar_symbol_details_html" : similar_symbol_details_html
         
         ,"binary_details_visible" : binary_details_visible
         
         ,"old_binary_info_visible" : old_binary_info_visible
         ,"new_binary_info_visible" : new_binary_info_visible
         
         ,"old_binary_info" : html.escapeString(self.settings.old_binary_info)
         ,"new_binary_info" : html.escapeString(self.settings.new_binary_info)
         
         ,"build_info_visible" : build_info_visible
         ,"build_info": html.escapeString(self.settings.build_info)
         
         ,"date" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
         ,"elfdiff_git_version": gitRepoInfo(self.settings)
         ,"home" : "<a href=\"#home\">&#x21A9;</a>"
      }
   
   def getHTMLTemplate(self):
      return PairReport.html_template_file
      
def generatePairReport(settings):
   PairReport(settings).generate()
