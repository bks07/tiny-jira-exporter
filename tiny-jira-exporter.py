# coding: utf8

import argparse
import logging
import traceback

from packages.issue_parser.issue_parser import IssueParser
from packages.exporter_config.exporter_config import ExporterConfig

DEFAULT_CONFIGURATION_FILE = "./conf/default.yaml"
DEFAULT_OUTPUT_FILE = "./exports/default.csv"
DISABLE_LOGGING = -1

def main():
    # Create the parser for handing over arguments
    parser = argparse.ArgumentParser(description = "This script fetches Jira issues with their timestamps given a defined workflow.")
    parser.add_argument("-c", "--config", type = str, dest ="config", help = "The configuration input file name. Type must be YAML.")
    parser.add_argument("-o", "--output", type = str, dest ="output", help = "The output file name. The output file will be an CSV file.")
    parser.add_argument("-l", "--loglevel", type = str, dest ="loglevel", help = "d := Debug (most verbose), i := Info, w := Warning, e := Error, c := Critical (least verbose), o := Off (completely disabled)")

    try:
        # Parse the arguments
        args = parser.parse_args()

        yaml_config_file_location = args.config
        if yaml_config_file_location == None or yaml_config_file_location == "":
            yaml_config_file_location = DEFAULT_CONFIGURATION_FILE
        
        csv_output_file_location = args.output
        if csv_output_file_location == None or csv_output_file_location == "":
            csv_output_file_location = DEFAULT_OUTPUT_FILE

        logging.basicConfig()
        logger = logging.getLogger(__name__)
        
        # Remove all existing default handlers
        logger.handlers = []
        
        log_level = DISABLE_LOGGING
        match str(args.loglevel):
                case "d":
                    log_level = logging.DEBUG # most verbose
                case "i":
                    log_level = logging.INFO
                case "w":
                    log_level = logging.WARNING
                case "e":
                    log_level = logging.ERROR
                case "c":
                    log_level = logging.CRITICAL # least verbose
                case _: # "o" for off or anything else
                    log_level = DISABLE_LOGGING # don't log anything

        if log_level == DISABLE_LOGGING:
            logger.addHandler(logging.NullHandler())
            logger.setLevel(logging.CRITICAL)
        else:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
            console_handler.setFormatter(formatter)
            #logger.addHandler(console_handler)
            logger.setLevel(log_level)


        config = ExporterConfig(yaml_config_file_location, logger, True)
        
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
        parser = IssueParser(config, logger, True)
        parser.fetch_issues()
        parser.parse_issues()
        parser.export_to_csv(csv_output_file_location)

    except Exception as error:
        logger.debug(f"Unexpected error: {error}\nScript has been canceled.\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()