# coding: utf8

import math
import chardet
from jira import JIRA
import pandas as pd

from packages.exporter_config.exporter_config import ExporterConfig
from packages.exporter_config.standard_issue_field import StandardIssueField
from packages.exporter_config.custom_issue_field import CustomIssueField

class IssueParser:
    """
    Connects to Jira and fetches the issues directly from Jira using a JQL query.

    :param config: The configuration originating from the YAML configuration file
    :type config: (object)ExporterConfig
    :param logger: The logger for debugging purposes
    :type logger: object
    """
    def __init__(self, config: ExporterConfig, logger: object, pretty_print: bool = False):
        self.__config: ExporterConfig = config
        self.__logger: object = logger
        self.__jira: JIRA = JIRA(config.domain, basic_auth=(config.username, config.api_token))
        self.__issues: list = []
        self.__parsed_data: list = []
        self.__shall_pretty_print: bool = pretty_print


    ######################
    ### Public methods ###
    ######################


    def fetch_issues(self) -> None:
        """
        Connects to Jira and fetches the issues directly from Jira using a JQL query.

        :param jql_query: The JQL query that gets executed
        :type jql_query: str
        :param max_results: The maximum number of issues that will be returned by the JQL query
        :type max_results: int

        :raise None

        :return The issue object
        """
        # Execute JQL query
        if self.__shall_pretty_print:
            print("\nFetch issues from Jira...")
        
        try:
            self.__issues = self.__jira.search_issues(self.__config.jql_query, fields=self.__config.fields_to_fetch, maxResults=self.__config.max_results)
            self.__logger.info(f"Issues successfully fetched: {len(self.__issues)}")
        except Exception as e:
            self.__logger.critical(f"Jira request failed with JQL: {self.__config.jql_query} (Original message: {e})")
            raise ValueError(f"Jira request failed with JQL: {self.__config.jql_query}")
        
        if self.__shall_pretty_print:
            print(" ... done.")


    def parse_issues(self) -> None:
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """
        if self.__shall_pretty_print:
            print("\nParse fetched Jira issues...")

        number_of_issues = len(self.__issues)
        # Crawl all fetches issues
        for i in range(number_of_issues):
            issue = self.__issues[i]
            # Save some variables for later use
            issue_id = self.__parse_field_value(issue.id)
            issue_status = self.__parse_field_value(issue.fields.status.name)
            issue_creation_date = self.__parse_field_value(self.__transform_date(issue.fields.created))
            issue_summary = self.__parse_field_value(issue.fields.summary)
            # Get the default values of an issue that are available for each export

            if self.__shall_pretty_print:
                self.__display_progress_bar(number_of_issues, i, issue_id, issue.key, issue_summary)

            issue_data = {}
            
            for field in self.__config.issue_fields:
                if not field.shall_export_to_csv:
                    continue

                if isinstance(field, CustomIssueField):
                    column_name: str = self.__config.custom_field_prefix + field.name
                    issue_data[self.__parse_field_value(column_name)] = self.__parse_field_value(eval("issue.fields." + field.id))

                elif isinstance(field, StandardIssueField):
                    column_name: str = self.__config.standard_field_prefix + field.name

                    match field.name:
                        case ExporterConfig.ISSUE_FIELD_NAME_ISSUE_KEY:
                            # No prefix for this column
                            issue_data[field.name] = self.__parse_field_value(issue.key)

                        case ExporterConfig.ISSUE_FIELD_NAME_ISSUE_ID:
                            # No prefix for this column
                            issue_data[field.name] = issue_id

                        case ExporterConfig.ISSUE_FIELD_NAME_ISSUE_TYPE:
                            issue_data[field.name] = self.__parse_field_value(issue.fields.issuetype.name)

                        case ExporterConfig.ISSUE_FIELD_NAME_REPORTER:
                            issue_reporter_account_id = ""
                            if issue.fields.reporter != None:
                                issue_reporter_account_id = issue.fields.reporter.accountId
                            issue_data[column_name] = self.__parse_field_value(issue.fields.reporter)
                            issue_data[column_name + " ID"] = self.__parse_field_value(issue_reporter_account_id)

                        case ExporterConfig.ISSUE_FIELD_NAME_ASSIGNEE:
                            issue_assignee_account_id = ""
                            if issue.fields.assignee != None:
                                issue_assignee_account_id = issue.fields.assignee.accountId
                            issue_data[column_name] = self.__parse_field_value(issue.fields.assignee)
                            issue_data[column_name + " ID"] = self.__parse_field_value(issue_assignee_account_id)

                        case ExporterConfig.ISSUE_FIELD_NAME_SUMMARY:
                            issue_data[column_name] = issue_summary

                        case ExporterConfig.ISSUE_FIELD_NAME_STATUS:
                            issue_data[column_name] = issue_status

                        case ExporterConfig.ISSUE_FIELD_NAME_RESOLUTION:
                            issue_data[column_name] = self.__parse_field_value(issue.fields.resolution)

                        case ExporterConfig.ISSUE_FIELD_NAME_PRIORITY:
                            issue_data[column_name] = self.__parse_field_value(issue.fields.priority)

                        case ExporterConfig.ISSUE_FIELD_NAME_CREATED:
                            issue_data[column_name] = issue_creation_date

                        case ExporterConfig.ISSUE_FIELD_NAME_RESOLVED:
                            issue_data[column_name] = self.__parse_field_resolution_date(issue.fields.resolutiondate)

                        case ExporterConfig.ISSUE_FIELD_NAME_FLAGGED:
                            issue_data[column_name] = self.__parse_field_flagged(eval("issue.fields." + field.id))

                        case ExporterConfig.ISSUE_FIELD_NAME_LABELS:
                            issue_data[column_name] = self.__parse_field_labels(issue.fields.labels)
                    
            if self.__config.has_workflow():
                issue_data.update(self.__parse_status_category_timestamps(issue_id, issue_creation_date))
            
            self.__parsed_data.append(issue_data)
        
        if self.__shall_pretty_print:
            print(" ... done.")


    def export_to_csv(self, file_location: str) -> None:
        if self.__shall_pretty_print:
            print(f"\nWrite CSV output file to '{file_location}'.")
        
        df = pd.DataFrame.from_dict(self.__parsed_data)
        df.to_csv(file_location, index=False, sep=";", encoding="latin-1")

        if self.__shall_pretty_print:
            print(" ... done.")


    ############################
    ### PARSE SPECIAL FIELDS ###
    ############################


    def __parse_field_labels(self, labels:list):
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """
        return_string = ""
        if len(labels) > 0:
           return_string = "'" + "'|'".join([x for x in labels]) + "'"
        return self.__parse_field_value(return_string)
        

    def __parse_field_resolution_date(self, date:str) -> str:
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """
        return_string = ""
        if date != None and len(str(date)) > 0:
            return_string = date
        return self.__parse_field_value(self.__transform_date(return_string))

        
    def __parse_field_flagged(self, value):
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """
        return value is not None


    ######################
    ### PARSE WORKFLOW ###
    ######################


    def __parse_status_category_timestamps(self, issue_id, issue_creation_date) -> dict:
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """
        categories = {}
        transitions = []
        is_first_category = True
        # Initiate the status category timestamps by adding all of them with value None
        for status_category in self.__config.get_status_categories():
            if is_first_category:
                # Every issue gets created with the very first status of the workflow
                # Therefore, set the creation date for the very first category
                categories[status_category] = issue_creation_date
                is_first_category = False
            else:
                categories[status_category] = None

        # Crawl through all changelogs of an issue
        changelogs = self.jira.issue(issue_id, expand="changelog").changelog.histories
        self.logger.debug(f"ISSUE {issue_id}")
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


    def __set_transition_dates(self, category_dates:dict, from_status:str, to_status:str, date:str) -> dict:
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """
        category_from_status = self.__config.workflow.category_of_status(from_status)
        category_to_status = self.__config.workflow.category_of_status(to_status)

        category_from_status_index = self.__config.workflow.index_of_category(category_from_status)
        category_to_status_index = self.__config.workflow.index_of_category(category_to_status)

        self.__logger.debug(f"###TRANSITION: {from_status}({category_from_status}) -> {to_status}({category_to_status})")
        self.__logger.debug(f"Date: {date}")
        # Nothing to do here, this date had already been written
        # since there is no change to the category
        if category_from_status_index == category_to_status_index:
            self.__logger.debug(f"Same category!\n")
            return category_dates
        # The normal case, where the issue has been moved forward
        elif category_from_status_index < category_to_status_index:
            for category_index in range(category_from_status_index, category_to_status_index):
                self.__logger.debug(f"SET DATE: {category_index+1}")
                category_dates[self.__config.workflow.categories[category_index+1]] = date
        # The case, when an issue has moved backward to a previous category
        else:
            for category_index in range(category_to_status_index, category_from_status_index):
                self.__logger.debug(f"DELETE DATE: {category_index+1}")
                category_dates[self.__config.workflow.categories[category_index+1]] = None

        return category_dates


    #######################
    ### SUPPORT METHODS ###
    #######################


    def __parse_field_value(self, value) -> str:
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
            match self.__config.get_decimal_separator():
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


    def __transform_date(self, timestamp:str):
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


    def __display_progress_bar(self, number_of_issues:int, iterator:int, issue_id:str, issue_key:str, issue_summary:str):
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """
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