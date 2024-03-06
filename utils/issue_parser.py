# coding: utf8

from jira import JIRA
import chardet
from .exporter_config import ExporterConfig

class IssueParser:
    def __init__(self, config:object):
        self._config = config
        self._jira = JIRA(config.get_domain(), basic_auth=(config.get_username(), config.get_api_token()))
        self._issues = []
        self._parsed_data = []


    def fetch_issues(self, jql_query:str="", max_results:int=0):
        # Execute JQL query
        if jql_query == "":
            jql_query = self._config.get_jql_query()
        if max_results == 0:
            max_results = self._config.get_max_results()
        
        self._issues = self._jira.search_issues(jql_query, maxResults=max_results)
        print(self._issues)


    def parse_issues(self) -> list:
        # Crawl all fetches issues
        for issue in self._issues:
            # Save some variables for later use
            issue_id = issue.id
            issue_status = issue.fields.status.name
            issue_creation_date = self._transform_date(issue.fields.created)
            # Get the default values of an issue that are available for each export
            issue_data = {
                "issueKey": issue.key,
                "issueID": issue_id,
                "issueType": issue.fields.issuetype.name,
                "Summary": self._parse_field_value(issue.fields.summary),
                "Status": issue_status,
                "Resolution": issue.fields.resolution,
                "Created": issue_creation_date,
                "Resolved": "" if len(str(issue.fields.resolutiondate)) > 0 else self._transform_date(issue.fields.resolutiondate),
                "Flagged": str(issue.fields.customfield_10021 is not None),
                "Labels": "" if len(issue.fields.labels) == 0 else "'" + "'|'".join([x for x in issue.fields.labels]) + "'", # empty string if there are no labels
            }

            # Get the values of the extra custom fields defined in the YAML file
            if self._config.has_custom_fields():
                for field_name in self._config.get_custom_fields().keys():
                    issue_data[field_name] = self._parse_field_value(eval("issue.fields." + self._config.get_custom_field_id(field_name)))

            if self._config.has_workflow():
                self._parse_status_category_timestamps(issue_id, issue_status, issue_creation_date)
            
            self._parsed_data.append(issue_data)

        return self._parsed_data


    def _parse_field_value(self, value) -> str:
        if value == None or str(value) == "":
            return ""
        
        return_string = ""

        if isinstance(value, float):
            match self._config.get_decimal_separator():
                case ExporterConfig.DECIMAL_SEPARATOR_COMMA:
                    return_string = str(value).replace(".", ",")
                case _: #ExporterConfig.DECIMAL_SEPARATOR_POINT
                    return_string = str(value).replace(",", ".")
        elif isinstance(value, int):
            return_string = str(value)
        elif isinstance(value, str):
            # Make sure that special chars are working (TODO: not working atm)
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


    def _parse_status_category_timestamps(self, issue_id, issue_status, issue_creation_date) -> dict:
        categories = {}
        # Initiate the status category timestamps by adding all of them with value None
        for status_category in self._config.get_status_categories():
            categories[status_category] = None
        
        # Set the issue's creation date as a guess for the initial status
        initial_category = self._config.get_status_category_from_status(issue_status)
        categories[initial_category] = issue_creation_date        

        # Crawl through all changelogs of an issue
        changelogs = self._jira.issue(issue_id, expand="changelog").changelog.histories
        for changelog in changelogs:
            # Crawl through all items of the changelog
            items = changelog.items
            for item in items:
                # Transitions are saved in the field status
                if item.field == "status":
                    # Get the date and strip all unnecessary timezone information
                    date = self._transform_date(changelog.created)
                    # Get the old and new status from Jira
                    origin_status = item.fromString
                    destination_status = item.toString
                    # Get the old and new status categories based on the given status
                    origin_category = self._config.get_status_category_from_status(origin_status)
                    destination_category = self._config.get_status_category_from_status(destination_status)
                    # Get the transition dates based on the categories
                    origin_transition_date = categories[origin_category]
                    destination_transition_date = categories[destination_category]
                    
                    # Only set a new timestamp when the category has changed
                    if origin_category is not None and origin_category != destination_category:
                        # Only set the timestamp for valid timestamps
                        if destination_status in self._config.get_status_category_mapping().keys():
                            if destination_transition_date is None or destination_transition_date < date:
                                categories[destination_category] = issue_creation_date # always set the creation date to the from status to get the info for the very first status
                                categories[destination_category] = date
                        else:
                            print(f"Invalid status: '{destination_status}'; Date: '{date}'")
        return categories


    def _transform_date(self, timestamp:str):
        return timestamp[0:10]