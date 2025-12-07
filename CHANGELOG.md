# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

This release will focus on harmonizing the loading process for the YAML config file.

### Added

- None.

### Changed

- None.

## Deprecated

- None.

## Removed

- None.

### Fixed

- None.

### Security

- None.

## [0.2.0] - 2025-12-07

This release focused on a mayor refactoring I had already planned for a long time.
It is a first step towards increased robustness and better code structure.

The main aspect of this release is, that extracted issue fields are now handled according to their correct field type.
This happens dynamically as the extractor fetches the field types for each field and then applies the correct field handling.

### Added

- Time zone is now used for all date/datetime fields (SKSD-8)
- Datetime processing with timezone conversion and format flexibility (SKSD-8)
- Support for array field types with multiple item types (string, user, component, version, option)
- Support for flagged field type with TRUE/FALSE boolean conversion (SKSD-21)
- Support for parent field type with issue key and ID extraction (SKSD-45)
- Advanced datetime handling with seconds (SKSD-65) and millisecond (SKSD-66) padding for Jira timestamps

### Changed

- Enhanced field type system with proper abstract base class implementation, including factory pattern for field type creation with centralized configuration
- Complete documentation modernization from Sphinx-style to Google-style docstrings (SKSD-64)
- Enhanced exporter.py with enterprise-grade documentation and error handling (SKSD-64)

## Deprecated

- None.

## Removed

- I did not compile the code - there will be no Windows executable in future

### Fixed

- 'requirements.txt' and 'requirements-dev.txt' are now up to date (SKSD-62)
- TJE breaks when parsing due date (SKSD-60)  
- TJE shows meaningless info message while exporting (SKSD-61)
- UTF-8 encoding handling for international characters in all field types (SKSD-3)

### Security

- None.

## [0.1.1] - 2025-10-12

This release focused on fixing the issue that Atlassian changed the API to version 3.
Therefore, I replaced the 3rd party JIRA module with Atlassian's official Jira Python API module.
However, in the end, after publishing, it turned out that TJE breaks when parsing the due date field (SKSD-60).

### Added

- Changes will now be documented inside CHANGELOG.md

### Changed

- Using 'atlassian-pyton-api' module instead of 'JIRA' module
- Date formatting now uses 'datetime' and 'pytz' modules

## Deprecated

- None.

## Removed

- None.

### Fixed

- Jira API has changed to v3 (SKSD-59)

### Security

- None.

## [0.1.0] - 2024-10-25

First release.

### Added

- All functionality as described inside README.md

### Changed

- Changed sort order of standard issue fields within CSV export file so that it makes more sense

## Deprecated

- None.

## Removed

- None.

### Fixed

- "Issue Type" used instead "Type" (SKSD-46)
- Eporter is lmited to 100 results (SKSD-53)
- Script does not recognize all Jira URLs (SKSD-55)
- Exporter fails when integer is used for max limit in YAML configuration file (SKSD-57)
- Exporter continues to fetch when there are no more issues (SKSD-58)

### Security

- None.
