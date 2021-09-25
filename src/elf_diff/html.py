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
import codecs
import jinja2
from jinja2 import Environment, FileSystemLoader, StrictUndefined


def escapeString(string):
    return string.replace("<", "&lt;").replace(">", "&gt;")


def formatNumber(number):
    return '<span class="number">%s</span>' % (number)


def highlightNumberClass(number):
    if number > 0:
        return "deterioration"
    elif number < 0:
        return "improvement"

    return "unchanged"


def highlightNumber(number):
    css_class = highlightNumberClass(number)

    if number == 0:
        return '<span class="%s number">%d</span>' % (css_class, number)

    return '<span class="%s number">%+d</span>' % (css_class, number)


def highlightNumberDelta(old_size, new_size):
    return highlightNumber(new_size - old_size)


def preHighlightSourceCode(src):
    return "__ED_SOURCE_START__%s__ED_SOURCE_END__" % (src)


def postHighlightSourceCode(src):
    return src.replace("__ED_SOURCE_START__", '<span class="source">').replace(
        "__ED_SOURCE_END__", "</span>"
    )


def postHighlightSourceCodeRemoveTags(src):
    return src.replace("__ED_SOURCE_START__", "").replace("__ED_SOURCE_END__", "")


def replaceHighlights(src):
    return src.replace("__HIGHLIGHT_START__", '<span class="diff_highlight">').replace(
        "__HIGHLIGHT_END__", "</span>"
    )


def diffStringsSource(str1, str2):
    seqm = difflib.SequenceMatcher(None, str1, str2)
    output = []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == "equal":
            output.append(seqm.a[a0:a1])
        elif opcode == "insert":
            pass
        elif opcode == "delete":
            output.append("__HIGHLIGHT_START__" + seqm.a[a0:a1] + "__HIGHLIGHT_END__")
        elif opcode == "replace":
            output.append("__HIGHLIGHT_START__" + seqm.a[a0:a1] + "__HIGHLIGHT_END__")
        else:
            raise RuntimeError("unexpected opcode")

    return replaceHighlights(escapeString("".join(output)))


def diffStringsTarget(str1, str2):
    seqm = difflib.SequenceMatcher(None, str1, str2)
    output = []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == "equal":
            output.append(seqm.a[a0:a1])
        elif opcode == "insert":
            output.append("__HIGHLIGHT_START__" + seqm.b[b0:b1] + "__HIGHLIGHT_END__")
        elif opcode == "delete":
            pass
        elif opcode == "replace":
            output.append("__HIGHLIGHT_START__" + seqm.b[b0:b1] + "__HIGHLIGHT_END__")
        else:
            raise RuntimeError("unexpected opcode")

    return replaceHighlights(escapeString("".join(output)))


def configureTemplate(settings, template_filename, keywords):

    template_path = settings.module_path + "/html"

    env = Environment(loader=FileSystemLoader(template_path), undefined=StrictUndefined)

    try:
        creator = env.get_template(template_filename)

    except jinja2.exceptions.TemplateError as e:
        unrecoverableError("Failed creating jinja creator\n" + str(e))

    try:
        sys.stdout.flush()
        replacedContent = creator.render(keywords)
    except (jinja2.exceptions.TemplateError) as e:
        unrecoverableError(
            "Failed rendering jinja template '" + template_filename + "'\n" + str(e)
        )

    return replacedContent


def configureTemplateWrite(settings, template_filename, html_output_filename, keywords):

    with codecs.open(html_output_filename, "w", "utf-8") as html_output_file:
        html_code = configureTemplate(settings, template_filename, keywords)
        html_output_file.write(html_code)
