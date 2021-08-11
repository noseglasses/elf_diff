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

from elf_diff.error_handling import unrecoverableError
import sys
import difflib

def escapeString(string):
   return string.replace("<", "&lt;").replace(">", "&gt;")
      
def generateSymbolTableEntry(symbol_name):
   return "<a name=\"table_%s\"><a href=\"#details_%s\">%s</a></a>" % \
          (symbol_name, symbol_name, symbol_name)

def generateSymbolTableEntryLight(symbol_name, symbol_representation):
   return "<a href=\"#details_%s\">%s</a>" % \
          (symbol_name, symbol_representation)

def generateSymbolDetailsTitle(symbol_name):
   return "<a name=\"details_%s\"><a href=\"#table_%s\">%s</a></a>" % \
          (symbol_name, symbol_name, tagSymbolName(symbol_name))

def generateSymbolDetailsTitleWithRepresentation(symbol_name, symbol_representation):
   return "<a name=\"details_%s\"><a href=\"#table_%s\">%s</a></a>" % \
          (symbol_name, symbol_name, tagSymbolName(symbol_representation))

def generateSimilarSymbolTableEntry(similar_pair_id):
   return "<a name=\"similar_table_%s\"><a href=\"#similar_details_%s\">%s</a></a>" % \
          (similar_pair_id, similar_pair_id, similar_pair_id)
               
def generateSimilarSymbolDetailsTitle(similar_pair_id):
   return "<a name=\"similar_details_%s\"><a href=\"#similar_table_%s\">%s</a></a>" % \
          (similar_pair_id, similar_pair_id, similar_pair_id)
       
def tagSymbolName(symbol_name):
   return "<span class=\"symbol_name\">%s</span>" % (symbol_name)

def formatNumber(number):
   return "<span class=\"number\">%s</span>" % (number)
   
def formatMonospace(number):
   return "<span class=\"monospace\">%s</span>" % (number)

def highlightNumber(number):
   if number > 0:
      css_class = "deterioration"
   elif number < 0:
      css_class = "improvement"
   else:
      css_class = "unchanged"
      
   return "<span  class=\"%s number\">%+d</span>" % (css_class, number)

def preHighlightSourceCode(src):
   return "__ED_SOURCE_START__%s__ED_SOURCE_END__" % (src)

def postHighlightSourceCode(src):
   return src.replace("__ED_SOURCE_START__", "<span class=\"source\">") \
             .replace("__ED_SOURCE_END__", "</span>")

def postHighlightSourceCodeRemoveTags(src):
   return src.replace("__ED_SOURCE_START__", "") \
             .replace("__ED_SOURCE_END__", "")

def formatNumberDelta(old_size, new_size):
   difference = new_size - old_size
   return highlightNumber(new_size - old_size)
        
def replaceHighlights(src):
    return src.replace("__HIGHLIGHT_START__", "<span class=\"diff_highlight\">") \
              .replace("__HIGHLIGHT_END__", "</span>")
   
def diffStringsSource(str1, str2):
    seqm = difflib.SequenceMatcher(None, str1, str2)
    output= []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            output.append(seqm.a[a0:a1])
        elif opcode == 'insert':
            pass
        elif opcode == 'delete':
            output.append("__HIGHLIGHT_START__" + seqm.a[a0:a1] + "__HIGHLIGHT_END__")
        elif opcode == 'replace':
            output.append("__HIGHLIGHT_START__" + seqm.a[a0:a1] + "__HIGHLIGHT_END__")
        else:
            raise RuntimeError("unexpected opcode")
            
    return replaceHighlights(escapeString(''.join(output)))
    
def diffStringsTarget(str1, str2):
    seqm = difflib.SequenceMatcher(None, str1, str2)
    output= []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            output.append(seqm.a[a0:a1])
        elif opcode == 'insert':
            output.append("__HIGHLIGHT_START__" + seqm.b[b0:b1] + "__HIGHLIGHT_END__")
        elif opcode == 'delete':
            pass
        elif opcode == 'replace':
            output.append("__HIGHLIGHT_START__" + seqm.b[b0:b1] + "__HIGHLIGHT_END__")
        else:
            raise RuntimeError("unexpected opcode")
            
    return replaceHighlights(escapeString(''.join(output)))

def configureTemplate(settings, template_filename, keywords):
   
   import jinja2, os, inspect
   from jinja2 import Environment, FileSystemLoader, StrictUndefined
   
   template_path = settings.repo_path + "/html"
   
   env = Environment(loader=FileSystemLoader(template_path), \
                                    undefined = StrictUndefined)
         
   #addGlobalJinjaFunction(GetComponentLink)
      
   try:
      creator = env.get_template(template_filename)
      
   except jinja2.exceptions.TemplateError as e:
      unrecoverableError("Failed creating jinja creator\n" + str(e))
      
   try:
      sys.stdout.flush()
      replacedContent = creator.render(keywords)
   except (jinja2.exceptions.TemplateError) as e:
      unrecoverableError("Failed rendering jinja template \'" + \
         template_filename + "\'\n" + str(e))

   return replacedContent#.encode('utf8')
   
def configureTemplateWrite(settings, template_filename, out_file, keywords):
   
   html_code = configureTemplate(settings, template_filename, keywords)
   
   out_file.write(html_code)
