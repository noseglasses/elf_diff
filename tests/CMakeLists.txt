# -*- mode: c++ -*-
#
# elf_diff
#
# Copyright (C) 2019  Noseglasses (shinynoseglasses@gmail.com)
#
# This program is free software: you can redistribute it and/or modify it under
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

project(elf_diff_test CXX)

if(NOT "${PLATFORM}" STREQUAL "")
  set(PLATFORM_POSTFIX "-${PLATFORM}")
endif()

add_library(elf_diff_test_release_old${PLATFORM_POSTFIX} STATIC src/old/test.cpp)
add_library(elf_diff_test_release_new${PLATFORM_POSTFIX} STATIC src/new/test.cpp)

add_library(elf_diff_test_debug_old${PLATFORM_POSTFIX} STATIC src/old/test.cpp)
add_library(elf_diff_test_debug_new${PLATFORM_POSTFIX} STATIC src/new/test.cpp)

target_compile_options(elf_diff_test_debug_old${PLATFORM_POSTFIX} PRIVATE "-g")
target_compile_options(elf_diff_test_debug_new${PLATFORM_POSTFIX} PRIVATE "-g")

add_library(elf_diff_test2_release_old${PLATFORM_POSTFIX} STATIC src/old/test2.cpp)
add_library(elf_diff_test2_release_new${PLATFORM_POSTFIX} STATIC src/new/test2.cpp)

add_library(elf_diff_test2_debug_old${PLATFORM_POSTFIX} STATIC src/old/test2.cpp)
add_library(elf_diff_test2_debug_new${PLATFORM_POSTFIX} STATIC src/new/test2.cpp)

target_compile_options(elf_diff_test2_debug_old${PLATFORM_POSTFIX} PRIVATE "-g")
target_compile_options(elf_diff_test2_debug_new${PLATFORM_POSTFIX} PRIVATE "-g")

add_library(elf_diff_migration_test_release_old${PLATFORM_POSTFIX} STATIC src/old/migration_test1.cpp src/old/migration_test2.cpp)
add_library(elf_diff_migration_test_release_new${PLATFORM_POSTFIX} STATIC src/new/migration_test1.cpp src/new/migration_test2.cpp)

add_library(elf_diff_migration_test_debug_old${PLATFORM_POSTFIX} STATIC src/old/migration_test1.cpp src/old/migration_test2.cpp)
add_library(elf_diff_migration_test_debug_new${PLATFORM_POSTFIX} STATIC src/new/migration_test1.cpp src/new/migration_test2.cpp)

target_compile_options(elf_diff_migration_test_debug_old${PLATFORM_POSTFIX} PRIVATE "-g")
target_compile_options(elf_diff_migration_test_debug_new${PLATFORM_POSTFIX} PRIVATE "-g")
