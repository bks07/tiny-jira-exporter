# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Added a changelog

### Fixed

- ...

### Changed

- ...

### Removed

- ...

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