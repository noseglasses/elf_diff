# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2021-11-05
### Added
- Badges at the top of README.md file
- Documents Weasyprint usage in README.md
- Documents PyPI package name inconsistency
- Mangling files for compilers with exotic name mangling that do not provide binutils
- Similar symbols detection and output can now explicitly disabled for performance reasons
- CI tests on Windows
- CI code coverage testing (line & branch coverage)
- CI codacy code quality testing
- Github CI now deploys examples to gh_pages
- CONTRIBUTING.md file
- CODE_OF_CONDUCT.md file
- Github issue templates
- A second simple example for testing and documentation (also deployed on gh_pages)
- Balloons with additional information are displayed when hovering over HTML table headers
- Statistics now comprise the total number and the number of selected and excluded symbols
of each binary in addition to the selection and exclusion regex
- Added means to gess whether symbol demangling is available
- Plugin system added
- Report generation now taken over by plugins
- Added YAML, JSON and TXT reports
- Between the extraction of symbols from the binaries and the report generation a
new central data structure, the _document tree_ is established
- Jinja2 templates of the html export plugin now operate directly on the document tree
- Custom plugins can be loaded from the command line
- Command line flag added to write the document tree to stdout
- HTML reports now additionally output tree formatted information to aid changing the Jinja templates or writing custom versions

### Changed
- Initial example in README.md improved
- README.md restructured
- Added and improved tests
- Tests write their output to a directory structure that matches the fixture and test names
of the Python test definition
- Python requirements mostly tied to exact versions
- Mass reports deprecated
- Mass reports Jinja template simplified
- Symbol type 'new' renamed to 'appeared in order not to conflict with the distinction old/new
- 'Symbol similarity' renamed 'signature similarity'

### Removed
- Unused package requirement pdfkit

## [0.3.4] - 2021-10-17
### Changed
- Fixes github issue 51 (https://github.com/noseglasses/elf_diff/issues/51):
Pair report generation broken

## [0.3.3] - 2021-09-26
### Changed
- Fixes broken Python package version again

## [0.3.2] - 2021-09-26
### Changed
- Fixes broken Python package version again

## [0.3.1] - 2021-09-26
### Changed
- Fixes broken Python package version

## [0.3.0] - 2021-09-25
### Added
- PyPI Python package installable via pip
- Enhanced CI for testing Python build, packaging and package installation from a local path

## [0.2.0] - 2021-09-21
### Added
- Multi-page HTML reports
- Select and exclude symbols via regular expressions
- A fancy Logo
- Self contained HTML reports

### Changed
- Fix internal links in pdf reports

## [0.1.0] - 2019-05-02
### Added
- Initial release
