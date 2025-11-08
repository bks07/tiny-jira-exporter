# coding: utf8

import sys
import math
import chardet
from atlassian import Jira
from datetime import datetime
import pytz
import pandas as pd

from modules.exporter_config.exporter_config import ExporterConfig
from .fields.issue_field_type import IssueFieldType
from .fields.issue_field_type_factory import IssueFieldTypeFactory
from .fields.issue_field_type_short_text import IssueFieldTypeShortText
from .fields.issue_field_type_date import IssueFieldTypeDate
from .fields.issue_field_type_datetime import IssueFieldTypeDatetime

class IssueParser:
    """
    Connects to Jira and fetches the issues directly from Jira using a JQL query.

    :param config: The configuration originating from the YAML configuration file
    :type config: (object)ExporterConfig
    :param logger: The logger for debugging purposes
    :type logger: object
    """
    DATE_PATTERN_FULL = "%Y-%m-%dT%H:%M:%S.%f%z"
    DATE_PATTERN_DATE_ONLY = "%Y-%m-%d"

    def __init__(
        self,
        logger: object,
        config: ExporterConfig,
        pretty_print: bool = False
    ):
        # Read-only properties
        self.__logger: object = logger
        self.__config: ExporterConfig = config
        self.__shall_pretty_print: bool = pretty_print
        # Alterable properties
        self.__fields_to_fetch: dict = {}
        self.__parsed_data: list = []

    @property
    def logger(self) -> object:
        return self.__logger

    @property
    def shall_pretty_print(self) -> bool:
        return self.__shall_pretty_print


    @property
    def config(self) -> ExporterConfig:
        return self.__config
    
    @config.setter
    def config(self, value: ExporterConfig) -> None:
        self.__config = value
    

    @property
    def fields_to_fetch(self) -> dict:
        return self.__fields_to_fetch
    

    ######################
    ### PUBLIC METHODS ###
    ######################

    def fetch_and_parse_issues(
        self
    ) -> list:
        """
        Connects to Jira, fetches the issues, and prepares them for parsing.

        :return: None
        """
        self.__pretty_print("Connect to Jira instance...")
        self.logger.info(f"Connect to Jira instance '{self.config.domain}' with user '{self.config.username}'.")
        jira = self.__connect_to_jira()
        self.__pretty_print("... done.")
        self.logger.info("Jira connection successful.")

        self.__pretty_print("Prepare fields to fetch from Jira...")
        self.logger.info("Prepare fields to fetch from Jira.")
        schema_type_map = self.__fetch_field_types(jira)
        self.__prepare_standard_fields_to_fetch(schema_type_map)
        self.__prepare_custom_fields_to_fetch(schema_type_map)
        self.__pretty_print("... done.")
        self.logger.info("All fields are prepared to fetch.")

        self.__pretty_print("Fetch issues from Jira...")
        self.logger.info("Starting to fetch issues from Jira.")
        issues = self.__fetch_issues(jira)
        self.__pretty_print("... done.")
        self.logger.info(f"Issues successfully fetched: {len(issues)}")

        self.__pretty_print("Parse fetched Jira issues...")
        self.logger.info("Starting to parse issues.")
        parsed_issues =self.__parse_issues(issues)
        self.__pretty_print("... done.")
        self.logger.info("All fetched issues parsed successfully.")

        return parsed_issues


    def __connect_to_jira(
        self,
        jira_instance = None # Class for mock testing
    ) -> Jira:
        return jira_instance or Jira(
            url = self.config.domain,
            username = self.config.username,
            password = self.config.api_token,
            cloud = True
        )
    
    
    def __fetch_field_types(
        self,
        jira: Jira
    ) -> dict:
        # Build schema type map for all fields
        schema_type_map: dict = {}
        all_fields = jira.get_all_fields()
        for field in all_fields:
            field_id = field.get('id')
            schema_type = field.get('schema', {}).get('type')
            
            # Only store valid fields that have an ID and a schema type
            if field_id and schema_type:
                schema_type_map[field_id] = schema_type
        return schema_type_map


    def __prepare_standard_fields_to_fetch(self, schema_type_map: dict) -> None:
        """
        Prepare the list of standard Jira issue fields to fetch and export based on configuration.

        :param self: The IssueParser instance containing configuration and state
        """
        # Decide for all standard fields
        for standard_field_name, standard_field_id in ExporterConfig.STANDARD_ISSUE_FIELDS.items():
            shall_fetch = False
            shall_export_to_csv = bool(standard_field_name in self.config.standard_issue_fields)
            
            if (
                standard_field_name == ExporterConfig.ISSUE_FIELD_NAME__ISSUE_KEY
                or standard_field_name == ExporterConfig.ISSUE_FIELD_NAME__ISSUE_ID
            ):
                # Always fetch and export issue key and issue id
                shall_fetch = shall_export_to_csv = True
            elif standard_field_name == ExporterConfig.ISSUE_FIELD_NAME__SUMMARY:
                # Always fetch summary for having the info available for the progress bar
                shall_fetch = True
            elif standard_field_name == ExporterConfig.ISSUE_FIELD_NAME__FLAGGED:
                # Always fetch flagged for having the info available for the workflow
                standard_field_id = self.config.standard_issue_field_id_flagged
            
            self.__prepare_fields_to_fetch(
                schema_type_map,
                standard_field_name,
                standard_field_id,
                shall_fetch,
                shall_export_to_csv
            )


    def __prepare_custom_fields_to_fetch(self, schema_type_map: dict) -> None:
        for custom_field_name, custom_field_id in ExporterConfig.STANDARD_ISSUE_FIELDS.items():
            self.__prepare_fields_to_fetch(
                schema_type_map,
                custom_field_name,
                custom_field_id,
                shall_fetch=True,
                shall_export_to_csv=True
            )


    def __prepare_fields_to_fetch(
        self,
        schema_type_map: dict,
        field_name: str,
        field_id: str,
        shall_fetch: bool,
        shall_export_to_csv: bool
    ):
        schema_type = schema_type_map.get(field_id)
        self.logger.debug(f"Prepare field '{field_name}' (ID: {field_id}, Schema type: {schema_type}), Fetch: {shall_fetch}, Export to CSV: {shall_export_to_csv}")
        issue_field_type:IssueFieldType = IssueFieldTypeFactory.create_field_type(
            schema_type,
            field_name,
            field_id,
            shall_fetch,
            shall_export_to_csv,
            self.logger
        )
        self.logger.debug(f"Done. Adding field to fetch list with field type class: {issue_field_type.__class__.__name__}.")
        self.__fields_to_fetch[field_id] = issue_field_type
        

    def __fetch_issues(self, jira) -> list:
        """
        Connects to Jira and fetches the issues directly from Jira using a JQL query.
        Uses the configuration to access all required login credentials.

        :raise ValueError: On Jira error when JQL failed.

        :return: None
        """        
        try:
            # Call Jira to fetch issues
            json_result_string = jira.enhanced_jql(self.config.jql_query, fields=self.__fields_to_fetch.keys())
            return json_result_string.get("issues", [])

        except Exception as e:
            self.logger.critical(f"Jira request failed with JQL: {self.config.jql_query} (Original message: {e})")
            raise ValueError(f"Jira request failed with JQL: {self.config.jql_query}")


    def __parse_issues(self, issues_response: list) -> list:
        """
        Parses all issues that have been fetched previously to extract all information
        that will be written to the CSV output file.

        :return: None
        """
        parsed_issues = []
        number_of_issues = len(issues_response)
        # Crawl all fetches issues
        for i in range(number_of_issues):
            issue_raw = issues_response[i]
            # Save some variables for later use
            issue_key = IssueFieldTypeShortText("Issue Key", ExporterConfig.ISSUE_FIELD_ID__ISSUE_KEY)
            issue_key.data = issue_raw['key']

            issue_id = IssueFieldTypeShortText("Issue ID", ExporterConfig.ISSUE_FIELD_ID__ISSUE_ID)
            issue_id.data = issue_raw['id']

            issue_fields_raw = issue_raw['fields']

            issue_summary = self.fields_to_fetch(ExporterConfig.ISSUE_FIELD_ID__SUMMARY)
            issue_summary.data = issue_fields_raw[ExporterConfig.ISSUE_FIELD_ID__SUMMARY]


            self.logger.debug(f"Start parsing issue {issue_key.get_value_for_csv()} ({issue_id.get_value_for_csv()}).")


            # Get the default values of an issue that are available for each exported issue
            issue_creation_date = self.__parse_field_value(self.__timestamp_to_date(issue_fields['created'], IssueParser.DATE_PATTERN_FULL))

            # if self.shall_pretty_print:
            #     self.__display_progress_bar(number_of_issues, i, issue_id, issue_key, issue_summary)

            issue_data = {}

            for id, field in self.fields_to_fetch.items():
                if not field.shall_export_to_csv:
                    continue
                
                field.data = issue_fields_raw.get(id)

                if field.is_custom_field:
                    issue_data[self.config.custom_field_prefix + field.name] = field.get_value_for_csv()
                else:
                    issue_data[self.config.standard_field_prefix + field.name] = field.get_value_for_csv()
            
            # If workflow analysis is enabled, parse the status category timestamps
            if self.config.has_workflow:
                issue_data.update(self.__parse_status_category_timestamps(issue_id, issue_creation_date))
            
            parsed_issues.append(issue_data)
        
        if self.shall_pretty_print:
            print(" ... done.")
        
        self.logger.debug("All issues parsed.")
        return parsed_issues


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
        self.logger.debug("Write CSV file.")

        if self.shall_pretty_print:
            print(f"\nWrite CSV output file to '{file_location}'.")
        
        try:
            df = pd.DataFrame.from_dict(self.__parsed_data)
            df.to_csv(file_location, index=False, sep=";", encoding="utf-8")
            
            if self.shall_pretty_print:
                print(" ... done.")
            
            self.logger.debug("CSV file successfully written.")
        except Exception as error:
            self.logger.critical(error)


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
        for status_category in self.config.workflow.categories:
            column_name: str = self.config.status_category_prefix + status_category
            if is_first_category:
                # Every issue gets created with the very first status of the workflow
                # Therefore, set the creation date for the very first category
                categories[column_name] = issue_creation_date
                is_first_category = False
            else:
                categories[column_name] = None

        # Crawl through all status changes of an issue
        status_changelog = reversed(self.jira.get_issue_status_changelog(issue_id))
        for transition in status_changelog:
            # Add the transition information to a list first
            # since it is returned in descending sort order
            self.__set_transition_dates(categories, transition['from'], transition['to'], transition['date'])

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
        category_start_status = self.config.workflow.category_of_status(start_status)
        category_destination_status = self.config.workflow.category_of_status(destination_status)

        position_start_status = self.config.workflow.index_of_status(start_status)
        position_destination_status = self.config.workflow.index_of_status(destination_status)

        category_start_status_index = self.config.workflow.index_of_category(category_start_status)
        category_destination_status_index = self.config.workflow.index_of_category(category_destination_status)

        self.logger.debug(f"Transition on {date}: {position_start_status}:{start_status}({category_start_status}) -> {position_destination_status}:{destination_status}({category_destination_status})")
        # Nothing to do here, this date had already been written
        # since there is no change to the category
        if category_start_status_index == category_destination_status_index:
            self.logger.debug(f"Same category, no dates to set.")
            return category_dates
        # The normal case, where the issue has been moved forward
        elif category_start_status_index < category_destination_status_index:
            for category_index in range(category_start_status_index, category_destination_status_index):
                self.logger.debug(f"Set date {date} for category: {category_index+1}")
                column_name: str = self.config.status_category_prefix + self.config.workflow.categories[category_index+1]
                # __timestamp_to_date returns a YYYY-MM-DD string now
                category_dates[column_name] = self.__parse_field_value(self.__timestamp_to_date(date, IssueParser.DATE_PATTERN_FULL))
        # The case, when an issue has moved backward to a previous category
        else:
            for category_index in range(category_destination_status_index, category_start_status_index):
                self.logger.debug(f"Unset date for category: {category_index+1}")
                column_name: str = self.config.status_category_prefix + self.config.workflow.categories[category_index+1]
                category_dates[column_name] = None

        return category_dates


    #######################
    ### SUPPORT METHODS ###
    #######################


    def __pretty_print(
        self,
        message: str
    ) -> None:
        if self.shall_pretty_print:
            print(f"\n{message}")