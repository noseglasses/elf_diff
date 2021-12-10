# -*- coding: utf-8 -*-

# -*- mode: python -*-
#
# elf_diff
#
# Copyright (C) 2021  Noseglasses (shinynoseglasses@gmail.com)
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
from elf_diff_test.test_in_subdirs import TestCaseWithSubdirs
from elf_diff_test.elf_diff_execution import ElfDiffExecutionMixin
from elf_diff_test.test_binaries import getTestBinary
from elf_diff_test.args_watcher import ElfDiffCommandLineArgsWatcher, ArgsList
from elf_diff_test.test_binaries import TESTING_DIR

from elf_diff.__main__ import RETURN_CODE_WARNINGS_OCCURRED

import os
import unittest
from typing import Optional

OLD_MANGLING_FILE_GHS: str = os.path.join(
    TESTING_DIR, "ghs", "libelf_diff_test_release_old.a.demangle.txt"
)
NEW_MANGLING_FILE_GHS: str = os.path.join(
    TESTING_DIR, "ghs", "libelf_diff_test_release_new.a.demangle.txt"
)
TEST_PLUGIN: str = os.path.join(TESTING_DIR, "plugin", "test_plugin.py")

if os.name == "nt":
    STANDARD_BIN_DIR = r"C:\msys64\mingw64\bin"
    ARM_BIN_PREFIX = "arm-none-eabi-"
    EXE_SUFFIX = ".exe"
else:
    STANDARD_BIN_DIR = "/usr/bin"
    ARM_BIN_PREFIX = "arm-linux-gnueabi-"
    EXE_SUFFIX = ""


class TestCommandLineArgs(ElfDiffExecutionMixin, TestCaseWithSubdirs):

    ELF_DIFF_COMMAND_LINE_ARGS_WATCHER = ElfDiffCommandLineArgsWatcher()
    # ELF_DIFF_COMMAND_LINE_args_WATCHER.printTestSkeletons()

    @classmethod
    def tearDownClass(cls) -> None:
        super(TestCommandLineArgs, cls).tearDownClass()
        TestCommandLineArgs.ELF_DIFF_COMMAND_LINE_ARGS_WATCHER.testIfAllArgsUsedAtLeastOnce()

    def registerArgUsed(self, key: str, value: Optional[str]) -> None:
        TestCommandLineArgs.ELF_DIFF_COMMAND_LINE_ARGS_WATCHER.considerArgTested(key)

    def test_run_elf_diff_without_debug(self):
        # By resetting the default args, we make sure that the --debug flag is removed
        self.default_args = []
        self.runSimpleTest()

    def test_bin_dir(self):
        self.runSimpleTest([("bin_dir", STANDARD_BIN_DIR)])

    def test_bin_prefix1(self):
        self.runSimpleTestArm([("bin_prefix", ARM_BIN_PREFIX)])

    @unittest.expectedFailure
    def test_bin_prefix2(self):
        self.runSimpleTestArm([("bin_prefix", "___bad_prefix___")])

    def test_build_info(self):
        self.runSimpleTest([("build_info", "Some buildinfo string")])

    def test_consider_equal_sized_identical(self):
        self.runSimpleTest([("consider_equal_sized_identical", None)])

    def test_driver_file(self):

        elf_diff_test_yaml_file = "pair_report.elf_diff_test.yml"

        pdf_file = "driven_pair_report_output.pdf"
        html_file = "driven_pair_report_output.html"
        html_dir = "driven_pair_report_multi_page"
        template_file = "driven_pair_report_output.tmpl.yml"

        with open(elf_diff_test_yaml_file, "w") as f:

            f.write(
                "old_binary_filename: '"
                + getTestBinary("x86_64", "test", "release", "old")
                + "'\n"
            )
            f.write(
                "new_binary_filename: '"
                + getTestBinary("x86_64", "test", "release", "new")
                + "'\n"
            )
            f.write("old_alias: " + "an_old_alias\n")
            f.write("new_alias: " + "a_new_alias\n")
            f.write(
                "old_info_file: '"
                + os.path.join(TESTING_DIR, "old_binary_info.txt")
                + "'\n"
            )
            f.write(
                "new_info_file: '"
                + os.path.join(TESTING_DIR, "new_binary_info.txt")
                + "'\n"
            )
            f.write("build_info: >\n")
            f.write("  Build info.\n")
            f.write("  More build info.\n")
            f.write("html_file: '" + html_file + "'\n")
            f.write("html_dir: '" + html_dir + "'\n")
            f.write("pdf_file: '" + pdf_file + "'\n")
            f.write("project_title: '" + "Project title'\n")
            f.write("driver_template_file: '" + template_file + "'\n")

        self.runElfDiff(args=[("driver_file", elf_diff_test_yaml_file)])

        # Check if all output files exist
        #
        self.assertTrue(os.path.isfile(pdf_file))
        self.assertTrue(os.path.isfile(html_file))
        self.assertTrue(os.path.isfile(template_file))

    def test_driver_template_file(self):
        driver_template_file = "elf_diff_test_template.yml"
        self.runSimpleTest([("driver_template_file", driver_template_file)])
        self.assertTrue(os.path.isfile(driver_template_file))

    def test_dump_document_structure(self):
        self.runSimpleTest([("dump_document_structure", None)])

    def test_html_dir(self):
        html_dir = "parameter_test_multi_page_pair_report"
        self.runSimpleTestBase([("html_dir", html_dir)])
        self.assertTrue(os.path.isdir(html_dir))

    def test_html_file(self):  # pylint: disable=no-self-use
        # Already tested by all simple tests
        pass

    def test_html_template_dir(self):
        # Parameter currently not exported
        # source_template_path = os.path.join(root_dir, "src", "elf_diff", "html")
        # target_template_path = "template_copy"
        # shutil.copytree(source_template_path, target_template_path)
        # self.runSimpleTest([("html_template_dir": target_template_path})
        pass

    def test_json_file(self):
        self.runSimpleTest([("json_file", "output.json")])

    def test_language1(self):
        self.runSimpleTest([("language", "c++")])

    @unittest.expectedFailure
    def test_language2(self):
        self.runSimpleTest([("language", "___unknown___")])

    def test_list_default_plugins(self):
        self.runSimpleTest([("list_default_plugins", None)])

    def test_load_default_plugin_success(self):
        self.runSimpleTest(
            [
                (
                    "load_default_plugin",
                    "html_export;single_page=True;output_file=bla.html",
                )
            ]
        )

    @unittest.expectedFailure
    def test_load_default_plugin_failure1(self):
        self.runSimpleTest(
            [
                (
                    "load_default_plugin",
                    "some_unknown_default_plugin",
                )
            ]
        )

    @unittest.expectedFailure
    def test_load_default_plugin_failure2(self):
        self.runSimpleTest(
            [
                (
                    "load_default_plugin",
                    "html_export;some_bad_parameter=i_m_bad",
                )
            ]
        )

    def test_load_plugin_success1(self):
        self.runSimpleTest(
            [
                (
                    "load_plugin",
                    f"{TEST_PLUGIN};TestExportPairReportPlugin;magic_words=clatu_ferrata_nectu",
                )
            ]
        )

    def test_load_plugin_success2(self):
        self.runSimpleTest(
            [
                (
                    "load_plugin",
                    f"{TEST_PLUGIN};TestExportPairReportPlugin",
                )
            ]
        )

    @unittest.expectedFailure
    def test_load_plugin_failure(self):
        self.runSimpleTest(
            [
                (
                    "load_plugin",
                    f"{TEST_PLUGIN};TestExportPairReportPlugin;some_unknown_keyword=foo",
                )
            ]
        )

    def _testMassReport(self, args: Optional[ArgsList] = None):

        elf_diff_test_yaml_file = "mass_report.elf_diff_test.yml"

        pdf_file = "driven_mass_report_output.pdf"
        html_file = "driven_mass_report_output.html"
        template_file = "driven_mass_report_output.tmpl.yml"

        with open(elf_diff_test_yaml_file, "w") as f:

            f.write("build_info: >\n")
            f.write("  Build info.\n")
            f.write("  More build info.\n")
            f.write("html_file: '" + html_file + "'\n")
            f.write("pdf_file: '" + pdf_file + "'\n")
            f.write("project_title: 'Project title'\n")
            f.write("driver_template_file: '" + template_file + "'\n")

            f.write("binary_pairs:\n")
            f.write(
                "    - old_binary: '"
                + getTestBinary("x86_64", "test", "release", "old")
                + "'\n"
            )
            f.write(
                "      new_binary: '"
                + getTestBinary("x86_64", "test", "release", "new")
                + "'\n"
            )
            f.write("      short_name: 'First binary name'\n")
            f.write(
                "    - old_binary: '"
                + getTestBinary("x86_64", "test2", "release", "old")
                + "'\n"
            )
            f.write(
                "      new_binary: '"
                + getTestBinary("x86_64", "test2", "release", "new")
                + "'\n"
            )
            f.write("      short_name: 'Second binary name'\n")

        args = args or []
        args.append(("driver_file", elf_diff_test_yaml_file))

        self.runElfDiff(args=args)

        # Check if all output files exist
        #
        self.assertTrue(os.path.isfile(pdf_file))
        self.assertTrue(os.path.isfile(html_file))
        self.assertTrue(os.path.isfile(template_file))

    def test_mass_report1(self):
        self._testMassReport()

    def test_mass_report2(self):
        self._testMassReport(args=[("mass_report", None)])

    def test_new_alias(self):
        self.runSimpleTest([("new_alias", "New alias")])

    def test_new_binary_filename(self):  # pylint: disable=no-self-use
        # This is already tested by all simple tests
        pass

    def test_new_info_file(self):
        new_info_file = "new_info.txt"
        with open(new_info_file, "w") as f:
            f.write("Some additional new info")
        self.runSimpleTest([("new_info_file", new_info_file)])

    def test_new_mangling_file(self):
        self.expected_return_code = RETURN_CODE_WARNINGS_OCCURRED
        self.runSimpleTestGhs([("new_mangling_file", NEW_MANGLING_FILE_GHS)])

    def test_nm_command(self):
        self.runSimpleTest(
            [("nm_command", os.path.join(STANDARD_BIN_DIR, f"nm{EXE_SUFFIX}"))]
        )

    def test_objdump_command(self):
        self.runSimpleTest(
            [
                (
                    "objdump_command",
                    os.path.join(STANDARD_BIN_DIR, f"objdump{EXE_SUFFIX}"),
                )
            ]
        )

    def test_old_alias(self):
        self.runSimpleTest([("old_alias", "Old alias")])

    def test_old_binary_filename(self):  # pylint: disable=no-self-use
        # This is already tested by all simple tests
        pass

    def test_old_info_file(self):
        old_info_file = "old_info.txt"
        with open(old_info_file, "w") as f:
            f.write("Some additional old info")
        self.runSimpleTest([("old_info_file", old_info_file)])

    def test_old_mangling_file(self):
        self.expected_return_code = RETURN_CODE_WARNINGS_OCCURRED
        self.runSimpleTestGhs([("old_mangling_file", OLD_MANGLING_FILE_GHS)])

    def test_pdf_file(self):
        pdf_file = "parameter_test_single_page_pair_report.pdf"
        self.runSimpleTestBase([("pdf_file", pdf_file)])
        self.assertTrue(os.path.isfile(pdf_file))

    def test_project_title(self):
        self.runSimpleTest([("project_title", "A Project")])

    def test_readelf_command(self):
        self.runSimpleTest(
            [
                (
                    "readelf_command",
                    os.path.join(STANDARD_BIN_DIR, f"readelf{EXE_SUFFIX}"),
                )
            ]
        )

    def test_similarity_threshold(self):
        self.runSimpleTest([("similarity_threshold", "0.5")])

    def test_size_command(self):
        self.runSimpleTest(
            [("size_command", os.path.join(STANDARD_BIN_DIR, f"size{EXE_SUFFIX}"))]
        )

    def test_skip_details(self):
        self.runSimpleTest([("skip_details", None)])

    def test_skip_persisting_same_size(self):
        self.runSimpleTest([("skip_persisting_same_size", None)])

    def test_skip_symbol_similarities(self):
        self.runSimpleTest([("skip_symbol_similarities", None)])

    def test_source_prefix1(self):
        self.runSimpleTest(
            [("old_source_prefix", "src/old/"), ("new_source_prefix", "src/new/")]
        )

    def test_source_prefix2(self):
        self.runSimpleTest([("source_prefix", "src/")])

    def test_symbol_exclusion_regex(self):
        self.runSimpleTest2([("symbol_exclusion_regex", ".*IStay.*")])

    def test_symbol_exclusion_regex_new(self):
        self.runSimpleTest2([("symbol_exclusion_regex_new", ".*IStay.*")])

    def test_symbol_exclusion_regex_old(self):
        self.runSimpleTest2([("symbol_exclusion_regex_old", ".*IStay.*")])

    def test_symbol_selection_regex(self):
        self.runSimpleTest2([("symbol_selection_regex", ".*IStay.*")])

    def test_symbol_selection_regex_new(self):
        self.runSimpleTest2([("symbol_selection_regex_new", ".*IStay.*")])

    def test_symbol_selection_regex_old(self):
        self.runSimpleTest2([("symbol_selection_regex_old", ".*IStay.*")])

    def test_txt_file(self):
        self.runSimpleTest([("txt_file", "output.txt")])

    def test_xml_file(self):
        self.runSimpleTest([("xml_file", "output.xml")])

    def test_yaml_file(self):
        self.runSimpleTest([("yaml_file", "output.yaml")])
