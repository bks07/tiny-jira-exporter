# coding: utf8

# Import all required modules
import sys
import argparse
import yaml
import pandas as pd
import chardet
# Import the JIRA library from https://jira.readthedocs.io/
from jira import JIRA

DEFAULT_CONFIGURATION_FILE = "./conf/default.yaml"
DEFAULT_OUTPUT_FILE = "./exports/default.csv"
DECIMAL_SEPARATOR_POINT = "Point"
DECIMAL_SEPARATOR_COMMA = "Comma"

def parse_yaml_file(file_location:str=None) -> dict:
    if file_location == None or file_location == "":
        file_location = DEFAULT_CONFIGURATION_FILE

    # Open the YAML file in read mode
    with open(file_location, "r") as file:
        # Parse the contents using safe_load()
        data = yaml.safe_load(file)
    
    config_data = {}
    # Set up the Jira access data
    config_data["domain"] = data["Connection"]["Domain"]
    if "Username" in data["Connection"]:
        config_data["username"] = data["Connection"]["Username"]
    else:
        # If not defined in YAML file, prompt for username
        config["username"] = input("Enter your Jira username: ")
    
    if "API Token" in data["Connection"]:
        config_data["api_token"] = data["Connection"]["API Token"]
    else:
        # If not defined in YAML file, prompt for API token
        config["api_token"] = input("Enter your Jira API token: ")

    # Set up the JQL query to retrieve the right issues
    if "Projects" in data["Search Criteria"] and len(data["Search Criteria"]["Projects"]) > 0:
        # Creates a default JQL query like "project IN(PKEY1, PKEY2) ORDER BY issuekey ASC
        jql_query = "project IN("
        for project_key in data["Search Criteria"]["Projects"]:
            jql_query += project_key + ", "
        jql_query = jql_query[:-2]
        if "Issue Types" in data["Search Criteria"] and len(data["Search Criteria"]["Issue Types"]) > 0:
            jql_query += " AND issuetype IN("
            for issue_type in data["Search Criteria"]["Issue Types"]:
                jql_query += issue_type + ", "
            jql_query = jql_query[:-2]
        jql_query += ") ORDER BY issuekey ASC"
    elif "Filter" in data["Search Criteria"]:
        # Creates a query where it selects the given filter
        jql_query = "filter = '" + data["Search Criteria"]["Filter"] + "'"
        if "Issue Types" in data["Search Criteria"] and len(data["Search Criteria"]["Issue Types"]) > 0:
            jql_query += " AND issuetype IN("
            for issue_type in data["Search Criteria"]["Issue Types"]:
                jql_query += issue_type + ", "
            jql_query = jql_query[:-2] + ")"
    else:
        raise ValueError("No project key or filter defined in YAML configuration file.")
    config_data["jql_query"] = jql_query

    # Set up the defined issue types
    config_data["issue_types"] = []
    if "Issue Types" in data["Search Criteria"]:
        for issue_type in data["Search Criteria"]["Issue Types"]:
            config_data["issue_types"].append(issue_type)

    # Define the maximum search results
    config_data["max_results"] = 100
    if "Max Results" in data["Search Criteria"]:
        config_data["max_results"] = data["Search Criteria"]["Max Results"]

    # Set up all workflow-related information
    config_data["status_categories"] = []
    config_data["status_category_mapping"] = {}
    for status_category in data["Workflow"]:
        config_data["status_categories"].append(status_category)
        for status in data["Workflow"][status_category]:
            config_data["status_category_mapping"][status] = status_category

    # Set up all defined custom fields
    config_data["custom_fields"] = {}
    if "Custom Fields" in data:
        config_data["custom_fields"] = data["Custom Fields"]

    config_data["decimal_separator"] = data["Misc"]["Decimal Separator"]

    return config_data


def parse_issues(jira:object, issues:dict, status_categories:list, status_category_mapping:dict, custom_fields:list, decimal_separator) -> list:
    # A dictionary to store all issue-related information
    data = []

    # Crawl all fetches issues
    for issue in issues:
        # Save some variables for later use
        issue_id = issue.id
        issue_status = issue.fields.status.name
        issue_creation_date = issue.fields.created[0:10]

        # Get the default values of an issue that are available for each export
        issue_data = {
            "issueKey": issue.key,
            "issueID": issue_id,
            "issueType": issue.fields.issuetype.name,
            "Summary": parse_field_value(issue.fields.summary),
            "Status": issue_status,
            "Resolution": issue.fields.resolution,
            "Created": issue_creation_date,
            "Resolved": "" if len(str(issue.fields.resolutiondate)) > 0 else str(issue.fields.resolutiondate)[0:10],
            "Flagged": str(issue.fields.customfield_10021 is not None),
            "Labels": "" if len(issue.fields.labels) == 0 else "'" + "'|'".join([x for x in issue.fields.labels]) + "'", # empty string if there are no labels
        }

        # Get the values of the extra custom fields defined in the YAML file
        for field_name in custom_fields.keys():
            issue_data[field_name] = parse_field_value(eval("issue.fields." + custom_fields[field_name]), decimal_separator)

        # Initiate the status category timestamps by adding all of them with value None
        for status_category in status_categories:
            issue_data[status_category] = None
        
        # Set the issue's creation date as a guess for the initial status
        initial_category = status_category_mapping[issue_status]
        issue_data[initial_category] = issue_creation_date        

        # Crawl through all changelogs of an issue
        changelogs = jira.issue(issue_id, expand="changelog").changelog.histories
        for changelog in changelogs:
            # Get the date and strip all unnecessary timezone information
            date = changelog.created[0:10]

            # Crawl through all items of the changelog
            items = changelog.items
            for item in items:
                # Transitions are saved in the field status
                if item.field == "status":
                    # Get the old and new status from Jira
                    origin_status = item.fromString
                    destination_status = item.toString
                    # Get the old and new status categories based on the given status
                    origin_category = status_category_mapping[origin_status]
                    destination_category = status_category_mapping[destination_status]
                    # Get the transition dates based on the categories
                    origin_transition_date = issue_data[origin_category]
                    destination_transition_date = issue_data[destination_category]
                    
                    # Only set a new timestamp when the category has changed
                    if origin_category is not None and origin_category != destination_category:
                        # Only set the timestamp for valid timestamps
                        if destination_status in status_category_mapping.keys():
                            if destination_transition_date is None or destination_transition_date < date:
                                issue_data[destination_category] = issue_creation_date # always set the creation date to the from status to get the info for the very first status
                                issue_data[destination_category] = date
                                #print(f" - Transition from '{origin_status}' to '{destination_status}' at '{date}'.")
                        else:
                            print(f"Invalid status: '{destination_status}'; Date: '{date}'")
        
        data.append(issue_data)

    return data


def parse_field_value(value, decimal_separator:str=DECIMAL_SEPARATOR_COMMA) -> str:
    if value == None or str(value) == "":
        return ""
    
    return_string = ""

    if isinstance(value, float):
        if decimal_separator == DECIMAL_SEPARATOR_COMMA:
            return_string = str(value).replace(".", ",")
        elif decimal_separator == DECIMAL_SEPARATOR_POINT:
            return_string = str(value).replace(".", ",")
    elif isinstance(value, int):
        return_string = str(value)
    elif isinstance(value, str):
        # Make sure that special chars are working (not working atm)
        # Check if encoding was detected
        character_set = chardet.detect(value.encode())
        if character_set["encoding"]:
            match character_set["encoding"]:
                case "ascii":
                    encoded_string = value.encode(character_set["encoding"], errors="strict")
                    return_string = encoded_string.decode("utf-8")
                case _:
                    #return_string = bytes(value,character_set["encoding"]).decode("utf-8") # doesn't work
                    #encoded_string = str(value).encode(character_set["encoding"], errors="strict") # doesn't work
                    return_string = value
        else:
            raise Exception("Encoding detection for string failed.")

    return return_string


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

    # Erstellen Sie einen Pandas-Datenrahmen aus der Datenliste
    df = pd.DataFrame.from_dict(data)

    # Exportieren Sie den Datenrahmen in eine CSV-Datei
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
        config = parse_yaml_file(args.config)

        # Connect to Jira Cloud
        jira = JIRA(config["domain"], basic_auth=(config["username"], config["api_token"]))
        
        # Execute JQL query
        issues = jira.search_issues(config["jql_query"], maxResults=config["max_results"])
        
        # Parse all received issues
        output_data = parse_issues(jira, issues, config["status_categories"], config["status_category_mapping"], config["custom_fields"], config["decimal_separator"])
        
        # Write output file
        write_csv_file(output_data, args.output)
    except Exception as error:
        print(f"Unexpected error: {error}")
    
    return None

if __name__ == "__main__":
    main()