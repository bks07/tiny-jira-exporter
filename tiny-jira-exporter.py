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
        data: A mixed list holding the information for the CSV file.
        location: The string of the folder and file location of the CSV file.

    Returns:
        None.

    Raises:
        Exception: If there is an error while writing the file.
    """
    if location == None or location == "":
        location = DEFAULT_OUTPUT_FILE

    # Write data to csv file using the Pandas module
    try:
        df = pd.DataFrame.from_dict(data)
        df.to_csv(location, index=False, sep=";", encoding="latin-1")
    except Exception as e:
        raise Exception("Error writing CSV file:", e)
    
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
        yaml_config_file_location = args.config
        if yaml_config_file_location == None or yaml_config_file_location == "":
            yaml_config_file_location = DEFAULT_CONFIGURATION_FILE
        
        print("Process YAML config file...")
        config = ExporterConfig(yaml_config_file_location)
        print(" ... done.")

        if config.get_domain() == "" or \
            config.get_username() == "" or \
            config.get_api_token() == "":
            print("\nPlease enter the following  connection details manually.")
            if config.get_domain() == "":
                config.set_domain(input("Jira domain name (https://[yourname].atlassian.net): "))

            if config.get_username() == "":
                config.set_username(input("Enter your Jira username: "))
            
            if config.get_api_token() == "":
                config.set_api_token(input("Enter your Jira API token: "))

        
        # Parse all received issues
        print("\nFetch issues from Jira...")
        parser = IssueParser(config)
        parser.fetch_issues()
        print(" ... done.")

        print("\nParse fetched Jira issues...")
        output_data = parser.parse_issues()
        print(" ... done.")

        # Write output file
        print(f"\nWrite CSV output file to '{yaml_config_file_location}'.")
        write_csv_file(output_data, args.output)
        print(" ... done.")

    except Exception as error:
        print(f"Unexpected error: {error}")
    
    return None

if __name__ == "__main__":
    main()