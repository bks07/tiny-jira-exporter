# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Time zone is now used for all date/datetime fields (SKSD-8)
- Comprehensive Google-style docstrings across entire codebase
- Enhanced field type system with proper abstract base class implementation
- Support for array field types with multiple item types (string, user, component, version, option)
- Support for flagged field type with TRUE/FALSE boolean conversion
- Support for parent field type with issue key and ID extraction
- Advanced datetime handling with millisecond padding for Jira timestamps
- Configurable decimal separators for numeric fields (period/comma)
- Enhanced workflow analysis with sophisticated Kanban logic implementation
- Factory pattern for field type creation with centralized configuration
- Comprehensive error handling and validation across all field types
- Progress bar utility with dynamic console updates and message truncation

### Fixed

- 'requirements.txt' and 'requirements-dev.txt' are now up to date
- TJE breaks when parsing due date (SKSD-60)  
- TJE shows meaningless info message while exporting (SKSD-61)
- Datetime parsing issues with Jira's millisecond format handling
- Field type validation and error handling inconsistencies
- Workflow transition logic for complex backward movement scenarios
- UTF-8 encoding handling for international characters in all field types
- Memory management and performance optimization for large datasets

### Changed

- Added to README.md how to get custom field ids via API
- Applied many recommendations by Copilot
- Complete documentation modernization from Sphinx-style to Google-style docstrings
- Refactored entire field type system with abstract base class and proper inheritance
- Enhanced IssueFieldTypeFactory with configuration management and type mapping
- Improved workflow analysis with precise timestamp handling and Kanban logic
- Restructured datetime processing with timezone conversion and format flexibility
- Enhanced exporter.py with enterprise-grade documentation and error handling
- Optimized field processing pipeline with factory pattern implementation
- Upgraded progress tracking with professional console output formatting

### Removed

- None


## [0.1.1] - 2025-10-12

### Added

- Changes will now be documented inside CHANGELOG.md

### Fixed

- Jira API has changed to v3 (SKSD-59)

### Changed

- Using 'atlassian-pyton-api' module instead of 'JIRA' module
- Date formatting now uses 'datetime' and 'pytz' modules

### Removed

- None


## [0.1.0] - 2024-10-25

### Added

- All functionality as described inside README.md

### Fixed

- "Issue Type" used instead "Type" (SKSD-46)
- Eporter is lmited to 100 results (SKSD-53)
- Script does not recognize all Jira URLs (SKSD-55)
- Exporter fails when integer is used for max limit in YAML configuration file (SKSD-57)
- Exporter continues to fetch when there are no more issues (SKSD-58)

### Changed

- Changed sort order of standard issue fields within CSV export file so that it makes more sense