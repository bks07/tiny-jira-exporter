# coding: utf8

import argparse
import pandas as pd
from utils.issue_parser import IssueParser
from utils.exporter_config import ExporterConfig

DEFAULT_CONFIGURATION_FILE = "./conf/default.yaml"
DEFAULT_OUTPUT_FILE = "./exports/default.csv"

def write_csv_file(data:list, location:str=""):
    """Writes the output CSV file to the specified location.

    Args:
        data: A mixed list of integers.
        location: The string of the folder location where to store the CSV file.

    Returns:
        None.

    Raises:
        ValueError: If the list is empty.
    """
    if location == None or location == "":
        location = DEFAULT_OUTPUT_FILE

    # Write data to csv file using the Pandas module
    df = pd.DataFrame.from_dict(data)
    if not df.to_csv(location, index=False):
        raise Exception("Couldn't write output CSV file.")
    else:
        print("CSV file created successfully!")
    
    return None


def main():
    # Create the parser for handing over arguments
    parser = argparse.ArgumentParser(description="This script fetches Jira issues with their timestamps given a defined workflow.")
    parser.add_argument("-c", "--config", type=str, dest="config", help="The configuration input file name. Type must be YAML.")
    parser.add_argument("-o", "--output", type=str, dest="output", help="The output file name. The output file will be an CSV file.")
    parser.add_argument("-v", "--verbose", dest="verbose", help="")
    # Parse the arguments
    args = parser.parse_args()

    try:
        config_file_location = args.config
        if config_file_location == None or config_file_location == "":
            config_file_location = DEFAULT_CONFIGURATION_FILE
        
        config = ExporterConfig(config_file_location)

        if config.get_domain() == "":
            config.set_domain(input("Enter your Jira domain name (https://[yourname].atlassian.net): "))

        if config.get_username() == "":
            config.set_username(input("Enter your Jira username: "))
        
        if config.get_api_token() == "":
            config.set_api_token(input("Enter your Jira API token: "))

        # Parse all received issues
        parser = IssueParser(config)
        parser.fetch_issues()
        output_data = parser.parse_issues()
        
        # Write output file
        write_csv_file(output_data, args.output)
    except Exception as error:
        print(f"Unexpected error: {error}")
    
    return None

if __name__ == "__main__":
    main()