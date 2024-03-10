# coding: utf8

from jira import JIRA
import math
import chardet
from .exporter_config import ExporterConfig

class IssueParser:
    def __init__(self, config:object):
        self._config = config
        self._jira = JIRA(config.get_domain(), basic_auth=(config.get_username(), config.get_api_token()))
        self._issues = []
        self._parsed_data = []


    def fetch_issues(self, jql_query:str="", max_results:int=0):
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """
        # Execute JQL query
        if jql_query == "":
            jql_query = self._config.get_jql_query()
        if max_results == 0:
            max_results = self._config.get_max_results()
        
        self._issues = self._jira.search_issues(jql_query, maxResults=max_results)


    def parse_issues(self) -> list:
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """

        number_of_issues = len(self._issues)
        i = 1
        # Crawl all fetches issues
        for issue in self._issues:
            # Save some variables for later use
            issue_id = self._parse_field_value(issue.id)
            issue_status = self._parse_field_value(issue.fields.status.name)
            issue_creation_date = self._parse_field_value(self._transform_date(issue.fields.created))
            issue_summary = self._parse_field_value(issue.fields.summary)
            issue_flagged = self._parse_flagged(eval("issue.fields." + self._config.get_field_id_flagged()))
            # Get the default values of an issue that are available for each export

            self._display_progress_bar(number_of_issues, i, issue_id, issue.key, issue_summary)
            
            issue_reporter_account_id = ""
            if issue.fields.reporter != None:
                issue_reporter_account_id = issue.fields.reporter.accountId

            issue_assignee_account_id = ""
            if issue.fields.assignee != None:
                issue_assignee_account_id = issue.fields.assignee.accountId

            issue_data = {
                "issueKey": self._parse_field_value(issue.key),
                "issueID": issue_id,
                "issueType": self._parse_field_value(issue.fields.issuetype.name),
                "Reporter": self._parse_field_value(issue.fields.reporter),
                "Reporter ID": self._parse_field_value(issue_reporter_account_id),
                "Assignee": self._parse_field_value(issue.fields.assignee),
                "Assignee ID": self._parse_field_value(issue_assignee_account_id),
                "Summary": issue_summary,
                "Status": issue_status,
                "Resolution": self._parse_field_value(issue.fields.resolution),
                "Created": issue_creation_date,
                "Resolved": self._parse_resolution_date(issue.fields.resolutiondate),
                "Flagged": issue_flagged,
                "Labels": self._parse_labels(issue.fields.labels)
            }
            
            # Get the values of the extra custom fields defined in the YAML file
            if self._config.has_custom_fields():
                for field_name in self._config.get_custom_fields().keys():
                    issue_data[self._parse_field_value(self._config.get_custom_field_prefix() + field_name)] = self._parse_field_value(eval("issue.fields." + self._config.get_custom_field_id(field_name)))

            if self._config.has_workflow():
                issue_data.update(self._parse_status_category_timestamps(issue_id, issue_status, issue_creation_date))
            
            i += 1
            self._parsed_data.append(issue_data)

        return self._parsed_data


    def _parse_field_value(self, value) -> str:
        """...
        In the end, there is a recursive call to ensure that all strings
        are transformed to latin-1, since this is the only character set
        that works when exporting the data to CSV.

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """
        if value == None or value == "":
            return ""
        
        return_string = ""

        if isinstance(value, str):
            # Make sure that special chars are working (TODO: not working atm)
            # Check if encoding was detected
            character_set = chardet.detect(value.encode())
            if character_set["encoding"]:
                encoded_string = value.encode(character_set["encoding"], errors="strict")
                return_string = encoded_string.decode("latin-1")
            else:
                raise Exception("Encoding detection for string failed.")

        elif isinstance(value, float):
            match self._config.get_decimal_separator():
                case ExporterConfig.DECIMAL_SEPARATOR_COMMA:
                    return_string = str(value).replace(".", ",")
                case _: # ExporterConfig.DECIMAL_SEPARATOR_POINT
                    return_string = str(value).replace(",", ".")
            # Ensure the right encoding
            return_string = self._parse_field_value(return_string)
        
        else:
            # Ensure the right encoding
            return_string = self._parse_field_value(str(value))
        
        return return_string


    def _parse_status_category_timestamps(self, issue_id, issue_status, issue_creation_date) -> dict:
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """
        categories = {}
        # Initiate the status category timestamps by adding all of them with value None
        for status_category in self._config.get_status_categories():
            categories[self._parse_field_value(status_category)] = None
        
        # Set the issue's creation date as a guess for the initial status
        initial_category = self._parse_field_value(self._config.get_status_category_from_status(issue_status))
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
                    date = self._parse_field_value(self._transform_date(changelog.created))
                    # Get the old and new status from Jira
                    origin_status = self._parse_field_value(item.fromString)
                    destination_status = self._parse_field_value(item.toString)
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
                                categories[self._parse_field_value(destination_category)] = issue_creation_date # always set the creation date to the from status to get the info for the very first status
                                categories[self._parse_field_value(destination_category)] = date
                        else:
                            raise ValueError(f"Invalid status: '{destination_status}'; Date: '{date}'")
                        
        return categories


    def _transform_date(self, timestamp:str):
        """TODO: Must be implemented.

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """
        #import pytz
        #if timezone_str in pytz.all_timezones:
        #    ...
        #else:
        #    raise ValueError("Invalid timezone string!")
        return timestamp[0:10]
    

    def _parse_labels(self, labels:list):
        return_string = ""
        if len(labels) > 0:
           return_string = "'" + "'|'".join([x for x in labels]) + "'"
        return self._parse_field_value(return_string)


    def _parse_resolution_date(self, date):
        return_string = ""
        if date != None and len(str(date)) > 0:
            return_string = date
        return self._parse_field_value(self._transform_date(return_string))

        
    def _parse_flagged(self, value):
        return self._parse_field_value(str(value is not None))


    def _display_progress_bar(self, number_of_issues:int, iterator:int, issue_id:str, issue_key:str, issue_summary:str):
        percentage = math.ceil(iterator/number_of_issues*100)

        progress_bar_length = 10
        
        length_done = int(percentage / 10)
        length_todo = progress_bar_length - length_done

        progress_bar_done = "#" * length_done
        progress_bar_todo = " " * length_todo

        progress_bar = "[" + progress_bar_done + progress_bar_todo + "]"
        
        end_of_print = "\r"
        if percentage == 100:
            end_of_print = "\n"
        
        print(f" {progress_bar} {iterator}/{number_of_issues} ({percentage}%) {issue_key} ({issue_id}): {issue_summary}", end=end_of_print)
        if percentage < 100:
            print("\033[2K", end="") # Clear entire line