# coding: utf8

import sys
from atlassian import Jira
import pandas as pd

from modules.exporter_config.exporter_config import ExporterConfig
from modules.issue_parser.workflow import Workflow
from modules.issue_parser.progress_bar import ProgressBar
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
        parsed_issues = self.__parse_issues(issues)
        self.__pretty_print("... done.")
        self.logger.info("All fetched issues parsed successfully.")

        return parsed_issues


    def export_to_csv(
        self,
        parsed_issues: list,
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
            df = pd.DataFrame.from_dict(parsed_issues)
            df.to_csv(file_location, index=False, sep=";", encoding="utf-8")
            
            if self.shall_pretty_print:
                print(" ... done.")
            
            self.logger.debug("CSV file successfully written.")
        except Exception as error:
            self.logger.critical(error)


    ####################
    ### PARSER LOGIC ###
    ####################


    def __connect_to_jira(
        self,
        jira_instance = None # Class for mock testing
    ) -> Jira:
        if self.config.is_cloud:
            self.logger.info("Connecting to Jira Cloud instance.")
            return jira_instance or Jira(
                url = self.config.domain,
                username = self.config.username,
                password = self.config.api_token,
                cloud = True
            )
        else:
            self.logger.info("Connecting to Jira Server/Data Center instance.")
            return jira_instance or Jira(
                url = self.config.domain,
                username = self.config.username,
                password = self.config.api_token,
                cloud = False
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
        added_fields = []
        for standard_field_id, standard_field_name in self.config.standard_issue_fields.items():
            self.__prepare_fields_to_fetch(
                schema_type_map,
                standard_field_name,
                standard_field_id
            )
            added_fields.append(standard_field_name)
        if self.config.has_workflow:
            # Make sure that the status field is always fetched when workflow analysis is enabled
            if not ExporterConfig.ISSUE_FIELD_NAME__STATUS in added_fields:
                self.__prepare_fields_to_fetch(
                    schema_type_map,
                    ExporterConfig.ISSUE_FIELD_NAME__STATUS,
                    ExporterConfig.STANDARD_ISSUE_FIELDS[ExporterConfig.ISSUE_FIELD_NAME__STATUS],
                    fetch_only=True
                )
            # Make sure that the created field is always fetched when workflow analysis is enabled
            if not ExporterConfig.ISSUE_FIELD_NAME__CREATED in added_fields:
                self.__prepare_fields_to_fetch(
                    schema_type_map,
                    ExporterConfig.ISSUE_FIELD_NAME__CREATED,
                    ExporterConfig.STANDARD_ISSUE_FIELDS[ExporterConfig.ISSUE_FIELD_NAME__CREATED],
                    fetch_only=True
                )
        

    def __prepare_custom_fields_to_fetch(self, schema_type_map: dict) -> None:
        for custom_field_id, custom_field_name in self.config.custom_issue_fields.items():
            self.__prepare_fields_to_fetch(
                schema_type_map,
                custom_field_name,
                custom_field_id
            )


    def __prepare_fields_to_fetch(
        self,
        schema_type_map: dict,
        field_name: str,
        field_id: str
    ):
        schema_type = schema_type_map.get(field_id)
        self.logger.debug(f"Prepare field '{field_name}' (ID: {field_id}) with schema type '{schema_type}'.")
        issue_field_type:IssueFieldType = IssueFieldTypeFactory.create_field_type(
            schema_type,
            field_name,
            field_id,
            self.logger
        )
        self.logger.debug(f"Done. Adding field to fetch list with field type class: {issue_field_type.__class__.__name__}.")
        self.fields_to_fetch[field_id] = issue_field_type
        

    def __fetch_issues(self, jira) -> list:
        """
        Connects to Jira and fetches the issues directly from Jira using a JQL query.
        Uses the configuration to access all required login credentials.

        :raise ValueError: On Jira error when JQL failed.

        :return: None
        """        
        try:
            # Call Jira to fetch issues
            field_ids = []
            for id in self.fields_to_fetch.keys():
                field_ids.append(id)

            json_result_string = jira.enhanced_jql(self.config.jql_query, fields=field_ids)
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

        progress_bar = ProgressBar(total_number_of_items=number_of_issues)

        if self.config.has_workflow:
            workflow = Workflow(
                self.config.workflow,
                self.config.time_zone,
                IssueFieldTypeDate.DATE_PATTERN, # TODO: Should be configurable via ExporterConfig 
                self.config.status_category_prefix,
                self.logger)

        # Crawl all fetches issues
        for i in range(number_of_issues):
            raw_issue_data = issues_response[i]
            parsed_issue_fields = {}            

            # Issue key and ID are not stored as fields but part at the root of the issue JSON
            issue_key = IssueFieldType.string_to_utf8(raw_issue_data[ExporterConfig.ISSUE_FIELD_ID__ISSUE_KEY])
            issue_id = IssueFieldType.string_to_utf8(raw_issue_data[ExporterConfig.ISSUE_FIELD_ID__ISSUE_ID])

            self.logger.debug(f"Start parsing issue {issue_key} ({issue_id}).")

            parsed_issue_fields[self.config.standard_field_prefix + ExporterConfig.ISSUE_FIELD_NAME__ISSUE_KEY] = issue_key
            parsed_issue_fields[self.config.standard_field_prefix + ExporterConfig.ISSUE_FIELD_NAME__ISSUE_ID] = issue_id

            if self.shall_pretty_print:
                progress_bar.next_item()
                progress_bar.display(f"{issue_key} ({issue_id})")

            # The created date is required for workflow analysis later on
            issue_created_date = None
            field_id_created = ExporterConfig.STANDARD_ISSUE_FIELDS[ExporterConfig.ISSUE_FIELD_NAME__CREATED]

            # Crawl all fields the exporter should fetch
            for id, field in self.fields_to_fetch.items():
                field.data = raw_issue_data['fields'].get(id)

                # Export the field value to the parsed issue fields dictionary if required
                if not field.fetch_only:
                    if field.is_custom_field:
                        column_name = self.config.custom_field_prefix + field.name
                    else:
                        column_name = self.config.standard_field_prefix + field.name
                    
                    parsed_issue_fields[column_name] = field.get_value_for_csv()

                    if self.config.export_value_ids and field.has_value_id:
                        parsed_issue_fields[column_name + self.config.value_id_suffix] = field.get_value_id_for_csv()
                
                # Store the created date for workflow analysis later on
                if field_id_created == id and self.config.has_workflow:
                    issue_created_date = field.get_value_for_csv()

            
            # If workflow analysis is enabled, parse the status category timestamps
            if self.config.has_workflow:
                workflow.something() # TODO remove this line once Workflow class is not empty anymore
                parsed_issue_fields.update(self.__parse_status_category_timestamps(issue_id, issue_created_date))
            
            parsed_issues.append(parsed_issue_fields)
        
        self.logger.debug("All issues parsed.")
        return parsed_issues


    #######################
    ### SUPPORT METHODS ###
    #######################


    def __pretty_print(
        self,
        message: str
    ) -> None:
        if self.shall_pretty_print:
            print(message)