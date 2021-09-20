# -*- mode: c++ -*-
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
cmake_minimum_required(VERSION 2.8)

project(elf_diff_test)

add_library(elf_diff_test_release_old STATIC src/old/test.cpp)
add_library(elf_diff_test_release_new STATIC src/new/test.cpp)

add_library(elf_diff_test_debug_old STATIC src/old/test.cpp)
add_library(elf_diff_test_debug_new STATIC src/new/test.cpp)

target_compile_options(elf_diff_test_debug_old PRIVATE "-g")
target_compile_options(elf_diff_test_debug_new PRIVATE "-g")

