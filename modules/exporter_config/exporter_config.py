# coding: utf8

import datetime
import yaml
import re

from .workflow import Workflow
from ..issue_parser.fields.issue_field_type import IssueFieldType

class ExporterConfig:
    """
    Reads and parses a YAML configuration file and provides all configuration data
    to the IssueParser class for Jira issue export.

    This class handles:
    - Jira connection details (domain, username, API token)
    - Search criteria (projects, filters, issue types, date ranges)
    - Issue field configuration (standard and custom fields)
    - Workflow and status tracking
    - Export formatting options (decimal separator, time zone, field prefixes)

    :param yaml_file_location: The file location of the YAML configuration file
    :type yaml_file_location: str
    :param logger: The logger instance for debugging and informational messages
    :type logger: object
    :param shall_pretty_print: If True, configuration parser prints basic information to console
    :type shall_pretty_print: bool
    :raises ValueError: If required configuration sections or attributes are missing
    """
    
    # YAML configuration section keys
    YAML__CONNECTION = "Connection"
    YAML__CONNECTION__DOMAIN = "Domain"
    YAML__CONNECTION__USERNAME = "Username"
    YAML__CONNECTION__API_TOKEN = "API Token"
    YAML__SEARCH_CRITERIA = "Search Criteria"
    YAML__SEARCH_CRITERIA__PROJECTS = "Projects"
    YAML__SEARCH_CRITERIA__ISSUE_TYPES = "Issue Types"
    YAML__SEARCH_CRITERIA__FILTER = "Filter"
    YAML__SEARCH_CRITERIA__MAX_RESULTS = "Max Results"
    YAML__SEARCH_CRITERIA__EXCLUDE_CREATED_DATE = "Exclude Created Date"
    YAML__SEARCH_CRITERIA__EXCLUDE_RESOLVED_DATE = "Exclude Resolved Date"
    YAML__STANDARD_FIELDS = "Standard Issue Fields"
    YAML__CUSTOM_FIELDS = "Custom Issue Fields"
    YAML__WORKFLOW = "Workflow"
    YAML__MANDATORY = "Mandatory"
    YAML__MANDATORY__FLAGGED = "Flagged Field ID"
    YAML__MANDATORY__DECIMAL_SEPARATOR = "Decimal Separator"
    YAML__MISC = "Misc"
    YAML__MISC__STANDARD_FIELD_PREFIX = "Standard Field Prefix"
    YAML__MISC__CUSTOM_FIELD_PREFIX = "Custom Field Prefix"
    YAML__MISC__ISSUE_FIELD_ID_POSTFIX = "Issue Field ID Postfix"
    YAML__MISC__STATUS_CATEGORY_PREFIX = "Status Category Prefix"
    YAML__MISC__TIME_ZONE = "Time Zone"

    # Issue field display names - Always exported
    ISSUE_FIELD_NAME__ISSUE_KEY = "Key"
    ISSUE_FIELD_NAME__ISSUE_ID = "ID"
    # Descriptive fields
    ISSUE_FIELD_NAME__ISSUE_TYPE = "Type"
    ISSUE_FIELD_NAME__SUMMARY = "Summary"
    ISSUE_FIELD_NAME__PARENT = "Parent"
    # User fields
    ISSUE_FIELD_NAME__REPORTER = "Reporter"
    ISSUE_FIELD_NAME__ASSIGNEE = "Assignee"
    # Status-related fields
    ISSUE_FIELD_NAME__STATUS = "Status"
    ISSUE_FIELD_NAME__PRIORITY = "Priority"
    ISSUE_FIELD_NAME__FLAGGED = "Flagged"
    ISSUE_FIELD_NAME__RESOLUTION = "Resolution"
    # Date/time-related fields
    ISSUE_FIELD_NAME__CREATED = "Created"
    ISSUE_FIELD_NAME__DUE_DATE = "Due Date"
    ISSUE_FIELD_NAME__UPDATED = "Updated"
    ISSUE_FIELD_NAME__RESOLVED = "Resolved"
    # Label-like fields
    ISSUE_FIELD_NAME__LABELS = "Labels"
    ISSUE_FIELD_NAME__COMPONENTS = "Components"
    ISSUE_FIELD_NAME__AFFECTED_VERSIONS = "Affected Versions"
    ISSUE_FIELD_NAME__FIXED_VERSIONS = "Fixed Versions"

    # Mapping of issue field display names to Jira field IDs
    STANDARD_ISSUE_FIELDS = {
        ISSUE_FIELD_NAME__ISSUE_KEY: "key",
        ISSUE_FIELD_NAME__ISSUE_ID: "id",
        ISSUE_FIELD_NAME__ISSUE_TYPE: "issuetype",
        ISSUE_FIELD_NAME__SUMMARY: "summary",
        ISSUE_FIELD_NAME__PARENT: "parent",
        ISSUE_FIELD_NAME__REPORTER: "reporter",
        ISSUE_FIELD_NAME__ASSIGNEE: "assignee",
        ISSUE_FIELD_NAME__STATUS: "status",
        ISSUE_FIELD_NAME__PRIORITY: "priority",
        ISSUE_FIELD_NAME__FLAGGED: "",
        ISSUE_FIELD_NAME__RESOLUTION: "resolution",
        ISSUE_FIELD_NAME__CREATED: "created",
        ISSUE_FIELD_NAME__DUE_DATE: "duedate",
        ISSUE_FIELD_NAME__UPDATED: "updated",
        ISSUE_FIELD_NAME__RESOLVED: "resolved",
        ISSUE_FIELD_NAME__LABELS: "labels",
        ISSUE_FIELD_NAME__COMPONENTS: "components",
        ISSUE_FIELD_NAME__AFFECTED_VERSIONS: "versions",
        ISSUE_FIELD_NAME__FIXED_VERSIONS: "fixVersions"
    }

    # Decimal separator constants
    DECIMAL_SEPARATOR_POINT = "Point"
    DECIMAL_SEPARATOR_COMMA = "Comma"

    def __init__(
        self,
        yaml_file_location: str,
        logger: object,
        shall_pretty_print: bool = False
    ):
        """
        Initialize the ExporterConfig instance by loading and parsing the YAML configuration file.

        :param yaml_file_location: Path to the YAML configuration file
        :type yaml_file_location: str
        :param logger: Logger instance for debug and info messages
        :type logger: object
        :param shall_pretty_print: Whether to print configuration info to console, defaults to False
        :type shall_pretty_print: bool
        :raises ValueError: If required configuration sections or attributes are missing or invalid
        """
        self.__logger = logger
        self.__shall_pretty_print = shall_pretty_print
        
        # Properties for Jira connection
        self.__domain: str = ""
        self.__username: str = ""
        self.__api_token: str = ""

        # Properties for JQL request
        self.__jql_query: str = ""
        self.__max_results: int = 100

        # Properties for issue field export
        self.__standard_issue_fields: dict = {}
        self.__standard_issue_field_id_flagged: str = ""
        self.__custom_issue_fields: dict = {}

        self.__standard_field_prefix: str = ""
        self.__custom_field_prefix: str = ""
        self.__issue_field_id_postfix: str = ""

        # Workflow timestamp export
        self.__workflow: Workflow = None
        self.__status_category_prefix: str = ""

        # Other properties
        self.__decimal_separator: str = ExporterConfig.DECIMAL_SEPARATOR_COMMA
        self.__time_zone: str = ""

        # Parse YAML config file to populate all properties
        self.__load_yaml_file(yaml_file_location)

    
    ##################
    ### PROPERTIES ###
    ##################

    @property
    def logger(self) -> object:
        """
        Get the logger instance.

        :return: The logger object used for debug messages
        :rtype: object
        """
        return self.__logger


    # Properties for Jira connection

    @property
    def domain(self) -> str:
        """
        Get the Jira domain URL.

        :return: The Jira domain URL in format https://[YOUR-NAME].atlassian.net
        :rtype: str
        """
        return self.__domain

    @domain.setter
    def domain(self, value: str):
        """
        Set the Jira domain URL with validation.

        :param value: The Jira domain URL to set
        :type value: str
        :raises ValueError: If the domain does not match the expected pattern
        """
        if re.match(r"^https://[^/]+\.atlassian\.net$", value):
            self.__domain = value
        else:
            raise ValueError(f"The given domain '{value}' does not fit the pattern 'https://[YOUR-NAME].atlassian.net'. Please check the YAML configuration file.")
        self.__log_attribute(ExporterConfig.YAML__CONNECTION, ExporterConfig.YAML__CONNECTION__DOMAIN, value)


    @property
    def username(self) -> str:
        """
        Get the Jira username.

        :return: The Jira username for authentication
        :rtype: str
        """
        return self.__username

    @username.setter
    def username(self, value: str):
        """
        Set the Jira username.

        :param value: The Jira username to set
        :type value: str
        """
        self.__username = value
        self.__log_attribute(ExporterConfig.YAML__CONNECTION, ExporterConfig.YAML__CONNECTION__USERNAME, value)


    @property
    def api_token(self) -> str:
        """
        Get the Jira API token.

        :return: The Jira API token for authentication
        :rtype: str
        """
        return self.__api_token

    @api_token.setter
    def api_token(self, value: str):
        """
        Set the Jira API token.

        :param value: The Jira API token to set
        :type value: str
        """
        self.__api_token = value
        self.__log_attribute(ExporterConfig.YAML__CONNECTION, ExporterConfig.YAML__CONNECTION__API_TOKEN, value)


    # Properties for JQL request

    @property
    def jql_query(self) -> str:
        """
        Get the JQL query used to fetch issues.

        :return: The JQL (Jira Query Language) query string
        :rtype: str
        """
        return self.__jql_query

    @jql_query.setter
    def jql_query(self, value: str):
        """
        Set the JQL query.

        :param value: The JQL query string to set
        :type value: str
        """
        self.__jql_query = value
        self.logger.debug(f"JQL query generated: {value}")


    @property
    def max_results(self) -> int:
        """
        Get the maximum number of results to fetch from Jira.

        :return: The maximum number of issues to fetch
        :rtype: int
        """
        return self.__max_results

    @max_results.setter
    def max_results(self, value: int):
        """
        Set the maximum number of results to fetch.

        :param value: The maximum number of issues to fetch
        :type value: int
        """
        self.__max_results = value
        self.__log_attribute(ExporterConfig.YAML__SEARCH_CRITERIA, ExporterConfig.YAML__SEARCH_CRITERIA__MAX_RESULTS, str(value))


    # Properties for issue field export

    @property
    def standard_issue_fields(self) -> dict:
        """
        Get the standard issue fields to export.

        :return: Dictionary mapping Jira field IDs to display names
        :rtype: dict
        """
        return self.__standard_issue_fields


    @property
    def standard_issue_field_id_flagged(self) -> str:
        """
        Get the custom field ID for the flagged field.

        :return: The custom field ID for flagged issues
        :rtype: str
        """
        return self.__standard_issue_field_id_flagged


    @property
    def custom_issue_fields(self) -> dict:
        """
        Get the custom issue fields to export.

        :return: Dictionary mapping custom field IDs to display names
        :rtype: dict
        """
        return self.__custom_issue_fields


    @property
    def standard_field_prefix(self) -> str:
        """
        Get the prefix for standard field names in the export.

        :return: The prefix string for standard fields
        :rtype: str
        """
        return self.__standard_field_prefix

    @standard_field_prefix.setter
    def standard_field_prefix(self, value: str) -> None:
        """
        Set the prefix for standard field names.

        :param value: The prefix string to set
        :type value: str
        """
        self.__standard_field_prefix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__STANDARD_FIELD_PREFIX, str(value))


    @property
    def custom_field_prefix(self) -> str:
        """
        Get the prefix for custom field names in the export.

        :return: The prefix string for custom fields
        :rtype: str
        """
        return self.__custom_field_prefix

    @custom_field_prefix.setter
    def custom_field_prefix(self, value: str) -> None:
        """
        Set the prefix for custom field names.

        :param value: The prefix string to set
        :type value: str
        """
        self.__custom_field_prefix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__CUSTOM_FIELD_PREFIX, str(value))


    @property
    def issue_field_id_postfix(self) -> str:
        """
        Get the postfix appended to field IDs in the export.

        :return: The postfix string for field IDs
        :rtype: str
        """
        return self.__issue_field_id_postfix
    
    @issue_field_id_postfix.setter
    def issue_field_id_postfix(self, value: str) -> None:
        """
        Set the postfix for field IDs.

        :param value: The postfix string to set
        :type value: str
        """
        self.__issue_field_id_postfix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__ISSUE_FIELD_ID_POSTFIX, str(value))


    # Properties for workflow timestamp export

    @property
    def workflow(self) -> Workflow:
        """
        Get the workflow configuration.

        :return: The Workflow object containing status information
        :rtype: Workflow
        """
        return self.__workflow


    @property
    def has_workflow(self) -> bool:
        """
        Check if workflow configuration exists and contains statuses.

        :return: True if workflow is configured with at least one status, False otherwise
        :rtype: bool
        """
        return self.workflow is not None and self.workflow.number_of_statuses > 0


    @property
    def status_category_prefix(self) -> str:
        """
        Get the prefix for status category field names.

        :return: The prefix string for status categories
        :rtype: str
        """
        return self.__status_category_prefix
    
    @status_category_prefix.setter
    def status_category_prefix(self, value: str) -> None:
        """
        Set the prefix for status category field names.

        :param value: The prefix string to set
        :type value: str
        """
        self.__status_category_prefix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__STATUS_CATEGORY_PREFIX, str(value))


    # Other properties

    @property
    def decimal_separator(self) -> str:
        """
        Get the decimal separator to use in CSV export.

        :return: Either DECIMAL_SEPARATOR_POINT or DECIMAL_SEPARATOR_COMMA
        :rtype: str
        """
        return self.__decimal_separator
    
    @decimal_separator.setter
    def decimal_separator(self, value: str) -> None:
        """
        Set the decimal separator for CSV export.

        :param value: Either DECIMAL_SEPARATOR_POINT or DECIMAL_SEPARATOR_COMMA
        :type value: str
        """
        self.__decimal_separator = value
        self.__log_attribute(ExporterConfig.YAML__MANDATORY, ExporterConfig.YAML__MANDATORY__DECIMAL_SEPARATOR, str(value))


    @property
    def time_zone(self) -> str:
        """
        Get the time zone for date/time field conversion.

        :return: The time zone string (e.g., 'UTC', 'America/New_York')
        :rtype: str
        """
        return self.__time_zone
    
    @time_zone.setter
    def time_zone(self, value: str) -> None:
        """
        Set the time zone for date/time field conversion.

        :param value: The time zone string
        :type value: str
        """
        self.__time_zone = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__TIME_ZONE, str(value))


    ######################
    ### PUBLIC METHODS ###
    ######################


    #######################
    ### SUPPORT METHODS ###
    #######################

    def __load_yaml_file(self, file_location: str) -> None:
        """
        Load and parse the YAML configuration file and populate all configuration properties.

        Processes connection details, search criteria, field configurations, workflow settings,
        and miscellaneous export options from the YAML file.

        :param file_location: The path to the YAML configuration file
        :type file_location: str
        :raises ValueError: If required configuration sections are missing or attributes are invalid
        :return: None
        """
        self.logger.debug("Start loading YAML configuration file.")

        self.__pretty_print("Process YAML config file...")

        # Open the YAML file in read mode
        with open(file_location, "r") as file:
            # Parse the contents using safe_load()
            data = yaml.safe_load(file)
        
        # Check if search criteria is set properly
        if ExporterConfig.YAML__SEARCH_CRITERIA not in data:
            raise ValueError("No search criteria defined in YAML config file.")

        # Check if mandatory attributes are configured
        if ExporterConfig.YAML__MANDATORY not in data:
            raise ValueError("Mandatory configuration properties are missing in YAML file.")

        # Set up the Jira access data, this part of the configuration is optional.
        if ExporterConfig.YAML__CONNECTION in data:
            if ExporterConfig.YAML__CONNECTION__DOMAIN in data[ExporterConfig.YAML__CONNECTION]:
                self.domain = data[ExporterConfig.YAML__CONNECTION][ExporterConfig.YAML__CONNECTION__DOMAIN]

            if ExporterConfig.YAML__CONNECTION__USERNAME in data[ExporterConfig.YAML__CONNECTION]:
                self.username = data[ExporterConfig.YAML__CONNECTION][ExporterConfig.YAML__CONNECTION__USERNAME]
            
            if ExporterConfig.YAML__CONNECTION__API_TOKEN in data[ExporterConfig.YAML__CONNECTION]:
                self.api_token = data[ExporterConfig.YAML__CONNECTION][ExporterConfig.YAML__CONNECTION__API_TOKEN]
        
        # Set up the JQL query to retrieve the right issues
        jql_query: str = ""
        if ExporterConfig.YAML__SEARCH_CRITERIA__FILTER in data[ExporterConfig.YAML__SEARCH_CRITERIA]:
            # Creates a query where it selects the given filter
            jql_query = "filter = '" + str(data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__FILTER]) + "'"
        elif ExporterConfig.YAML__SEARCH_CRITERIA__PROJECTS in data[ExporterConfig.YAML__SEARCH_CRITERIA] and len(data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__PROJECTS]) > 0:
            # Creates a default JQL query like "project IN(PKEY1, PKEY2) ORDER BY issuekey ASC
            jql_query = self.__jql_list_of_values("project", data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__PROJECTS])

            if ExporterConfig.YAML__SEARCH_CRITERIA__ISSUE_TYPES in data[ExporterConfig.YAML__SEARCH_CRITERIA] and \
                len(data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__ISSUE_TYPES]) > 0:
                jql_query += " AND " + self.__jql_list_of_values("issuetype", data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__ISSUE_TYPES])
            
            # Issues created after a certain date
            if ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_CREATED_DATE in data[ExporterConfig.YAML__SEARCH_CRITERIA]:
                exclude_created_date = data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_CREATED_DATE]
                if self.__check_date(exclude_created_date):
                    jql_query += f" AND created >= '{exclude_created_date}'"
            # Issues resolved after a certain date
            if ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_RESOLVED_DATE in data[ExporterConfig.YAML__SEARCH_CRITERIA]:
                exclude_resolved_date = data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_RESOLVED_DATE]
                if self.__check_date(exclude_resolved_date):
                    jql_query += f" AND (resolved IS EMPTY OR resolved >= '{exclude_resolved_date}')"

            jql_query += " ORDER BY issuekey ASC"       
        else:
            raise ValueError("Couldn't build JQL query. No project key or filter defined in YAML configuration file.")
        
        self.jql_query = jql_query

        # Define the maximum search results
        if ExporterConfig.YAML__SEARCH_CRITERIA__MAX_RESULTS in data[ExporterConfig.YAML__SEARCH_CRITERIA]:
            self.max_results = data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__MAX_RESULTS]

        # Check all mandatory attributes    
        match self.__check_mandatory_attribute(data, ExporterConfig.YAML__MANDATORY__DECIMAL_SEPARATOR):
            case ExporterConfig.DECIMAL_SEPARATOR_POINT:
                self.decimal_separator = ExporterConfig.DECIMAL_SEPARATOR_POINT
            case ExporterConfig.DECIMAL_SEPARATOR_COMMA:
                self.decimal_separator = ExporterConfig.DECIMAL_SEPARATOR_COMMA
            case _:
                raise ValueError(f"Please check the value for the attribute {ExporterConfig.YAML__MANDATORY} > {ExporterConfig.YAML__MANDATORY__DECIMAL_SEPARATOR}.")

        self.__standard_issue_field_id_flagged = self.__check_mandatory_attribute(data, ExporterConfig.YAML__MANDATORY__FLAGGED)
        self.logger.debug(f"ID for issue field '{ExporterConfig.ISSUE_FIELD_NAME__FLAGGED}': {self.standard_issue_field_id_flagged}")
            
        # Set up all standard fields that should be exported        
        if ExporterConfig.YAML__STANDARD_FIELDS in data:
            for standard_field_name, shall_export in data[ExporterConfig.YAML__STANDARD_FIELDS].items():
                if standard_field_name in ExporterConfig.STANDARD_ISSUE_FIELDS.keys():
                    if standard_field_name == ExporterConfig.ISSUE_FIELD_NAME__FLAGGED:
                        standard_field_id = self.standard_issue_field_id_flagged
                    else:
                        standard_field_id = ExporterConfig.STANDARD_ISSUE_FIELDS[standard_field_name]
                    self.__standard_issue_fields[standard_field_id] = standard_field_name
                else:
                    self.logger.warning(f"Standard field '{standard_field_name}' with id '{standard_field_id}' is not recognized and will be ignored.")

        # Set up all defined custom fields that should be exported
        if ExporterConfig.YAML__CUSTOM_FIELDS in data and isinstance(data[ExporterConfig.YAML__CUSTOM_FIELDS], dict):
            for custom_field_name, custom_field_id in data[ExporterConfig.YAML__CUSTOM_FIELDS].items():
                if IssueFieldType.check_custom_field_id(custom_field_id):
                    self.__custom_issue_fields[custom_field_id] = custom_field_name
                else:
                    self.logger.warning(f"Custom field ID '{custom_field_id}' for field '{custom_field_name}' is not valid and will be ignored.")

        if ExporterConfig.YAML__MISC in data:
            if ExporterConfig.YAML__MISC__STANDARD_FIELD_PREFIX in data[ExporterConfig.YAML__MISC]:
                self.standard_field_prefix = data[ExporterConfig.YAML__MISC][ExporterConfig.YAML__MISC__STANDARD_FIELD_PREFIX]

            if ExporterConfig.YAML__MISC__CUSTOM_FIELD_PREFIX in data[ExporterConfig.YAML__MISC]:
                self.custom_field_prefix = data[ExporterConfig.YAML__MISC][ExporterConfig.YAML__MISC__CUSTOM_FIELD_PREFIX]
            
            if ExporterConfig.YAML__MISC__ISSUE_FIELD_ID_POSTFIX in data[ExporterConfig.YAML__MISC]:
                self.issue_field_id_postfix = data[ExporterConfig.YAML__MISC][ExporterConfig.YAML__MISC__ISSUE_FIELD_ID_POSTFIX]

            if ExporterConfig.YAML__MISC__STATUS_CATEGORY_PREFIX in data[ExporterConfig.YAML__MISC]:
                self.status_category_prefix = data[ExporterConfig.YAML__MISC][ExporterConfig.YAML__MISC__STATUS_CATEGORY_PREFIX]

            if ExporterConfig.YAML__MISC__TIME_ZONE in data[ExporterConfig.YAML__MISC]:
                self.time_zone = data[ExporterConfig.YAML__MISC][ExporterConfig.YAML__MISC__TIME_ZONE]


        # Set up all workflow-related information.
        if ExporterConfig.YAML__WORKFLOW in data and data[ExporterConfig.YAML__WORKFLOW] is not None:
            self.__workflow = Workflow(data[ExporterConfig.YAML__WORKFLOW], self.logger)

        self.__pretty_print(" ... done.")

        self.logger.debug("YAML configuration file successfully loaded.")


    def __jql_list_of_values(self, issue_field: str, values: list) -> str:
        """
        Build a JQL query fragment from a list of values for a specific Jira issue field.

        Constructs a JQL IN clause like "project IN('KEY1', 'KEY2')" from the provided values.

        :param issue_field: The Jira issue field name (e.g., 'project', 'issuetype')
        :type issue_field: str
        :param values: List of values to include in the IN clause
        :type values: list
        :return: The JQL query fragment, e.g., "issuetype IN('Bug', 'Story')"
        :rtype: str
        """
        jql_query = issue_field + " IN("
        for value in values:
            jql_query += "'" + value + "', "
        jql_query = jql_query[:-2] + ")"
        
        return jql_query


    def __check_mandatory_attribute(self, data: dict, attribute: str) -> str:
        """
        Validate that a mandatory attribute exists in the YAML configuration.

        Checks if the mandatory attribute is present in the Mandatory section
        of the configuration data.

        :param data: The parsed YAML configuration data
        :type data: dict
        :param attribute: The name of the mandatory attribute to check
        :type attribute: str
        :raises ValueError: If the Mandatory section is missing or the attribute is not found
        :return: The value of the mandatory attribute
        :rtype: str
        """
        if ExporterConfig.YAML__MANDATORY in data:
            if attribute in data[ExporterConfig.YAML__MANDATORY]:
                return data[ExporterConfig.YAML__MANDATORY][attribute]
            else:
                raise ValueError(f"Mandatory attribute '{attribute}' is missing in YAML config file.")    
        else:
            raise ValueError(f"Section '{ExporterConfig.YAML__MANDATORY}' is missing in YAML config file.")


    def __check_date(self, date_string: str) -> bool:
        """
        Validate that a date string follows the correct format (YYYY-MM-DD).

        Attempts to parse the date string according to the expected format
        and returns True if successful, False otherwise.

        :param date_string: The date string to validate
        :type date_string: str
        :raises ValueError: If the date format cannot be parsed
        :return: True if the date format is correct, False otherwise
        :rtype: bool
        """
        try:
            datetime.datetime.strptime(str(date_string), "%Y-%m-%d")
            return True
        except (ValueError, TypeError):
            return False


    def __pretty_print(self, message: str) -> None:
        """
        Print a message to the console if pretty print is enabled.

        :param message: The message string to print
        :type message: str
        :return: None
        """
        if self.__shall_pretty_print:
            print(message)


    def __log_attribute(self, section: str, attribute_name: str, value) -> None:
        """
        Log a configuration attribute and its value for debugging purposes.

        Used internally within setter methods to track configuration changes.

        :param section: The YAML section name (e.g., 'Workflow', 'Mandatory')
        :type section: str
        :param attribute_name: The name of the configuration attribute
        :type attribute_name: str
        :param value: The value of the attribute
        :type value: any
        :return: None
        """
        self.logger.debug(f"YAML attribute '{section} > {attribute_name}' has been set to '{str(value)}'.")