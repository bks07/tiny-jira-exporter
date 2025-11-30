# coding: utf8

import datetime
import pytz
import yaml
import re
from typing import Any

from modules.issue_parser.fields.issue_field_type import IssueFieldType
from modules.issue_parser.fields.issue_field_type_date import IssueFieldTypeDate
from modules.issue_parser.fields.issue_field_type_datetime import IssueFieldTypeDatetime

class ExporterConfig:
    """
    Parse and expose exporter configuration from a YAML file.

    ExporterConfig reads a YAML configuration used by the exporter and exposes
    configuration values through properties and helper methods. The class acts
    as a small validation and transformation layer that converts YAML values
    into the shapes expected by the issue parser and exporter code.

    Responsibilities include:
    - Loading connection credentials and JQL/search criteria
    - Selecting and mapping standard and custom issue fields for export
    - Validating mandatory configuration values
    - Building the JQL query used to fetch issues
    - Loading workflow/status definitions used for timestamp and transition exports

    Use the ``load_yaml_file`` method to load a YAML file into an instance and
    use the provided property getters to access parsed values.

    Raises:
        ValueError: when mandatory configuration sections or attributes are missing
    """
    
    # YAML configuration section keys
    YAML__CONNECTION = "Connection"
    YAML__CONNECTION__DOMAIN = "Domain"
    YAML__CONNECTION__USERNAME = "Username"
    YAML__CONNECTION__API_TOKEN = "API Token"
    YAML__CONNECTION__CLOUD = "Cloud"
    YAML__SEARCH_CRITERIA = "Search Criteria"
    YAML__SEARCH_CRITERIA__PROJECTS = "Projects"
    YAML__SEARCH_CRITERIA__ISSUE_TYPES = "Issue Types"
    YAML__SEARCH_CRITERIA__FILTER = "Filter"
    YAML__SEARCH_CRITERIA__EXCLUDE_CREATED_DATE = "Exclude Created Date"
    YAML__SEARCH_CRITERIA__EXCLUDE_RESOLVED_DATE = "Exclude Resolved Date"
    YAML__STANDARD_FIELDS = "Standard Issue Fields"
    YAML__CUSTOM_FIELDS = "Custom Issue Fields"
    YAML__WORKFLOW = "Workflow"
    YAML__MANDATORY = "Mandatory"
    YAML__MANDATORY__FLAGGED = "Flagged Field ID"
    YAML__MISC = "Misc"
    YAML__MISC__CSV_SEPARATOR = "CSV Separator"
    YAML__MISC__STANDARD_FIELD_PREFIX = "Standard Field Prefix"
    YAML__MISC__CUSTOM_FIELD_PREFIX = "Custom Field Prefix"
    YAML__MISC__ISSUE_FIELD_ID_POSTFIX = "Issue Field ID Postfix"
    YAML__MISC__STATUS_CATEGORY_PREFIX = "Status Category Prefix"
    YAML__MISC__TIME_ZONE = "Time Zone"
    YAML__MISC__DATE_FORMAT = "Date Format"
    YAML__MISC__DATETIME_OPTION = "DateTime Option"
    YAML__MISC__DATETIME_FORMAT = "DateTime Format"
    YAML__MISC__DECIMAL_SEPARATOR = "Decimal Separator"
    YAML__MISC__EXPORT_VALUE_IDS = "Export Value IDs"

    # Issue field display names - Always exported
    ISSUE_FIELD_NAME__ISSUE_KEY = "Key"
    ISSUE_FIELD_ID__ISSUE_KEY = "key"
    ISSUE_FIELD_NAME__ISSUE_ID = "ID"
    ISSUE_FIELD_ID__ISSUE_ID = "id"
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
        ISSUE_FIELD_NAME__RESOLVED: "resolutiondate",
        ISSUE_FIELD_NAME__LABELS: "labels",
        ISSUE_FIELD_NAME__COMPONENTS: "components",
        ISSUE_FIELD_NAME__AFFECTED_VERSIONS: "versions",
        ISSUE_FIELD_NAME__FIXED_VERSIONS: "fixVersions"
    }

    DECIMAL_SEPARATOR_POINT = "Point"
    DECIMAL_SEPARATOR_COMMA = "Comma"
    DECIMAL_SEPARATORS = [DECIMAL_SEPARATOR_POINT, DECIMAL_SEPARATOR_COMMA]
    DEFAULT_DECIMAL_SEPARATOR = DECIMAL_SEPARATOR_POINT

    CSV_SEPARATOR_COMMA = "Comma"
    CSV_SEPARATOR_SEMICOLON = "Semicolon"
    CSV_SEPARATORS = [CSV_SEPARATOR_COMMA, CSV_SEPARATOR_SEMICOLON]
    DEFAULT_CSV_SEPARATOR = CSV_SEPARATOR_COMMA

    DEFAULT_DATE_FORMAT = "%Y-%m-%d"
    DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    DATETIME_OPTION_DATE = "Date"
    DATETIME_OPTION_SECONDS = "Seconds"
    DATETIME_OPTION_MILLISECONDS = "Milliseconds"
    DATETIME_OPTIONS = [DATETIME_OPTION_DATE, DATETIME_OPTION_SECONDS, DATETIME_OPTION_MILLISECONDS]
    DEFAULT_DATETIME_OPTION = DATETIME_OPTION_DATE
    
    def __init__(
        self,
        logger: object,
        shall_pretty_print: bool = False
    ):
        """
        Create a new ExporterConfig instance.

        The constructor only sets up internal state and accepts a logger and an
        optional pretty-print flag. Actual configuration values are populated by
        calling `load_yaml_file()` with the path to a YAML configuration.

        Args:
            logger: Logger instance used for debug/info messages.
            shall_pretty_print: When True, human-readable progress messages are
                printed during configuration loading.

        Note:
            This method does not validate or load configuration files; it
            prepares the object to receive configuration data.
        """
        self.__logger = logger
        self.__shall_pretty_print = shall_pretty_print
        
        # Properties for Jira connection
        self.__domain: str = ""
        self.__username: str = ""
        self.__api_token: str = ""
        self.__is_cloud: bool = True

        # Properties for JQL request
        self.__jql_query: str = ""

        # Properties for issue field export
        self.__standard_issue_fields: dict = {}
        self.__custom_issue_fields: dict = {}

        # Mandatory properties
        self.__standard_issue_field_id_flagged: str = ""

        # Workflow timestamp export
        self.__workflow: dict = {}

        # Misc properties
        self.__csv_separator: str = self.CSV_SEPARATOR_COMMA
        self.__standard_field_prefix: str = ""
        self.__custom_field_prefix: str = ""
        self.__issue_field_id_postfix: str = ""
        self.__status_category_prefix: str = ""
        self.__time_zone: str = ""
        self.__date_format: str = IssueFieldTypeDate.DEFAULT_DATE_FORMAT
        self.__datetime_option: str = ExporterConfig.DEFAULT_DATETIME_OPTION
        self.__datetime_format: str = IssueFieldTypeDatetime.DEFAULT_DATETIME_FORMAT
        self.__decimal_separator: str = ExporterConfig.DEFAULT_DECIMAL_SEPARATOR
        self.__export_value_ids: bool = False

    
    ############################
    ### PROPERTIES - GENERAL ###
    ############################


    @property
    def logger(self) -> object:
        """
        Logger instance used for debug and informational messages.

        Returns:
            The logger object configured during initialization.
        """
        return self.__logger


    @property
    def shall_pretty_print(self) -> bool:
        """
        Whether to print human-readable progress messages during config loading.

        Returns:
            True if pretty-printing is enabled, False otherwise.
        """
        return self.__shall_pretty_print
    
    @shall_pretty_print.setter
    def shall_pretty_print(self, value: bool) -> None:
        """
        Set whether to print human-readable progress messages during config loading.

        Args:
            value: True to enable pretty-printing, False to disable it.
        """
        self.__shall_pretty_print = value


    ####################################
    ### PROPERTIES - JIRA CONNECTION ###
    ####################################

    @property
    def domain(self) -> str:
        """
        Jira instance domain URL.

        Returns:
            The base URL for the Jira instance in the format 
            'https://[YOUR-NAME].atlassian.net'.
        """
        return self.__domain

    @domain.setter
    def domain(self, value: str):
        """
        Set the Jira domain URL with validation.

        Args:
            value: The Jira domain URL to set. Must match the pattern
                  'https://[YOUR-NAME].atlassian.net'.

        Raises:
            ValueError: If the domain doesn't match the expected Atlassian pattern.
        """
        if re.match(r"^https://[^/]+\.atlassian\.net$", value):
            self.__domain = value
        else:
            raise ValueError(f"The given domain '{value}' does not fit the pattern 'https://[YOUR-NAME].atlassian.net'. Please check the YAML configuration file.")
        self.__log_attribute(ExporterConfig.YAML__CONNECTION, ExporterConfig.YAML__CONNECTION__DOMAIN, value)


    @property
    def username(self) -> str:
        """
        Jira username for authentication.

        Returns:
            The username or email address used for Jira authentication.
        """
        return self.__username

    @username.setter
    def username(self, value: str):
        """
        Set the Jira username for authentication.

        Args:
            value: The Jira username or email address to use for authentication.
        """
        self.__username = value
        self.__log_attribute(ExporterConfig.YAML__CONNECTION, ExporterConfig.YAML__CONNECTION__USERNAME, value)


    @property
    def api_token(self) -> str:
        """
        Jira API token for secure authentication.

        Returns:
            The API token used for authentication with Jira Cloud instances.
        """
        return self.__api_token

    @api_token.setter
    def api_token(self, value: str):
        """
        Set the Jira API token for authentication.

        Args:
            value: The API token to use for Jira authentication. Should be
                  generated from the Jira user's security settings.
        """
        self.__api_token = value
        self.__log_attribute(ExporterConfig.YAML__CONNECTION, ExporterConfig.YAML__CONNECTION__API_TOKEN, value)


    @property
    def is_cloud(self) -> bool:
        """
        Jira deployment type indicator.

        Returns:
            True if connecting to Jira Cloud (Atlassian-hosted), False for 
            Jira Server or Data Center (self-hosted) instances.
        """
        return self.__is_cloud
    
    @is_cloud.setter
    def is_cloud(self, value: bool) -> None:
        """
        Set the Jira deployment type.

        Args:
            value: True for Jira Cloud instances, False for Server/Data Center.
        """
        self.__is_cloud = value
        self.__log_attribute(ExporterConfig.YAML__CONNECTION, ExporterConfig.YAML__CONNECTION__CLOUD, value)


    ##################################
    ###  PROPERTIES - JQL REQUEST  ###    
    ##################################


    @property
    def jql_query(self) -> str:
        """
        Complete JQL query used to fetch issues from Jira.

        Returns:
            The JQL (Jira Query Language) query string built from the
            configuration's search criteria.
        """
        return self.__jql_query

    @jql_query.setter
    def jql_query(self, value: str):
        """
        Set the JQL query string.

        Args:
            value: The JQL query string to use for fetching issues.
        """
        self.__jql_query = value
        self.logger.debug(f"JQL query generated: {value}")


    #################################
    ### PROPERTIES - ISSUE FIELDS ###
    #################################


    @property
    def standard_issue_fields(self) -> dict:
        """
        Standard Jira fields selected for export.

        Returns:
            Dictionary mapping Jira field IDs to human-readable display names
            for standard fields that should be included in the export.
        """
        return self.__standard_issue_fields

    @standard_issue_fields.setter
    def standard_issue_fields(self, value: dict) -> None:
        """
        Set the standard issue fields for export.

        Args:
            value: A dictionary mapping Jira field IDs to human-readable
                   display names for standard fields.
        """
        self.__standard_issue_fields = value


    @property
    def standard_issue_field_id_flagged(self) -> str:
        """
        Custom field ID used for the flagged field.

        Returns:
            The custom field ID (e.g. 'customfield_10001') that represents
            the flagged status in the Jira instance.
        """
        return self.__standard_issue_field_id_flagged

    @standard_issue_field_id_flagged.setter
    def standard_issue_field_id_flagged(self, value: str) -> None:
        """
        Set the custom field ID for the flagged field.

        Args:
            value: The custom field ID (e.g. 'customfield_10001') to use
                   for the flagged status.
        """
        self.__standard_issue_field_id_flagged = value
        self.__log_attribute(ExporterConfig.YAML__MANDATORY, ExporterConfig.YAML__MANDATORY__FLAGGED, str(value))


    ########################################
    ### PROPERTIES - WORKFLOW DEFINITION ###
    ########################################


    @property
    def workflow(self) -> dict:
        """
        Raw workflow configuration dictionary from YAML.

        Returns:
            Dictionary containing the workflow configuration mapping category 
            names to lists of status names, or empty dict if no workflow 
            is configured.
        """
        return self.__workflow


    @property
    def has_workflow(self) -> bool:
        """
        Whether a valid workflow configuration exists.

        Returns:
            True if a workflow is configured and contains at least one status,
            False otherwise.
        """
        return len(self.workflow) > 0


    ##################################
    ### PROPERTIES - MISC SETTINGS ###
    ##################################

    @property
    def csv_separator(self) -> str:
        """
        CSV separator character used in exports.

        Returns:
            Either 'Comma' or 'Semicolon' depending on the configuration.
        """
        return self.__csv_separator

    @csv_separator.setter
    def csv_separator(self, value: str) -> None:
        """
        Set the CSV separator character used in exports.

        Args:
            value: Either 'Comma' or 'Semicolon' to specify the CSV separator.
        """
        self.__csv_separator = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__CSV_SEPARATOR, str(value))


    @property
    def export_value_ids(self) -> bool:
        """
        Whether to export value IDs alongside display names.

        Returns:
            True if value IDs should be exported, False otherwise.
        """
        return self.__export_value_ids
    
    @export_value_ids.setter
    def export_value_ids(self, value: bool) -> None:
        """
        Set whether to export value IDs alongside display names.

        Args:
            value: True to export value IDs, False otherwise.
        """
        self.__export_value_ids = bool(value)
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__EXPORT_VALUE_IDS, str(value))


    @property
    def custom_issue_fields(self) -> dict:
        """
        Custom Jira fields selected for export.

        Returns:
            Dictionary mapping custom field IDs to human-readable display names
            for custom fields that should be included in the export.
        """
        return self.__custom_issue_fields

    @custom_issue_fields.setter
    def custom_issue_fields(self, value: dict) -> None:
        """
        Set the custom issue fields for export.

        Args:
            value: A dictionary mapping custom field IDs to human-readable
                   display names for custom fields.
        """
        self.__custom_issue_fields = value
        self.__log_attribute(ExporterConfig.YAML__CUSTOM_FIELDS, "Custom Issue Fields", str(value))


    @property
    def standard_field_prefix(self) -> str:
        """
        Prefix applied to standard field names in exports.

        Returns:
            The string prefix prepended to standard field display names
            in the exported data.
        """
        return self.__standard_field_prefix

    @standard_field_prefix.setter
    def standard_field_prefix(self, value: str) -> None:
        """
        Set the prefix for standard field names in exports.

        Args:
            value: The prefix string to prepend to standard field names.
        """
        self.__standard_field_prefix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__STANDARD_FIELD_PREFIX, str(value))


    @property
    def custom_field_prefix(self) -> str:
        """
        Prefix applied to custom field names in exports.

        Returns:
            The string prefix prepended to custom field display names
            in the exported data.
        """
        return self.__custom_field_prefix

    @custom_field_prefix.setter
    def custom_field_prefix(self, value: str) -> None:
        """
        Set the prefix for custom field names in exports.

        Args:
            value: The prefix string to prepend to custom field names.
        """
        self.__custom_field_prefix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__CUSTOM_FIELD_PREFIX, str(value))


    @property
    def issue_field_id_postfix(self) -> str:
        """
        Postfix appended to field IDs in exports.

        Returns:
            The string postfix appended to field identifiers in the
            exported data for additional identification.
        """
        return self.__issue_field_id_postfix
    
    @issue_field_id_postfix.setter
    def issue_field_id_postfix(self, value: str) -> None:
        """
        Set the postfix for field IDs in exports.

        Args:
            value: The postfix string to append to field identifiers.
        """
        self.__issue_field_id_postfix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__ISSUE_FIELD_ID_POSTFIX, str(value))


    @property
    def status_category_prefix(self) -> str:
        """
        Prefix applied to status category field names in exports.

        Returns:
            The string prefix prepended to status category field names
            in the exported data.
        """
        return self.__status_category_prefix
    
    @status_category_prefix.setter
    def status_category_prefix(self, value: str) -> None:
        """
        Set the prefix for status category field names in exports.

        Args:
            value: The prefix string to prepend to status category field names.
        """
        self.__status_category_prefix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__STATUS_CATEGORY_PREFIX, str(value))


    @property
    def decimal_separator(self) -> str:
        """
        Decimal separator character used in CSV exports.

        Returns:
            Either DECIMAL_SEPARATOR_POINT ('.') or DECIMAL_SEPARATOR_COMMA (',')
            depending on the configuration.
        """
        return self.__decimal_separator
    
    @decimal_separator.setter
    def decimal_separator(self, value: str) -> None:
        """
        Set the decimal separator for CSV exports.

        Args:
            value: Must be either DECIMAL_SEPARATOR_POINT or DECIMAL_SEPARATOR_COMMA.

        Raises:
            ValueError: If the value is not one of the allowed separator constants.
        """
        if value == ExporterConfig.DECIMAL_SEPARATOR_POINT or \
           value == ExporterConfig.DECIMAL_SEPARATOR_COMMA:
            self.__decimal_separator = value
            self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__DECIMAL_SEPARATOR, str(value))
        else:
            raise ValueError(
                f"Invalid decimal separator. Expected '{ExporterConfig.DECIMAL_SEPARATOR_POINT}' or '{ExporterConfig.DECIMAL_SEPARATOR_COMMA}' for attribute '{ExporterConfig.YAML__MISC__DECIMAL_SEPARATOR}' but '{value}' is given."
            )


    @property
    def time_zone(self) -> str:
        """
        Time zone used for date/time field conversion in exports.

        Returns:
            The time zone string (e.g., 'UTC', 'America/New_York') used to
            convert and format datetime fields in the export.
        """
        return self.__time_zone
    
    @time_zone.setter
    def time_zone(self, value: str) -> None:
        """
        Set the time zone for date/time field conversion.

        Args:
            value: A valid time zone string (e.g., 'UTC', 'Europe/London').
        """
        try:
            target_time_zone = pytz.timezone(value)
        except Exception:
            self.logger.debug(f"Invalid time zone '{value}', falling back to {IssueFieldTypeDatetime.DEFAULT_TIME_ZONE}.")
            target_time_zone = pytz.timezone(IssueFieldTypeDatetime.DEFAULT_TIME_ZONE)
        self.__time_zone = target_time_zone

        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__TIME_ZONE, str(value))


    @property
    def date_format(self) -> str:
        """
        Get the current date output format pattern.

        Returns:
            The strftime-compatible date format string used for CSV export.
        """
        return self.__date_format

    @date_format.setter
    def date_format(self, value: str) -> None:
        """
        Set the date format pattern for exports.

        Args:
            value: A strftime-compatible date format string.

        Raises:
            ValueError: If the provided format string is invalid.
        """
        try:
            # Test the format string by formatting the current date
            datetime.datetime.now().strftime(value)
        except Exception as e:
            raise ValueError(f"Invalid date format string: {value}") from e

        self.__date_format = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__DATE_FORMAT, str(value)) 


    @property
    def datetime_format(self) -> str:
        """
        Get the current datetime output format pattern.

        Returns:
            The strftime-compatible datetime format string used for CSV export.
        """
        return self.__datetime_format
    
    @datetime_format.setter
    def datetime_format(self, value: str) -> None:
        """
        Set the datetime format pattern for exports.

        Args:
            value: A strftime-compatible datetime format string.

        Raises:
            ValueError: If the provided format string is invalid.
        """
        try:
            # Test the format string by formatting the current datetime
            datetime.datetime.now().strftime(value)
        except Exception as e:
            raise ValueError(f"Invalid datetime format string: {value}") from e

        self.__datetime_format = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__DATETIME_FORMAT, str(value))


    @property
    def datetime_option(self) -> str:
        """
        Get the current datetime option (Date or DateTime).

        Returns:
            The datetime option string, either 'Date' or 'DateTime'.
        """
        return self.__datetime_option
    
    @datetime_option.setter
    def datetime_option(self, value: str) -> None:
        """
        Set the datetime option for exports.

        Args:
            value: Must be either 'Date' or 'DateTime'.
        Raises:
            ValueError: If the value is not one of the allowed options.
        """
        if value in ExporterConfig.DATETIME_OPTIONS:
            self.__datetime_option = value
            self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__DATETIME_OPTION, str(value))
        else:
            raise ValueError(
                f"Invalid datetime option. Expected '{ExporterConfig.DATETIME_OPTION_DATE}' or '{ExporterConfig.DATETIME_OPTION_DATETIME}' for attribute '{ExporterConfig.YAML__MISC__DATETIME_OPTION}' but '{value}' is given."
            )


    ######################
    ### PUBLIC METHODS ###
    ######################


    def load_yaml_file(self, file_location: str) -> None:
        """
        Load and validate configuration values from a YAML file.

        After calling this method the instance properties (for example
        `domain`, `jql_query`, `standard_issue_fields`) are
        populated and validated. The method performs the following high-level
        steps:
        1. Parse the YAML file into a Python dictionary
        2. Validate presence of mandatory sections and attributes
        3. Populate connection, search criteria, field and workflow settings

        Args:
            file_location: Path to the YAML configuration file to load.

        Raises:
            ValueError: If mandatory sections or attributes are missing or invalid.
        """
        self.logger.debug("Start loading YAML configuration file.")

        self.__pretty_print("Process YAML config file...")

        # Open the YAML file in read mode
        with open(file_location, "r") as file:
            # Parse the contents using safe_load()
            data = yaml.safe_load(file)

        # Set up the Jira access data, this part of the configuration is optional.
        section_connection = self.__get_section(data, ExporterConfig.YAML__CONNECTION, False)
        if section_connection:
            self.domain = self.__get_attribute(section_connection, ExporterConfig.YAML__CONNECTION__DOMAIN, is_mandatory=False)
            self.username = self.__get_attribute(section_connection, ExporterConfig.YAML__CONNECTION__USERNAME, is_mandatory=False)
            self.api_token = self.__get_attribute(section_connection, ExporterConfig.YAML__CONNECTION__API_TOKEN, is_mandatory=False)
            self.is_cloud = self.__get_attribute(section_connection, ExporterConfig.YAML__CONNECTION__CLOUD, is_mandatory=False) or True # Currently default to True - Jira Cloud only

        # Set up the JQL query to retrieve the right issues from Jira.
        section_search_criteria = self.__get_section(data, ExporterConfig.YAML__SEARCH_CRITERIA, True)
        self.jql_query = self.__generate_jql_query(
            filter=self.__get_attribute(section_search_criteria, ExporterConfig.YAML__SEARCH_CRITERIA__FILTER, is_mandatory=False),
            project_keys=self.__get_attribute(section_search_criteria, ExporterConfig.YAML__SEARCH_CRITERIA__PROJECTS, is_list=True, is_mandatory=True),
            issue_types=self.__get_attribute(section_search_criteria, ExporterConfig.YAML__SEARCH_CRITERIA__ISSUE_TYPES, is_list=True, is_mandatory=False),
            exclude_created_date=self.__get_attribute(section_search_criteria, ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_CREATED_DATE, is_mandatory=False),
            exclude_resolved_date=self.__get_attribute(section_search_criteria, ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_RESOLVED_DATE, is_mandatory=False)
        )

        # Check all mandatory attributes
        section_mandatory_attributes = self.__get_section(data, ExporterConfig.YAML__MANDATORY, is_mandatory=True)
        self.standard_issue_field_id_flagged = self.__get_attribute(section_mandatory_attributes, ExporterConfig.YAML__MANDATORY__FLAGGED, is_mandatory=True)

        # Set up all standard fields that should be exported
        section_standard_fields = self.__get_section(data, ExporterConfig.YAML__STANDARD_FIELDS, False)
        if section_standard_fields:
            self.standard_issue_fields = self.__collect_standard_issue_fields(section_standard_fields)

        # Set up all defined custom fields that should be exported
        section_custom_fields = self.__get_section(data, ExporterConfig.YAML__CUSTOM_FIELDS, False)
        if section_custom_fields:
            self.custom_issue_fields = self.__collect_custom_issue_fields(section_custom_fields)

        # Set up all miscellaneous configuration information.
        section_misc = self.__get_section(data, ExporterConfig.YAML__MISC, False)
        if section_misc:
            self.csv_separator = self.__get_attribute(section_misc, ExporterConfig.YAML__MISC__CSV_SEPARATOR, is_mandatory=False) or ExporterConfig.DEFAULT_CSV_SEPARATOR
            self.standard_field_prefix = self.__get_attribute(section_misc, ExporterConfig.YAML__MISC__STANDARD_FIELD_PREFIX, is_mandatory=False) or ""
            self.custom_field_prefix = self.__get_attribute(section_misc, ExporterConfig.YAML__MISC__CUSTOM_FIELD_PREFIX, is_mandatory=False) or ""
            self.issue_field_id_postfix = self.__get_attribute(section_misc, ExporterConfig.YAML__MISC__ISSUE_FIELD_ID_POSTFIX, is_mandatory=False) or ""
            self.status_category_prefix = self.__get_attribute(section_misc, ExporterConfig.YAML__MISC__STATUS_CATEGORY_PREFIX, is_mandatory=False) or ""
            self.time_zone = self.__get_attribute(section_misc, ExporterConfig.YAML__MISC__TIME_ZONE, is_mandatory=False) or IssueFieldTypeDatetime.DEFAULT_TIME_ZONE
            self.date_format = self.__get_attribute(section_misc, ExporterConfig.YAML__MISC__DATE_FORMAT, is_mandatory=False) or IssueFieldTypeDate.DEFAULT_DATE_FORMAT
            self.datetime_option = self.__get_attribute(section_misc, ExporterConfig.YAML__MISC__DATETIME_OPTION, is_mandatory=False) or ExporterConfig.DEFAULT_DATETIME_OPTION
            self.datetime_format = self.__get_attribute(section_misc, ExporterConfig.YAML__MISC__DATETIME_FORMAT, is_mandatory=False) or IssueFieldTypeDatetime.DEFAULT_DATETIME_FORMAT
            self.export_value_ids = self.__get_attribute(section_misc, ExporterConfig.YAML__MISC__EXPORT_VALUE_IDS, is_mandatory=False) or False
            self.decimal_separator = self.__get_attribute(section_misc, ExporterConfig.YAML__MISC__DECIMAL_SEPARATOR, is_mandatory=False) or ExporterConfig.DEFAULT_DECIMAL_SEPARATOR

        # Set up all workflow-related information.
        self.__workflow = self.__get_section(data, ExporterConfig.YAML__WORKFLOW, False)

        self.__pretty_print("... done.")

        self.logger.debug("YAML configuration file successfully loaded.")


    #######################
    ### PRIVATE METHODS ###
    #######################


    def __get_section(self, data: dict, attribute_name: str, is_mandatory: bool = False) -> dict:
        """
        Return a named top-level section from the parsed YAML or raise.

        Args:
            data: Parsed YAML configuration as a dictionary.
            attribute_name: Top-level section name to retrieve.
            is_mandatory: When True a missing section raises ValueError.

        Returns:
            The value of the requested section (dict) or an empty dict when the
            section is optional and missing.

        Raises:
            ValueError: If the section is mandatory but missing.
        """
        if attribute_name in data:
            return data[attribute_name]
        elif is_mandatory:
            raise ValueError(f"Mandatory top-level attribute '{attribute_name}' is missing in YAML config file.")
        return {}
    

    def __get_attribute(self, section: dict, attribute: str, is_list: bool = False, is_mandatory: bool = False) -> Any:
        """
        Retrieve and validate an attribute value from a YAML section.

        The helper supports optional list-valued attributes through ``is_list``
        and enforces presence when ``is_mandatory`` is True.

        Args:
            section: The dictionary representing the YAML subsection.
            attribute: Attribute name to read from the section.
            is_list: If True the attribute must be a list (or empty list if optional).
            is_mandatory: If True a missing or empty attribute raises ValueError.

        Returns:
            The attribute value. For optional string attributes an empty string
            is returned when the value is missing. For optional list attributes
            an empty list is returned when missing.

        Raises:
            ValueError: When a mandatory attribute is missing or empty.
        """
        return_value = None
        if attribute in section and not is_list:
            if isinstance(section[attribute], str) and len(section[attribute]) > 0:
                return_value = section[attribute]
            elif isinstance(section[attribute], bool):
                return_value = section[attribute]
            else:
                if is_mandatory:
                    raise ValueError(f"Mandatory attribute '{attribute}' is missing or empty in section '{section}' of YAML config file.")
                else:
                    return_value = ""

        if attribute in section and is_list:
            if isinstance(section[attribute], list):
                if len(section[attribute]) > 0:
                    return_value = section[attribute]
                elif not is_mandatory:
                    raise ValueError(f"Mandatory list attribute '{attribute}' is empty in section '{section}' of YAML config file.")
                else:
                    return_value = []
        if attribute == ExporterConfig.YAML__MISC__EXPORT_VALUE_IDS:
            print(return_value)
        return return_value


    def __jql_list_of_values(self, issue_field: str, values: list) -> str:
        """
        Create a JQL IN(...) fragment for the given field and values.

        Example: ``__jql_list_of_values('project', ['ABC', 'XYZ'])`` ->
        ``"project IN('ABC', 'XYZ')"``.

        Args:
            issue_field: Jira field name to search (e.g. 'project').
            values: Iterable of string values to include in the IN clause.

        Returns:
            A string containing the JQL fragment.
        """
        jql_query = issue_field + " IN("
        for value in values:
            jql_query += "'" + value + "', "
        jql_query = jql_query[:-2] + ")"
        
        return jql_query


    def __generate_jql_query(self, filter: str = "", project_keys: list = [], issue_types: list = [], exclude_created_date: str = "", exclude_resolved_date: str = "") -> str:
        """
        Build the full JQL query used to fetch issues.

        The method either returns a filter-based query (when ``filter`` is
        provided) or constructs a query using the supplied project keys,
        optional issue types and optional created/resolved date filters.

        Args:
            filter: Optional saved filter name or ID.
            project_keys: List of project keys to include (required when filter is empty).
            issue_types: Optional list of issue types to include.
            exclude_created_date: Optional 'created' cutoff date (YYYY-MM-DD) to include only newer issues.
            exclude_resolved_date: Optional 'resolved' cutoff date (YYYY-MM-DD) to include newer resolved issues.

        Returns:
            The complete JQL query string.

        Raises:
            ValueError: If neither a filter nor at least one project key is provided.
        """
        jql_query = ""
        if filter is not None and len(filter) > 0:
            # Creates a query where it selects the given filter
            jql_query = "filter = '" + filter + "'"
        else:
            # Creates a default JQL query like "project IN(PKEY1, PKEY2) ORDER BY issuekey ASC"
            if len(project_keys) == 0:
                raise ValueError("At least one project key must be specified in the YAML configuration file under 'Search Criteria > Projects' when no filter is provided.")
            jql_query = self.__jql_list_of_values("project", project_keys)
            
            # Issue types to include
            if len(issue_types) > 0:
                jql_query += " AND " + self.__jql_list_of_values("issuetype", issue_types)

            # Issues created after a certain date
            if exclude_created_date is not None and self.__check_date(exclude_created_date):
                jql_query += f" AND created >= '{exclude_created_date}'"
            # Issues resolved after a certain date
            if exclude_resolved_date is not None and self.__check_date(exclude_resolved_date):
                jql_query += f" AND (resolved IS EMPTY OR resolved >= '{exclude_resolved_date}')"

            jql_query += " ORDER BY created ASC"

        return jql_query


    def __collect_standard_issue_fields(self, section_standard_fields: dict) -> dict:
        """
        Convert YAML selection of standard fields into internal mapping.

        The YAML section maps display names to booleans. This method translates
        the selection into a dictionary that maps Jira field IDs to the human
        readable display name used in exports.

        Args:
            section_standard_fields: Mapping from display name -> bool (export flag).

        Returns:
            A dict mapping Jira field id -> display name for fields that should be exported.
        """
        standard_issue_fields = {}
        for standard_field_name, shall_export in section_standard_fields.items():
            if standard_field_name in ExporterConfig.STANDARD_ISSUE_FIELDS.keys():
                if standard_field_name == ExporterConfig.ISSUE_FIELD_NAME__FLAGGED:
                    standard_field_id = self.standard_issue_field_id_flagged
                else:
                    standard_field_id = ExporterConfig.STANDARD_ISSUE_FIELDS[standard_field_name]
                
                if shall_export:
                    standard_issue_fields[standard_field_id] = standard_field_name
                    self.logger.debug(f"Standard field '{standard_field_name}' with id '{standard_field_id}' has been selected for export.")
                else:
                    self.logger.debug(f"Standard field '{standard_field_name}' with id '{standard_field_id}' has NOT been selected for export.")
            else:
                self.logger.warning(f"Standard field '{standard_field_name}' with id '{standard_field_id}' is not recognized and will be ignored.")

        return standard_issue_fields


    def __collect_custom_issue_fields(self, section_custom_fields: dict) -> dict:
        """
        Validate and return custom fields to export.

        The YAML custom fields section maps display names to custom field IDs
        (e.g. 'My Field': 'customfield_10010'). This method validates each ID
        using IssueFieldType and returns a mapping of valid custom field IDs to
        their display names.

        Args:
            section_custom_fields: Mapping from display name -> custom field id.

        Returns:
            Dict of custom field id -> display name for valid custom fields.
        """
        custom_issue_fields = {}
        for custom_field_name, custom_field_id in section_custom_fields.items():
            if IssueFieldType.check_custom_field_id(custom_field_id):
                custom_issue_fields[custom_field_id] = custom_field_name
                self.logger.debug(f"Custom field '{custom_field_name}' with id '{custom_field_id}' has been selected for export.")
            else:
                self.logger.warning(f"Custom field ID '{custom_field_id}' for field '{custom_field_name}' is not valid and will be ignored.")
        return custom_issue_fields


    def __check_date(self, date_string: str) -> bool:
        """
        Check whether a string is a valid date in YYYY-MM-DD format.

        Returns True when the string can be parsed as a date in the expected
        format, otherwise False.

        Args:
            date_string: Date string to validate.

        Returns:
            True if valid, False otherwise.
        """
        try:
            datetime.datetime.strptime(str(date_string), "%Y-%m-%d")
            return True
        except (ValueError, TypeError):
            return False


    def __pretty_print(self, message: str) -> None:
        """
        Print a user-friendly progress message when pretty-printing is enabled.

        This is a convenience helper used during configuration loading to
        provide minimal, optional console output when the user requests it.
        """
        if self.shall_pretty_print:
            print(message)


    def __log_attribute(self, section: str, attribute_name: str, value) -> None:
        """
        Debug-log a configuration attribute change.

        Intended for internal use by property setters; formats and forwards a
        readable debug message to the configured logger.
        """
        self.logger.debug(f"YAML attribute '{section} > {attribute_name}' has been set to '{str(value)}'.")