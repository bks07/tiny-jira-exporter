#!/usr/bin/env python3
# coding: utf8

"""
Tiny Jira Exporter - Main entry point for Jira issue data export.

This module provides a command-line interface for extracting Jira issues and
their associated workflow data into CSV format. It handles configuration loading,
argument parsing, logging setup, and orchestrates the complete export process
from Jira API connection to CSV file generation.

The exporter supports:
- JQL-based issue filtering
- Custom field extraction
- Workflow analysis with time-in-status calculations
- Configurable output formatting
- Comprehensive logging and error handling

Usage:
    python main.py -c config.yaml -o output.csv -l debug

Example:
    python main.py --config conf/default.yaml --output export/issues.csv --loglevel info
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
    Main entry point for the Tiny Jira Exporter application.

    Handles command-line argument parsing, configuration validation, logging setup,
    and orchestrates the complete Jira export workflow. Validates input parameters,
    establishes file permissions, configures logging levels, loads YAML configuration,
    prompts for missing credentials, and executes the issue parsing and CSV export process.

    The function performs comprehensive error handling and validation:
    - Validates configuration file existence and readability
    - Checks output directory permissions and writability
    - Sets up appropriate logging levels and file handlers
    - Handles missing Jira connection credentials interactively
    - Manages all exceptions with proper error reporting and cleanup

    Command Line Arguments:
        -c, --config: Path to YAML configuration file (required)
        -o, --output: Path to output CSV file (required)
        -l, --loglevel: Logging verbosity level (debug, info, warning, error, critical, off)

    Raises:
        SystemExit: On invalid arguments, missing files, or permission errors.
        Exception: Re-raises any unexpected errors after logging for debugging.
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
    main()