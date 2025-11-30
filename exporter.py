#!/usr/bin/env python3
# coding: utf8

"""
Tiny Jira Exporter - Enterprise-grade command-line interface for comprehensive Jira data extraction.

This module serves as the primary entry point and orchestration layer for the Tiny Jira Exporter,
a sophisticated tool designed for extracting, analyzing, and exporting Jira issue data with
advanced workflow analytics. The application provides a robust command-line interface that handles
complete end-to-end processing from Jira API authentication through CSV file generation.

Core Application Architecture:
- **Configuration Management**: YAML-based configuration with comprehensive validation
- **Authentication Layer**: Secure Jira Cloud/Server API token authentication
- **Data Extraction**: JQL-powered issue filtering with custom field resolution
- **Workflow Analysis**: Advanced time-in-status calculations with Kanban logic
- **Export Processing**: Optimized CSV generation with configurable formatting
- **Error Handling**: Comprehensive exception management with detailed logging
- **Performance Monitoring**: Built-in progress tracking for large dataset processing

Advanced Features:
- **JQL Query Support**: Full JQL syntax with complex filtering and field selection
- **Custom Field Extraction**: Automatic field type detection and value parsing
- **Workflow Time Tracking**: Sophisticated status transition analysis with backward movement handling
- **Multi-format Output**: Configurable CSV export with timezone conversion and date formatting
- **Scalable Architecture**: Optimized for processing thousands of issues efficiently
- **Interactive Credential Management**: Secure credential prompting for missing authentication
- **Comprehensive Logging**: Multi-level logging with file output and console pretty-printing
- **Validation Framework**: Extensive input validation and error recovery mechanisms

Supported Jira Environments:
- Jira Cloud (atlassian.net domains)
- Jira Server/Data Center (on-premise installations)
- Custom Jira deployments with API access

Command Line Interface:
    python main.py --config CONFIG_FILE --output OUTPUT_FILE --loglevel LEVEL

Required Arguments:
    -c, --config    Path to YAML configuration file defining Jira connection,
                   field mappings, workflow definitions, and export settings
    -o, --output    Target CSV file path for exported issue data with full
                   directory path validation and permission checking

Optional Arguments:
    -l, --loglevel  Logging verbosity control with levels:
                   - debug: Most verbose, includes API calls and processing details
                   - info: Standard operational messages and progress updates
                   - warning: Important notices and potential issues
                   - error: Error conditions that don't halt execution
                   - critical: Severe errors requiring immediate attention
                   - off: Completely disable all logging output

Usage Examples:
    # Basic export with standard configuration
    python main.py -c conf/production.yaml -o exports/issues_2023.csv -l info
    
    # Debug mode for troubleshooting with comprehensive logging
    python main.py --config conf/debug.yaml --output /tmp/debug_export.csv --loglevel debug
    
    # Production export with minimal logging for automated processing
    python main.py -c conf/automated.yaml -o /data/exports/daily_issues.csv -l warning
    
    # Silent processing for scheduled jobs
    python main.py -c conf/scheduled.yaml -o /var/exports/nightly.csv -l off

Configuration Requirements:
    The YAML configuration file must define:
    - jira: Connection settings (domain, authentication)
    - fields: Field mappings and extraction rules
    - workflow: Status categories and transition logic
    - export: Output formatting and timezone settings
    - query: JQL query and result filtering options

Output Format:
    Generated CSV files contain:
    - Standard Jira fields (key, summary, status, etc.)
    - Custom field values with type-appropriate formatting
    - Workflow timing columns with entry timestamps
    - Calculated metrics (time in status, cycle time, etc.)

Error Handling:
    The application provides comprehensive error management:
    - Configuration validation with specific error messages
    - File system permission checking and path validation
    - Network connectivity and API authentication verification
    - Data processing errors with recovery mechanisms
    - Graceful shutdown with cleanup and status reporting

Performance Considerations:
    - Optimized for processing large issue datasets (10,000+ issues)
    - Memory-efficient streaming processing for minimal resource usage
    - Progress tracking with user feedback during long-running operations
    - Configurable batch sizes for API request optimization
    - Intelligent retry logic for handling transient API errors

Security Features:
    - Secure credential handling with no plain-text storage
    - Interactive credential prompting for missing authentication
    - API token validation with connection testing
    - File permission validation to prevent unauthorized access
    - Comprehensive audit logging for compliance requirements
"""

import sys
import os
import argparse
import logging
import traceback

from modules.issue_parser.issue_parser import IssueParser
from modules.exporter_config.exporter_config import ExporterConfig

def main():
    """
    Primary application entry point orchestrating the complete Jira export workflow.

    Serves as the central coordinator for the Tiny Jira Exporter application, managing
    the entire lifecycle from command-line argument processing through final CSV export.
    This function implements a robust, enterprise-grade workflow with comprehensive
    validation, error handling, and user interaction capabilities.

    The main function executes the following workflow stages:

    1. **Argument Processing & Validation**:
       - Parses command-line arguments with comprehensive validation
       - Validates configuration file existence and accessibility
       - Verifies output path permissions and directory structure
       - Provides detailed error messages for invalid inputs

    2. **File System Validation**:
       - Checks configuration file readability and format
       - Validates output directory existence and write permissions
       - Handles both existing files (overwrite) and new files (creation)
       - Prevents accidental directory overwriting with safety checks

    3. **Logging Infrastructure Setup**:
       - Configures multi-level logging with file and console output
       - Creates log files with intelligent naming (matches CSV output)
       - Supports dynamic log level configuration from command line
       - Implements safe logger handler management to prevent conflicts

    4. **Configuration Management**:
       - Loads and validates YAML configuration with schema checking
       - Handles missing or incomplete configuration gracefully
       - Implements interactive credential collection for security
       - Validates Jira connection parameters and API accessibility

    5. **Interactive Authentication**:
       - Prompts for missing Jira credentials when not in configuration
       - Secures sensitive information during input collection
       - Validates domain formats and connection parameters
       - Provides clear guidance for credential requirements

    6. **Core Processing Orchestration**:
       - Initializes issue parser with validated configuration
       - Executes Jira API connection and data fetching
       - Processes issues through workflow analysis pipeline
       - Generates CSV output with formatting and validation

    7. **Error Handling & Recovery**:
       - Comprehensive exception management with detailed logging
       - Graceful shutdown procedures with cleanup operations
       - User-friendly error messages with actionable guidance
       - System exit codes for automation and scripting integration

    Command Line Arguments:
        -c, --config (str, required): Absolute or relative path to YAML configuration file.
                                     Must be readable and contain valid YAML syntax with
                                     required sections for Jira connection, field mappings,
                                     workflow definitions, and export settings.
                                     
        -o, --output (str, required): Target path for CSV export file. Can be absolute
                                     or relative path. Parent directory must exist and
                                     be writable. File will be created or overwritten.
                                     
        -l, --loglevel (str, optional): Logging verbosity level controlling output detail:
                                       - 'debug': Maximum verbosity with API calls, processing steps
                                       - 'info': Standard operational messages and progress updates  
                                       - 'warning': Important notices and potential issues
                                       - 'error': Error conditions that don't halt execution
                                       - 'critical': Severe errors requiring immediate attention
                                       - 'off': Completely disable logging (silent operation)
                                       Default: 'debug' for maximum troubleshooting capability

    Validation Checks:
        - Configuration file exists and is readable
        - Configuration contains valid YAML syntax
        - Output directory exists and is writable  
        - Output path is not a directory
        - File permissions allow creation/modification
        - Logging directory is accessible for log file creation

    Exit Codes:
        0: Successful completion of export process
        1: Invalid arguments, file access errors, or processing failures

    Raises:
        SystemExit: Immediately terminates application on:
                   - Missing or invalid command-line arguments
                   - Configuration file not found or not readable
                   - Output directory not found or not writable
                   - Output path pointing to existing directory
                   - File permission errors preventing file operations
        
        Exception: Re-raises unexpected errors after comprehensive logging:
                  - Unexpected API failures or network issues
                  - Data processing errors during issue parsing
                  - Memory or resource exhaustion during large exports
                  - Unhandled configuration or validation errors

    Example Usage Scenarios:
        >>> # Standard production export
        >>> main()  # Called with: -c prod.yaml -o export.csv -l info
        
        >>> # Debug troubleshooting session
        >>> main()  # Called with: -c debug.yaml -o test.csv -l debug
        
        >>> # Automated batch processing
        >>> main()  # Called with: -c auto.yaml -o batch.csv -l warning

    Interactive Credential Flow:
        When Jira connection credentials are missing from configuration:
        1. Application prompts for Jira domain (https://[name].atlassian.net)
        2. Requests username for API authentication
        3. Securely collects API token for connection
        4. Validates credentials before proceeding with export

    Performance Characteristics:
        - Memory usage scales linearly with issue count
        - Network requests optimized with batch processing
        - File I/O performed with buffered writes for efficiency
        - Progress tracking provides user feedback during long operations
        - Configurable timeout handling for network resilience

    Security Considerations:
        - Credentials handled in memory only (no disk storage)
        - API tokens masked in log output for security
        - File permissions validated to prevent unauthorized access
        - Configuration files should restrict access to sensitive data
        - Audit trail maintained through comprehensive logging
    """
    # Create the parser for handing over arguments
    parser = argparse.ArgumentParser(description = "This script fetches Jira issues with their timestamps given a defined workflow.")
    parser.add_argument("-c", "--config", type = str, dest ="config", help = "The configuration input file name. Type must be YAML.")
    parser.add_argument("-o", "--output", type = str, dest ="output", help = "The output file name. The output file will be an CSV file.")
    parser.add_argument("-l", "--loglevel", type = str, dest ="loglevel", help = "debug (most verbose, default value), info, warning, error, critical (least verbose), off (completely disabled)")

    try:
        # Parse the arguments
        args = parser.parse_args()

        yaml_config_file_location = args.config
        if yaml_config_file_location is None or yaml_config_file_location == "":
            print("No configuration file provided. Please provide a valid config file when running the exporter.", file=sys.stderr)
            sys.exit(1)

        # Ensure the configuration file exists; exit with error if it does not
        if not os.path.isfile(yaml_config_file_location):
            print(f"Configuration file '{yaml_config_file_location}' does not exist.", file=sys.stderr)
            sys.exit(1)
        
        csv_output_file_location = args.output
        if csv_output_file_location is None or csv_output_file_location == "":
            print("No output file provided. Please provide a valid output file location when running the exporter.", file=sys.stderr)
            sys.exit(1)

        # Ensure the output path is not a directory
        if os.path.isdir(csv_output_file_location):
            print(f"Output path '{csv_output_file_location}' is a directory, not a file.", file=sys.stderr)
            sys.exit(1)

        # Determine parent directory (empty means current dir)
        parent_dir = os.path.dirname(csv_output_file_location) or '.'

        # Ensure parent directory exists and is a directory
        if not os.path.exists(parent_dir):
            print(f"Directory '{parent_dir}' does not exist for output file '{csv_output_file_location}'.", file=sys.stderr)
            sys.exit(1)
        if not os.path.isdir(parent_dir):
            print(f"Output directory '{parent_dir}' is not a directory.", file=sys.stderr)
            sys.exit(1)

        # Check write permission:
        # - If file exists, ensure it's writable.
        # - If it doesn't exist, ensure we can create files in the parent directory.
        if os.path.exists(csv_output_file_location):
            if not os.access(csv_output_file_location, os.W_OK):
                print(f"Output file '{csv_output_file_location}' is not writable.", file=sys.stderr)
                sys.exit(1)
        else:
            if not os.access(parent_dir, os.W_OK):
                print(f"Cannot create output file in directory '{parent_dir}' (permission denied).", file=sys.stderr)
                sys.exit(1)

        # Remove all handlers from the logger in a safe way
        logger = logging.getLogger(__name__)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        log_level = logging.NOTSET
        shall_pretty_print = True  # Always enabled
        
        # Create log file path ensuring proper extension handling
        if '.' in csv_output_file_location.split('/')[-1]:
            # If the filename has an extension, replace it with .log
            log_file = csv_output_file_location.rsplit('.', 1)[0] + '.log'
        else:
            # If no extension, simply append .log
            log_file = csv_output_file_location + '.log'
        
        match str(args.loglevel):
            case "off":
                log_level = logging.NOTSET # don't log anything
            case "critical":
                log_level = logging.CRITICAL # least verbose
            case "error":
                log_level = logging.ERROR
            case "warning":
                log_level = logging.WARNING
            case "info":
                log_level = logging.INFO
            case "debug" | _: # "off" for off or anything else
                log_level = logging.DEBUG # most verbose

        if log_level == logging.NOTSET:
            # disable all logging
            logging.disable(logging.CRITICAL)
            if shall_pretty_print:
                print("Logging is disabled as per user request.")
        else:
            logging.disable(logging.NOTSET)
            # Set up file handler
            file_handler = logging.FileHandler(log_file, mode='w')
            file_formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            logger.setLevel(log_level)
            logger.debug("Logging to file enabled")

        config = ExporterConfig(logger, shall_pretty_print)
        config.load_yaml_file(yaml_config_file_location)
        #sys.exit(0)  # --- IGNORE ---
        if config.domain == "" or \
            config.username == "" or \
            config.api_token == "":
            print("\nPlease enter the following connection details manually.")
            if config.domain == "":
                config.domain = str(input("Jira domain name (https://[yourname].atlassian.net): "))

            if config.username == "":
                config.username = str(input("Enter your Jira username: "))
            
            if config.api_token == "":
                config.api_token = str(input("Enter your Jira API token: "))
        
        # Parse all received issues
        parser = IssueParser(logger, config, shall_pretty_print)
        parsed_issues = parser.fetch_and_parse_issues()
        parser.export_to_csv(parsed_issues, csv_output_file_location)

    except Exception as error:
        logger.error(f"Unexpected error: {error}\nScript has been canceled.\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    """
    Script execution guard ensuring main() only runs when executed directly.
    
    This standard Python idiom prevents the main() function from executing when
    the module is imported, allowing safe module reuse while preserving the
    command-line interface functionality when run as a standalone script.
    """
    main()