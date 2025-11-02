#!/usr/bin/env python3
# coding: utf8

import sys
import os
# Add the project root directory to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(project_root)

import json
import logging
from argparse import ArgumentParser
from dotenv import load_dotenv

from modules.exporter_config.exporter_config import ExporterConfig

# Load environment variables from .env file
load_dotenv()

"""
Script to fetch test data using configuration from the exporter_config module.

This script loads a YAML configuration file, validates it, and uses it to fetch
test data. The configuration is managed by the `ExporterConfig` class.
"""

def main():
    """
    Main function to load and display configuration from a YAML file.

    This function parses command-line arguments or environment variables to locate
    the configuration file, loads the configuration, and performs basic operations
    like saving and loading a JSON object.

    :raises SystemExit: If the configuration file is not found.
    :return: The loaded configuration object.
    :rtype: ExporterConfig
    """
    parser = ArgumentParser(description='Generate config for test data fetching.')
    parser.add_argument('-c', '--config', help='Configuration YAML file path')
    
    args = parser.parse_args()
    
    logger = logging.getLogger(__name__)

    # Use environment variable CONFIG_FILE_PATH, fallback to command-line argument if not set
    config_path = os.getenv('CONFIG_FILE_PATH') or args.config
    
    if not config_path:
        logger.error("No configuration file specified. Use -c/--config or set CONFIG_FILE_PATH environment variable.")
        sys.exit(1)
    
    print(f"Using configuration file: {config_path}")
    if not os.path.exists(config_path):
        logger.error(f"Error: Configuration file not found at {config_path}")
        sys.exit(1)
    
    # Load configuration using exporter_config module
    logger.info(f"Using configuration file: {config_path}")
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found at {config_path}")
        sys.exit(1)
    
    config = ExporterConfig(config_path, logger, False)

    # Save object to file
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'tests', 'test_data', 'json'
    )
    output_path = os.path.join(output_dir, 'config.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=2, default=str, ensure_ascii=False)
    logger.info(f"Configuration saved to {output_path}")


if __name__ == "__main__":
    config = main()