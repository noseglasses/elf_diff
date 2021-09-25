[![Python application](https://github.com/CapeLeidokos/elf_diff/actions/workflows/python-app.yml/badge.svg)](https://github.com/CapeLeidokos/elf_diff/actions/workflows/python-app.yml)

<h1><img style="vertical-align:middle" src="https://github.com/CapeLeidokos/elf_diff/blob/bb703f85ea24c7ee27998bb6b3e554843f31248c/images/favicon.png"> elf_diff - A Tool to Compare Elf Binaries</h1>

## An Initial Example

Before going into detail about what elf_diff does, let's start with an example of
a multi page html report that was generated as part of one of the regression tests of this project.

The test compiles, links and compares the elf files of two similar versions of a simple C++ program. The self contained HTML report that is generated 
in a subdirectory allows to explore the prominent similarities and differences between the symbols defined in the two elf files.

HTML reports look as follows. Please click on the table headers to proceed to the generated HTML pages.

[Multi Page](https://capeleidokos.github.io/elf_diff/pair_report_multi_page/index.html)                 |  [Single Page](https://capeleidokos.github.io/elf_diff/pair_report_output.html)
:-------------------------:|:-------------------------:
![](https://github.com/CapeLeidokos/elf_diff/blob/119a0b62c5d7faf2d0b7a958b46f7daf4ee8bcc7/examples/multi_page_pair_report.png)  |  ![](https://github.com/CapeLeidokos/elf_diff/blob/119a0b62c5d7faf2d0b7a958b46f7daf4ee8bcc7/examples/single_page_pair_report.png)

[Pdf reports](https://github.com/CapeLeidokos/elf_diff/blob/master/examples/elf_diff_test_static_1.pdf) may be generated alternatively.

Please see the examples section at the end of this document for more usage examples.

## Purpose

* resource/performance optimization
* debugging
* learning/teaching

The main purpose of _elf_diff_ is to determine how specific changes to a piece of software affect resource consumption and performance. The tool may also serve to compare two independent change sets or just to have fun and learn how changes reflect in the generated assembly code.

The following information is part of _elf_diff_'s report pages:
* differences in the amount of program storage and static RAM usage
* symbols that are only present in one of the two versions
* symbols whose naming or call signature is similar in both versions, e.g. as a result of symbol renaming or subtly changing call signatures
* assembly code discrepancies of functions with identical names and call signatures

As _elf_diff_ operates on elf-files, it is fairly language and platform agnostic. All it requires to work is a suitable set of [GNU Binutils](https://en.wikipedia.org/wiki/GNU_Binutils) for the target platform.

## Introduction

This tool compares pairs of ELF binary files and provides information about differences in the contained symbols with respect to the space that they occupy in program memory (functions and global data) and in RAM (global data). Binary pairs that are passed to _elf_diff_ are typically two versions of the same program/library/firmware. _elf_diff_ can help you to find out about the impact of your changes on your code's resource consumption.

The differences between the binaries are summarized in tables that contain information about persisting, disappeared and new symbols. _elf_diff_ also attempts to find pairs of matching symbols that might have been subject to renaming or signature changes (modified function arguments). Please be warned that the means to determine such symbol relations are very limited when working with binaries. False positives will result.

For all those symbols that have been subject to changes and also for the new and disappeared symbols, the tool provides diff-like comparisons of the disassembly.

All results are presented in either HTML or pdf files. HTML documents are cross-linked to conveniently allow jumping back and forth between bits of information, e.g. tabular information and symbol disassemblies. Du to the potentially large amount of information, some parts of the HTML reports are ommitted in the pdf files.

_elf_diff_ has two modes of operation, pair-reports and mass-reports. While the former compares two binaries, the latter generates an overview-report for a set of binary-pairs. Such overview-reports list only the changes in terms of symbol sizes and the amount of symbols, no disassembly is provided to gain feasible document sizes.

## Requirements

_elf_diff_ is a Python script. It mostly uses standard libraries but also some non-standard packages (see the file `requirements.txt`) for more information.

elf_diff works and is automatically tested with Python 2 and 3.

## Setup

The following procedure is required to install the _elf_diff_ Python package.

1. Install Python version >= 3.0
3. Install the elf_diff package via one of the following commands
   * `python3 -m pip install elf_diff` (Linux)
   * `py -m pip install elf_diff` (Windows)

Alternatively when developing _elf_diff_, the following steps are required:

1. Install Python version >= 3.0
2. Clone the [_elf_diff_](https://github.com/CapeLeidokos/elf_diff) repo from github.
3. Install required packages via one of the following commands
   * `python3 -m pip install -r requirements.txt` (Linux)
   * `py -m pip install -r requirements.txt` (Windows)
4. Add the `bin` directory of the _elf_diff_ repo to your platform search path

To run _elf_diff_ from the local git-sandbox, please use the script `bin/elf_diff`, e.g. as `bin/elf_diff -h` to display the help string.

## Usage

There is a small difference between running Python on Linux and Windows. To display _elf_diff_'s help page in a console window, type the following in a linux console
```
python3 -m elf_diff -h
```
or
```
py -m elf_diff -h
```
in a Windows console.

In the examples provided below, we go with the Linux syntax. Please replace the keyword `python3` with `py` when executing the respective examples in a Windows environment.

### Generating Pair-Reports

To generate a pair report, two binary files need to be passed to _elf_diff_ via the command line. Let's assume those files are named `my_old_binary.elf` and `my_new_binary.elf`. 

The following command will generate a multipage html report in a subdirectory of your current working directory.
```
python3 -m elf_diff my_old_binary.elf my_new_binary.elf
```

### Generating Mass-Reports

Mass reports require a driver file (yaml syntax) that specifies a list of binaries to compare pair-wise. 

Let's assume you have two pairs of binaries that reside in a directory `/home/my_user`.
```
binary_a_old.elf <-> binary_a_new.elf
binary_b_old.elf <-> binary_b_new.elf
```

A driver file (named `my_elf_diff_driver.yaml`) would then contain the following information:
```
binary_pairs:
    - old_binary: "/home/my_user/binary_a_old.elf"
      new_binary: "/home/my_user/binary_a_new.elf"
      short_name: "A short name"
    - old_binary: "/home/my_user/binary_b_old.elf"
      new_binary: "/home/my_user/binary_b_new.elf"
      short_name: "B short name"
```

The `short_name` parameters are used in the result tables to reference the respective binary pairs.

By using the driver file, we can now run a mass-report as 
```
python3 -m elf_diff --mass_report --driver_file my_elf_diff_driver.yaml
```

This will generate a HTML file `elf_diff_mass_report.html` in your current working directory.

### Generating pdf-Files

pdf files are generated by supplying the output file name using the parameter `pdf_file` either at the command line 

```
python3 -m elf_diff --pdf_file my_pair_report.pdf my_old_binary.elf my_new_binary.elf
```
or from within a driver file, e.g.
```
pdf_file: "my_pair_report.pdf"
```

### Specifying an Alternative HTML File Location

Similar to specifying an explicit filename for pdf files, the same can be done for our HTML output files, either via the command line
```
python3 -m elf_diff --html_file my_pair_report.hmtl my_old_binary.elf my_new_binary.elf
```
or from within a driver file, e.g.
```
html_file: "my_pair_report.html"
```
this will create a single file HTML report (with the exact same content as generated pdf files).

### Specifying an Alternative HTML Directory

To generate a multi-page HTML report use the command line flag `--html_dir` to generate the HTML files e.g. in directory `my_target_dir`.
```
python3 -m elf_diff --html_dir my_target_dir my_pair_report.hmtl my_old_binary.elf my_new_binary.elf
```

### Using Driver Files

The driver files that we already met when generating mass-reports can also generally be used to run _elf_diff_. Any parameters that can be passed as command line arguments to _elf_diff_ can also occur in a driver file, e.g.
```
python3 -m elf_diff --mass_report --pdf_file my_file.pdf ...
```
In `my_elf_diff_driver.yaml`
```
mass_report: True
pdf_file: my_file.pdf
...
```
### Supplying a Project Title

A project title could e.g. be a short name that summarizes the changes that you applied between the old and the new version of the compared binaries. Supply a title via the parameter `project_title`.

### Adding Background Information

Additional information about the compared binaries can be added to pair-reports. Use the parameters `old_info_file` and `new_info_file` to supply filenames of text files whose content is supposed to be added to the report.

It is also possible to add general information to reports, e.g. about programming language or compiler version or about the build-system. This is supported through the `build_info` parameter which enables supplying a string that is added to the report. For longer strings, this can be conveniently done via the driver-file.

Everything that follows after `build_info: >` in the example will be added to the report.
```
build_info: >
  This build
  info is added to the report.
  The whitespaces in front of these lines are removed, the line breaks are
  preserved.
```

### Using Alias Strings

If you want to obtain anonymized reports, it is not desirable to reveile details about your user name (home directory) or the directory structure. In such a case, the binary filenames can be replaced by alias wherever they would appear in the reports. 

Supply alias names using the `old_alias` and `new_alias` parameters for the old or the new version of the binaries, respectively.

### Working with Cross-Build Binaries

When working on firmware projects for embedded devices, you typically will be using a cross-build environment. If based on GNU gcc, such an environment usually not only ships with the necessary compilers but also with a set of additional tools called [GNU Binutils](https://en.wikipedia.org/wiki/GNU_Binutils).

_elf_diff_ uses some of these tools to inspect binaries, namely `nm`, `objdump` and `size`. Although some information about binaries can be determined even with the host-version of these tools, it is e.g. not possible to retreive disassemblies.

In a cross-build environment, Binutils executable are usually bundled in a specific directory. They also often have a platform-specific prefix, to make them distinguishabel from their host-platform siblings. For the [avr](https://en.wikipedia.org/wiki/AVR_microcontrollers)-version of Binutils e.g., that is shipped with the [Arduino](https://en.wikipedia.org/wiki/Arduino) development suite, the prefix `avr-` is used. The respective commands are, thus, named `avr-nm`, `avr-objdump` and `avr-size`.

To make those dedicated binaries known to _elf_diff_, please add the binutils directory to the PATH environment variable, use the parameters `bin_dir` and `bin_prefix` or explicitly define the 
commands e.g. `objdump_command` (see command help).

A pair-report generation command for the avr-plattform would e.g. read

```
python3 -m elf_diff --bin_dir <path_to_avr_binaries> --bin_prefix "avr-" my_old_binary.elf my_new_binary.elf
```
The string `<path_to_avr_binaries>` in the above example would of course be replaced by the actual directory path where the binaries live.

### Generating a Template Driver File

To generate a template driver file that can serve as a basis for your own
driver files, just run _elf_diff_ with the `driver_template_file` parameter, e.g. as
```
python3 -m elf_diff --driver_template_file my_template.yaml
```

Template files contain the default values of all available parameters, or - if the temple file is generated in the same session where a report was created - the template file will contain the actual settings used for the report generation.

### Selecting and Excluding Symbols

By means of the command line arguments `symbol_selection_regex` and `symbol_exclusion_regex`, symbols can be explicitly selected and excluded.
The specified regular expressions are applied to both the old and the old binary. For more fine grained selection, please used the `*_old` and `*_new` versions of the 
respective command line arguments.

### Assembly Code

For most developers who are used to program in high level languages, assembly code is a mystery.
Still, there is some information that an assembly-novice can gather from observing assembly code. Starting with the number of assembly code statements. Normally less means good. The more assembly statements there are representing a high level language statement, the more time the processor needs to process them. On the contrary, sometimes there may be a suspiciously low number of assembly statements which might indicate that the compiler has optimized away something that it shouldn't have.

All this, of course, relies on the knowledge about what assembly code is associated with which line of source.
This information is not included in compiled binaries by default. The compiler must explicitly be told to export additional debugging information. For the gcc-compiler the flag `-g`, e.g., will cause this information to be emitted. But careful, some build systems when building debug versions replace optimization flags like `-O3` with the debug flag `-g`. This is not what you want when looking at the performance of your code. Instead you want to add the `-g` flag and keep the optimization flag(s) in place. CMake, e.g. has a configuration variable `CMAKE_BUILD_TYPE` that can be set to the value `RelWithDebInfo` to enable a release build (with optimization enabled) that also comes with debug symbols.

For binaries with debug symbols included, elf_diff will annotate the assembly code by adding the high level language statements that it was generated from.

## Examples

### Simple Example

An [example](https://github.com/CapeLeidokos/elf_diff/blob/master/examples/elf_diff_test_static_1.pdf) taken from the regression test bench that compares two binaries of two very simple C++ programs.

### libstdc++

[Comparison of two versions of libstdc++](https://github.com/CapeLeidokos/elf_diff/blob/master/examples/libstdc++_std_string_diff.pdf) shipping with gcc 4.8 and 5. There are vast differences between those two library versions which result in a great number of symbols being reported. The following command demonstrates how report generation can be resticted to a subset of symbols by using regular expressions.
In the example we select only those symbols related to class `std::string`.

```
# Generated on Ubuntu 20.04 LTS 
python3 -m elf_diff \
   --symbol_selection_regex "^std::string::.*"   # select any symbol name starting with std::string:: \
   --pdf_file libstdc++_std_string_diff.pdf      # generate a pdf file \
   /usr/lib/gcc/x86_64-linux-gnu/4.8/libstdc++.a # path to old binary \
   /usr/lib/gcc/x86_64-linux-gnu/5/libstdc++.a   # path to new binary
```

## TODO

The following is a list of features that would be nice to have and will or will not be added
in the future:

* read debug symbols from separate debug libraries and annotate assembly code
