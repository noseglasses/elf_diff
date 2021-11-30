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
from elf_diff_test.test_binaries import TESTING_DIR

from deepdiff import DeepDiff  # type: ignore # Make mypy ignore this module
from pprint import pformat
import json
import os
from typing import Dict, List
from bs4 import BeautifulSoup  # type: ignore # Make mypy ignore this module
import glob
import pathlib


def traverse(soup):
    dom_dictionary = {}

    if soup.name is not None:
        dom_dictionary["name"] = soup.name
    else:
        dom_dictionary["value"] = soup.string

    if hasattr(soup, "attrs"):
        dom_dictionary["attrs"] = soup.attrs
    if hasattr(soup, "children"):
        dom_dictionary["children"] = [
            traverse(child) for child in soup.children
        ]  # if child.name is not None]

    return dom_dictionary


def htmlDictFromFile(filename: str) -> Dict:
    with open(filename, "r") as f:
        # soup = BeautifulSoup(f, 'html.parser')
        soup = BeautifulSoup(f, "html5lib")
        # print(soup)
        # print(soup.__dict__)
        return traverse(soup)


def compareHTMLFiles(filename1: str, filename2: str, exclude_paths: List) -> None:
    # The output file is generated in the current directory
    if not os.path.exists(filename1):
        raise Exception(f"Missing file 1 '{filename1}'")
    tree1: Dict = htmlDictFromFile(filename1)

    if not os.path.exists(filename2):
        raise Exception(f"Missing file 2 '{filename2}'")
    tree2: Dict = htmlDictFromFile(filename2)

    diff = DeepDiff(tree1, tree2, exclude_paths=exclude_paths)

    if len(diff) > 0:
        diff_str: str = pformat(diff, indent=2)
        raise Exception(
            f"documents '{filename1}' and '{filename2}' differ:\n{diff_str}"
        )


class TestDocumentIntegrity(ElfDiffExecutionMixin, TestCaseWithSubdirs):
    def test_document_simple_json(self):
        output_file = "output.json"
        self.runSimpleTest([("json_file", output_file)])

        # The output file is generated in the current directory
        if not os.path.exists(output_file):
            raise Exception(f"Missing output file '{output_file}'")
        test_tree: Dict
        with open(output_file, "r") as f:
            test_tree = json.load(f)

        reference_document: str = os.path.join(
            TESTING_DIR, "x86_64", "reference_document.json"
        )
        if not os.path.exists(reference_document):
            raise Exception(f"Missing reference document file '{reference_document}'")
        reference_tree: Dict
        with open(reference_document, "r") as f:
            reference_tree = json.load(f)

        exclude_paths = [
            "root['document']['files']['input']['new']['binary_path']",
            "root['document']['files']['input']['old']['binary_path']",
            "root['document']['general']['elf_diff_repo_root']",
            "root['document']['general']['elf_diff_version']",
            "root['document']['general']['generation_date']",
        ]
        diff = DeepDiff(reference_tree, test_tree, exclude_paths=exclude_paths)

        if len(diff) > 0:
            diff_str: str = pformat(diff, indent=2)
            raise Exception("documents differ:\n%s" % diff_str)

    def test_document_simple_html_file(self):
        output_file = "output.html"
        self.runSimpleTestBase(
            args=[("html_file", output_file)], output_file=output_file
        )

        reference_file: str = os.path.join(
            TESTING_DIR, "x86_64", "reference_document.html"
        )

        exclude_paths = [
            "root['children'][1]['children'][2]['children'][3]['children'][1]['children'][1]['children'][3]['children'][0]['value']"
        ]

        compareHTMLFiles(output_file, reference_file, exclude_paths)

    def test_document_simple_html_dir(self):
        output_dir = "output"
        self.runSimpleTestBase(args=[("html_dir", output_dir)])

        reference_dir: str = pathlib.Path(TESTING_DIR, "x86_64", "reference_multi_page")

        exclude_paths_by_file = {
            "output/index.html": [
                "root['children'][1]['children'][2]['children'][1]['children'][13]['children'][1]['children'][1]['children'][1]['children'][0]['value']"
            ],
            "output/document.html": [
                "root['children'][1]['children'][2]['children'][41]['children'][0]['value']",
                "root['children'][1]['children'][2]['children'][5]['children'][0]['value']",
            ],
        }

        if not os.path.exists(output_dir):
            raise Exception(f"Missing output dir '{output_dir}'")
        for filename in glob.iglob(output_dir + "/**/*.html", recursive=True):
            source_file = pathlib.Path(filename)
            rel = source_file.relative_to(output_dir)

            target_file = reference_dir.joinpath(rel)

            exclude_paths = exclude_paths_by_file.get(str(source_file), [])

            compareHTMLFiles(str(source_file), str(target_file), exclude_paths)
