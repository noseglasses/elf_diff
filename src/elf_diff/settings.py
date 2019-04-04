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

import sys
import os

from elf_diff.binary_pair import BinaryPairSettings
from elf_diff.error_handling import unrecoverableError

class Parameter(object):
   
   def __init__(self, name, description, \
                      default = None, \
                      deprecated_alias = None, \
                      alias = None,
                      no_cmd_line = False,
                      is_flag = False):
      self.name = name
      self.description = description
      self.default = default
      self.alias = alias
      self.deprecated_alias = deprecated_alias
      self.no_cmd_line = no_cmd_line
      self.is_flag = is_flag

class Settings(object):
   
   def __init__(self, repo_path):
      
      self.repo_path = repo_path
      
      self.setupParameters()

      self.presetDefaults()
      
      cmd_line_args = self.parseCommandLineArgs()
      
      if cmd_line_args.driver_file:
         
         self.driver_file = cmd_line_args.driver_file
         
         self.readDriverFile()
         
      self.considerCommandLineArgs(cmd_line_args)
      
      self.validateAndInitSettings()
         
   def setupParameters(self):
      
      self.parameters = [ \
         Parameter("old_binary_filename", "The old elf binary", deprecated_alias = "old"), \
         Parameter("new_binary_filename", "The new elf binary", deprecated_alias = "new"), \
          \
         Parameter("old_alias", "An alias string that is supposed to be used to reference the old binary", deprecated_alias = "old-alias"), \
         Parameter("new_alias", "An alias string that is supposed to be used to reference the new binary", deprecated_alias = "new-alias"), \
          \
         Parameter("old_info_file", "A text file with information about the old binary", deprecated_alias = "old-info-file"), \
         Parameter("new_info_file", "A text file with information about the new binary", deprecated_alias = "new-info-file"), \
          \
         Parameter("build_info", "A string with build information", deprecated_alias = "build-info", default = ""), \
          \
         Parameter("bin_dir", "The place where the binaries live", deprecated_alias = "bin-dir", default = "/usr/bin"), \
          \
         Parameter("bin_prefix", "The place where the binaries live", deprecated_alias = "bin-prefix", default = ""), \
          \
         #Parameter("text_file", "A text file to write output to", deprecated_alias = "text-file"), \
         Parameter("html_file", "A html file to write output to", deprecated_alias = "html-file"), \
         Parameter("pdf_file", "A pdf file to write output to (details are skipped in pdf files)", deprecated_alias = "pdf-file"), \
          \
         Parameter("project_title", "A project title to use in reports", deprecated_alias = "project-title"), \
          \
         Parameter("driver_file", "A yaml file that contains settings and driver information", deprecated_alias = "driver-file"), \
         Parameter("driver_template_file", "A yaml file that is generated at the end of the run (contains default parameters if no action parameters were specified)"), \
         \
         Parameter("symbols_html_header", "The type of html tag to use for symbol headers", default = "H4", no_cmd_line = True), \
         Parameter("html_template_dir", "A directory that contains template html files", no_cmd_line = True), \
         Parameter("mass_report", "Forces a mass report being generated", default = False, is_flag = True) \
      ]
      
   def presetDefaults(self):
      
      self.mass_report_members = []
      
      for parameter in self.parameters:
         
         setattr(self, parameter.name, parameter.default)
      
   def deprecated(self, desc):
      return "{desc} [deprecated]".format(desc=desc)
      
   def parseCommandLineArgs(self):
      
      import argparse

      parser = argparse.ArgumentParser(description='Compare elf binaries and list the differences in the disassembly.')
      
      for parameter in self.parameters:
         
         if parameter.no_cmd_line:
            continue
         
         if parameter.alias:
            param_name = parameter.alias
         else:
            param_name = parameter.name
            
         if parameter.is_flag:
            action = "store_true"
         else:
            action = "store"
            
         parser.add_argument('--{name}'.format(name = param_name), \
                           default = parameter.default, \
                           dest = parameter.name, \
                           action = action, \
                           help = parameter.description)
         
         if parameter.deprecated_alias:
            parser.add_argument('--{name}'.format(name = parameter.deprecated_alias), \
                           default = parameter.default, \
                           dest = parameter.name, \
                           action = action, \
                           help = parameter.description + " (deprecated)")
            
      parser.add_argument("binaries", nargs='*', default = None, help='The binaries (this is an alternative to --old and --new)')
      
      actual_args = list()
      for arg_pos in range(1, len(sys.argv)):
         arg = sys.argv[arg_pos]
         if arg == "--":
               break
         actual_args.append(arg)
         
      return parser.parse_args(actual_args)
      
   def readDriverFile(self):
      
      import yaml
      
      my_yaml = None
      with open(self.driver_file, 'r') as stream:
         try:
            my_yaml = yaml.load(stream)
         except yaml.YAMLError as exc:
            print(exc)
            return
         
      for parameter in self.parameters:
         
         if parameter.name in my_yaml.keys():
            
            setattr(self, parameter.name, my_yaml[parameter.name])
         
      # Read binary pairs
      
      if "binary_pairs" in my_yaml.keys():
         
         for data_set in my_yaml["binary_pairs"]:
            
            bp = BinaryPairSettings(data_set.get("short_name"), \
                                    data_set.get("old_binary"), \
                                    data_set.get("new_binary"))
               
            self.mass_report_members.append(bp)
            
   def considerCommandLineArgs(self, cmd_line_args):
      
      for parameter in self.parameters:
         
         if parameter.no_cmd_line:
            continue
         
         if hasattr(cmd_line_args, parameter.name):
            value = getattr(cmd_line_args, parameter.name)
            
            if value != parameter.default:
               setattr(self, parameter.name, value)
               
      if len(cmd_line_args.binaries) == 0:
         pass               
      elif len(cmd_line_args.binaries) == 2:
         if self.old_binary_filename:
            unrecoverableError("Old binary filename redundantly defined")
            
         else:
            self.old_binary_filename = cmd_line_args.binaries[0]
            
         if self.new_binary_filename:
            unrecoverableError("Old binary filename redundantly defined")
            
         else:
            self.new_binary_filename = cmd_line_args.binaries[1]
      else:
         unrecoverableError("Please specify either none or two binaries")
      
   def validateAndInitSettings(self):
            
      if self.old_binary_filename and not os.path.isfile(self.old_binary_filename):
         unrecoverableError("Old binary \'%s\' is not a file or cannot be found" % (self.old_binary_filename))
         
      if self.new_binary_filename and not os.path.isfile(self.new_binary_filename):
         unrecoverableError("New binary \'%s\' is not a file or cannot be found" % (self.new_binary_filename))

      self.objdump_command = self.bin_dir + "/" + self.bin_prefix + "objdump"
      self.nm_command = self.bin_dir + "/" + self.bin_prefix + "nm"
      self.size_command = self.bin_dir + "/" + self.bin_prefix + "size"
      
      if (not os.path.isfile(self.objdump_command)) or (not os.access(self.objdump_command, os.X_OK)):
         unrecoverableError("objdump command \'%s\' is either not a file or not executable" % (self.objdump_command))
         
      if (not os.path.isfile(self.nm_command)) or (not os.access(self.nm_command, os.X_OK)):
         unrecoverableError("nm command \'%s\' is either not a file or not executable" % (self.nm_command))
               
      if (not os.path.isfile(self.size_command)) or (not os.access(self.size_command, os.X_OK)):
         unrecoverableError("size command \'%s\' is either not a file or not executable" % (self.size_command))
         
      if self.old_info_file:
         if os.path.isfile(self.old_info_file):
            with open(self.old_info_file, "r") as f:
               self.old_binary_info = f.read()
         else:
            unrecoverableError("Unable to find old info file \'%s\'" % (self.old_info_file))
      else:
         self.old_binary_info = ""
         
      if self.new_info_file:
         if os.path.isfile(self.new_info_file):
            with open(self.new_info_file, "r") as f:
               self.new_binary_info = f.read()
         else:
            unrecoverableError("Unable to find new info file \'%s\'" % (self.new_info_file))
      else:
         self.new_binary_info = ""     
         
      if not self.old_alias: 
         self.old_alias = self.old_binary_filename
      
      if not self.new_alias:
         self.new_alias = self.new_binary_filename

   def writeParameterTemplateFile(self, filename):
      
      import datetime
      
      with open(filename, "w") as f:
         
         f.write("# This is an auto generated elf_diff driver file\n")
         f.write("# Generated by elf_diff {date}\n".format(date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
         f.write("\n")
         
         for parameter in self.parameters:
            
            f.write("# {desc}\n".format(desc = parameter.description))
            f.write("#\n")
            f.write("{name}: {value}\n".format(name = parameter.name, value = parameter.default))
            f.write("\n")
         
   def isFirmwareBinaryDefined(self):
      return self.old_binary_filename or self.new_binary_filename
