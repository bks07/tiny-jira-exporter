# coding: utf8

import math
import chardet
#from jira import JIRA
from atlassian import Jira
import pandas as pd

from modules.exporter_config.exporter_config import ExporterConfig
from modules.exporter_config.issue_field import IssueField
from modules.exporter_config.standard_issue_field import StandardIssueField
from modules.exporter_config.custom_issue_field import CustomIssueField

class IssueParser:
    """
    Connects to Jira and fetches the issues directly from Jira using a JQL query.

    :param config: The configuration originating from the YAML configuration file
    :type config: (object)ExporterConfig
    :param logger: The logger for debugging purposes
    :type logger: object
    """
    def __init__(
        self,
        config: ExporterConfig,
        logger: object,
        pretty_print: bool = False
    ):
        self.__config: ExporterConfig = config
        self.__logger: object = logger
        self.__jira: Jira = Jira(
            url = config.domain,
            username = config.username,
            password = config.api_token,
            cloud = True)
        self.__issues: list = []
        self.__parsed_data: list = []
        self.__shall_pretty_print: bool = pretty_print


    ######################
    ### PUBLIC METHODS ###
    ######################


    def fetch_issues(
        self
    ) -> None:
        """
        Connects to Jira and fetches the issues directly from Jira using a JQL query.
        Uses the configuration to access all required login credentials.

        :raise ValueError: On Jira error when JQL failed.

        :return: None
        """
        # Execute JQL query
        self.__logger.debug("Starting to fetch issues from Jira.")

        if self.__shall_pretty_print:
            print("\nFetch issues from Jira...")
        
        try:
            start_at:int = 0
            batch_size:int = 50
            remaining_max_results:int = self.__config.max_results
            # Jira API returns pages with 100 issues per page max
            # That's why we need to use a loop to fetch several pages
            while remaining_max_results > 0:
                self.__logger.debug(f"Fetch first batch starting from {start_at} with batch size {batch_size}. Remaining max results: {remaining_max_results}.")
                
                # Only fetch as much as previously defined
                if batch_size > remaining_max_results:
                    batch_size = remaining_max_results
                
                # Call Jira to fetch issues
                self.__issues = self.__jira.jql(self.__config.jql_query)
                print(self.__issues)
                
                # Stop fetching when there are no more issues to fetch
                if len(self.__issues) < batch_size:
                    break

                start_at += batch_size
                remaining_max_results -= batch_size

        except Exception as e:
            self.__logger.critical(f"Jira request failed with JQL: {self.__config.jql_query} (Original message: {e})")
            raise ValueError(f"Jira request failed with JQL: {self.__config.jql_query}")
        
        if self.__shall_pretty_print:
            print(" ... done.")
        
        self.__logger.info(f"Issues successfully fetched: {len(self.__issues)}")


    def parse_issues(self) -> None:
        """
        Parses all issues that have been fetched previously to extract all information
        that will be written to the CSV output file.

        :return: None
        """
        self.__logger.debug("Starting to parse issues.")

        if self.__shall_pretty_print:
            print("\nParse fetched Jira issues...")

        number_of_issues = len(self.__issues)
        # Crawl all fetches issues
        for i in range(number_of_issues):
            issue = self.__issues[i]
            # Save some variables for later use
            issue_key = self.__parse_field_value(issue.key)
            issue_id = self.__parse_field_value(issue.id)

            self.__logger.debug(f"Start parsing issue {issue_key} ({issue_id}).")

            issue_summary = self.__parse_field_value(issue.fields.summary)

            # Get the default values of an issue that are available for each export
            issue_creation_date = self.__parse_field_value(self.__transform_date(issue.fields.created))

            if self.__shall_pretty_print:
                self.__display_progress_bar(number_of_issues, i, issue_id, issue_key, issue_summary)

            issue_data = {}
            
            for field in self.__config.issue_fields.values():
                if not field.shall_export_to_csv:
                    continue
                
                custom_field_column_name = self.__config.custom_field_prefix + field.name
                standard_field_column_name = self.__config.standard_field_prefix + field.name

                if isinstance(field, CustomIssueField):
                    
                    match field.name:
                        case ExporterConfig.ISSUE_FIELD_NAME__FLAGGED:
                            # Considered being a standard field
                            issue_data[standard_field_column_name] = self.__parse_field_flagged(eval("issue.fields." + field.id))
                        case _:
                            issue_data[custom_field_column_name] = self.__parse_field_value(eval("issue.fields." + field.id))

                elif isinstance(field, StandardIssueField):
                    

                    match field.name:
                        case ExporterConfig.ISSUE_FIELD_NAME__ISSUE_KEY:
                            # No prefix for this column
                            issue_data[field.name] = issue_key

                        case ExporterConfig.ISSUE_FIELD_NAME__ISSUE_ID:
                            # No prefix for this column
                            issue_data[field.name] = issue_id

                        case ExporterConfig.ISSUE_FIELD_NAME__ISSUE_TYPE:
                            issue_data[standard_field_column_name] = self.__parse_field_value(issue.fields.issuetype.name)

                        case ExporterConfig.ISSUE_FIELD_NAME__REPORTER:
                            issue_reporter_account_id = ""
                            if issue.fields.reporter != None:
                                issue_reporter_account_id = issue.fields.reporter.accountId
                            issue_data[standard_field_column_name] = self.__parse_field_value(issue.fields.reporter)
                            issue_data[standard_field_column_name + " ID"] = self.__parse_field_value(issue_reporter_account_id)

                        case ExporterConfig.ISSUE_FIELD_NAME__ASSIGNEE:
                            issue_assignee_account_id = ""
                            if issue.fields.assignee != None:
                                issue_assignee_account_id = issue.fields.assignee.accountId
                            issue_data[standard_field_column_name] = self.__parse_field_value(issue.fields.assignee)
                            issue_data[standard_field_column_name + " ID"] = self.__parse_field_value(issue_assignee_account_id)

                        case ExporterConfig.ISSUE_FIELD_NAME__SUMMARY:
                            issue_data[standard_field_column_name] = issue_summary

                        case ExporterConfig.ISSUE_FIELD_NAME__STATUS:
                            issue_data[standard_field_column_name] = self.__parse_field_value(issue.fields.status.name)

                        case ExporterConfig.ISSUE_FIELD_NAME__RESOLUTION:
                            issue_data[standard_field_column_name] = self.__parse_field_value(issue.fields.resolution)

                        case ExporterConfig.ISSUE_FIELD_NAME__PRIORITY:
                            issue_data[standard_field_column_name] = self.__parse_field_value(issue.fields.priority)

                        case ExporterConfig.ISSUE_FIELD_NAME__CREATED:
                            issue_data[standard_field_column_name] = issue_creation_date
                        
                        case ExporterConfig.ISSUE_FIELD_NAME__UPDATED:
                            issue_data[standard_field_column_name] = self.__parse_field_value(self.__transform_date(issue.fields.updated))

                        case ExporterConfig.ISSUE_FIELD_NAME__RESOLVED:
                            issue_data[standard_field_column_name] = self.__parse_field_optional_date(issue.fields.resolutiondate)

                        case ExporterConfig.ISSUE_FIELD_NAME__PARENT:
                            if hasattr(issue.fields, "parent") and issue.fields.parent is not None:
                                issue_data[standard_field_column_name] = self.__parse_field_value(issue.fields.parent.key)

                        case ExporterConfig.ISSUE_FIELD_NAME__LABELS:
                            issue_data[standard_field_column_name] = self.__parse_field_labels(issue.fields.labels)

                        case ExporterConfig.ISSUE_FIELD_NAME__DUE_DATE:
                            issue_data[standard_field_column_name] = self.__parse_field_optional_date(issue.fields.duedate)

                        case ExporterConfig.ISSUE_FIELD_NAME__COMPONENTS:
                            issue_data[standard_field_column_name] = self.__parse_versions(issue.fields.components) # The component field is similar to a version field 
                        
                        case ExporterConfig.ISSUE_FIELD_NAME__FIXED_VERSIONS:
                            issue_data[standard_field_column_name] = self.__parse_versions(issue.fields.fixVersions)

                        case ExporterConfig.ISSUE_FIELD_NAME__AFFECTED_VERSIONS:
                            issue_data[standard_field_column_name] = self.__parse_versions(issue.fields.versions)
                    
            if self.__config.has_workflow:
                issue_data.update(self.__parse_status_category_timestamps(issue_id, issue_creation_date))
            
            self.__parsed_data.append(issue_data)
        
        if self.__shall_pretty_print:
            print(" ... done.")
        
        self.__logger.debug("All issues parsed.")


    def export_to_csv(
        self,
        file_location: str
    ) -> None:
        """
        Exports the parsed data to a CSV file at a given location.

        :param file_location: The full path to the CSV file including the file
        :type file_location: str

        :return: None
        """
        self.__logger.debug("Write CSV file.")

        if self.__shall_pretty_print:
            print(f"\nWrite CSV output file to '{file_location}'.")
        
        try:
            df = pd.DataFrame.from_dict(self.__parsed_data)
            df.to_csv(file_location, index=False, sep=";", encoding="latin-1")
            
            if self.__shall_pretty_print:
                print(" ... done.")
            
            self.__logger.debug("CSV file successfully written.")
        except Exception as error:
            self.__logger.critical(error)


    ############################
    ### PARSE SPECIAL FIELDS ###
    ############################


    def __parse_field_labels(
        self,
        labels: list
    ):
        """
        Parses the list of labels and returns it as a string that
        can be used inside the CSV output file.

        :param labels: The list of labels
        :type labels: list

        :return: All labels in a string, separated by a tube | and enclosed in single quotation makrs '.
        :rtype: str
        """
        return_string = ""
        if len(labels) > 0:
           return_string = "'" + "'|'".join([x for x in labels]) + "'"
        return self.__parse_field_value(return_string)
        

    def __parse_versions(
        self,
        versions: list
    ):
        """
        Parses the list of labels and returns it as a string that
        can be used inside the CSV output file.

        :param versions: The list of versions
        :type labels: list[Version]

        :return: All labels in a string, separated by a tube | and enclosed in single quotation makrs '.
        :rtype: str
        """
        return_string = ""

        if len(versions) > 0:
            return_string = "'"
            for version in versions:
                return_string +=  version.name + "'|'"
            return_string = return_string[:-2]
        return self.__parse_field_value(return_string)
    

    def __parse_field_optional_date(
        self,
        date: str
    ) -> str:
        """
        Checks if the date is set. If so, returns it in an appropriate format.

        :param date: The list of labels
        :type date: str

        :return: Returns a proper formatted date string or an empty sting.
        :rtype: str
        """
        return_string = ""
        if date != None and len(str(date)) > 0:
            return_string = date
        return self.__parse_field_value(self.__transform_date(return_string))

        
    def __parse_field_flagged(
        self,
        value
    ) -> str:
        """
        Checks if the resolution date is set.

        :param value: Either an object (if flag is set) or None (if unflagged).
        :type value: Any

        :return: 'False' or 'True' as string
        :rtype: str
        """
        return value is not None


    ######################
    ### PARSE WORKFLOW ###
    ######################


    def __parse_status_category_timestamps(
        self,
        issue_id: int,
        issue_creation_date: str
    ) -> dict:
        """
        Parses a given workflow defintion and returns the timestamps
        for each category based on status transitions.

        :param issue_id: The id of an issue
        :type issue_id: int
        :param issue_creation_date: The first category will always be set to the creation date of the issue
        :type issue_creation_date: str

        :return: The list of catogies with the timestamp ("category: YYYY-MM-DD")
        :rtype: dict
        """
        categories = {}
        transitions = []
        is_first_category = True
        # Initiate the status category timestamps by adding all of them with value None
        for status_category in self.__config.workflow.categories:
            column_name: str = self.__config.status_category_prefix + status_category
            if is_first_category:
                # Every issue gets created with the very first status of the workflow
                # Therefore, set the creation date for the very first category
                categories[column_name] = issue_creation_date
                is_first_category = False
            else:
                categories[column_name] = None

        # Crawl through all changelogs of an issue
        changelogs = self.__jira.issue(issue_id, expand="changelog").changelog.histories
        for changelog in changelogs:
            # Crawl through all items of the changelog
            items = changelog.items
            for item in items:
                # Transitions are saved in the field status
                if item.field == "status":                    
                    # Add the transition information to a list first
                    # since it is returned in descending sort order
                    changelog_date = self.__transform_date(changelog.created)
                    transitions.append([item.fromString, item.toString, changelog_date])
        
        # Go through the transitions in reversed sort order
        # so that we start with the first transition
        for transition in reversed(transitions):
            categories = self.__set_transition_dates(categories, transition[0], transition[1], transition[2])

        return categories


    def __set_transition_dates(
        self,
        category_dates: dict,
        start_status: str,
        destination_status: str,
        date: str
    ) -> dict:
        """
        Sets the transition dates for categories based on the date of the
        history event and the start status to the destination status.
        Also recognizes when an issue has moved backwards in the workflow.
        Since this is a strict Kanban-oriented logic, the script will erase all
        timestamps once an issue has been moved back.

        :param category_dates: The dictionary with the timestamps so far
        :type category_dates: dict
        :param start_status: The status the issue was before it got transitioned
        :type start_status: str
        :param destination_status: The status the issue got transitioned to
        :type destination_status: str
        :param date: The date of the history event (when the transition happened)
        :type date: str

        :return: The updated transition categories
        :rtype: dict
        """
        category_start_status = self.__config.workflow.category_of_status(start_status)
        category_destination_status = self.__config.workflow.category_of_status(destination_status)

        position_start_status = self.__config.workflow.index_of_status(start_status)
        position_destination_status = self.__config.workflow.index_of_status(destination_status)

        category_start_status_index = self.__config.workflow.index_of_category(category_start_status)
        category_destination_status_index = self.__config.workflow.index_of_category(category_destination_status)

        self.__logger.debug(f"Transition on {date}: {position_start_status}:{start_status}({category_start_status}) -> {position_destination_status}:{destination_status}({category_destination_status})")
        # Nothing to do here, this date had already been written
        # since there is no change to the category
        if category_start_status_index == category_destination_status_index:
            self.__logger.debug(f"Same category, no dates to set.")
            return category_dates
        # The normal case, where the issue has been moved forward
        elif category_start_status_index < category_destination_status_index:
            for category_index in range(category_start_status_index, category_destination_status_index):
                self.__logger.debug(f"Set date {date} for category: {category_index+1}")
                column_name: str = self.__config.status_category_prefix + self.__config.workflow.categories[category_index+1]
                category_dates[column_name] = date
        # The case, when an issue has moved backward to a previous category
        else:
            for category_index in range(category_destination_status_index, category_start_status_index):
                self.__logger.debug(f"Unset date for category: {category_index+1}")
                column_name: str = self.__config.status_category_prefix + self.__config.workflow.categories[category_index+1]
                category_dates[column_name] = None

        return category_dates


    #######################
    ### SUPPORT METHODS ###
    #######################


    def __parse_field_value(
        self,
        value
    ) -> str:
        """...
        In the end, there is a recursive call to ensure that all strings
        are transformed to latin-1, since this is the only character set
        that works when exporting the data to CSV.

        :param value: The value of the issue field
        :type value: any

        :raise Exception: If the encoding of a string failed

        :return: The parsed field value
        :rtype: str
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
            match self.__config.decimal_separator:
                case ExporterConfig.DECIMAL_SEPARATOR_COMMA:
                    return_string = str(value).replace(".", ",")
                case _: # ExporterConfig.DECIMAL_SEPARATOR_POINT
                    return_string = str(value).replace(",", ".")
            # Ensure the right encoding
            return_string = self.__parse_field_value(return_string)
        
        else:
            # Ensure the right encoding
            return_string = self.__parse_field_value(str(value))
        
        return return_string


    def __transform_date(
        self,
        timestamp:str
    ) -> str:
        """
        A simple helper method that strips the all time information from a date filed (datetime to date only).
        TODO: Must be implemented to support user configured date formats as well as matching the correct time zone.

        :param timestamp: A timestamp that contains a date like YYYY-MM-DD
        :type timestamp: str

        :return: The date only following YYYY-MM-DD
        :rtype: str
        """
        #import pytz
        #if timezone_str in pytz.all_timezones:
        #    ...
        #else:
        #    raise ValueError("Invalid timezone string!")
        return timestamp[0:10]


    def __display_progress_bar(
        self,
        number_of_issues: int,
        iterator: int,
        issue_id: str,
        issue_key: str,
        issue_summary: str
    ) -> None:
        """
        This method prints out a progress bar while the issues get parsed.

        :param number_of_issues: The total number of fetched issues to parse
        :type number_of_issues: int
        :param iterator: Keeps track which of the fetched issues is currently parsed
        :type iterator: int
        :param issue_id: The id of the currently parsed issue - will be printed as well
        :type issue_id: str
        :param issue_key: The key of the currently parsed issue - will be printed as well
        :type issue_key: str
        :param issue_summary: The summary of the currently parsed issue - will be printed as well
        :type issue_summary: str
        
        :return: None
        """
        percentage = math.ceil(iterator/number_of_issues*100)

        progress_bar_length = 10
        
        length_done = int(percentage / progress_bar_length)
        length_todo = progress_bar_length - length_done

        progress_bar_done = "#" * length_done
        progress_bar_todo = " " * length_todo

        progress_bar = "[" + progress_bar_done + progress_bar_todo + "]"
        
        # Strip length to avoid malfunction SKSD-54
        if len(issue_summary) > 32:
            issue_summary = issue_summary[:29].strip() + "..."

        end_of_print = "\r"
        if percentage == 100:
            end_of_print = "\n"
        
        print(f" {progress_bar} {iterator}/{number_of_issues} ({percentage}%) {issue_key} ({issue_id}): {issue_summary}", end=end_of_print)
        if percentage < 100:
            print("\033[2K", end="") # Clear entire line