# coding: utf8

import datetime
import yaml
import re

from .workflow import Workflow
from ..issue_parser.fields.issue_field_type import IssueFieldType

class ExporterConfig:
    """
    Reads out a YAML configuration file and provides all configuration data
    to the IssueParser class (strong coupling).

    :param yaml_file_location: The file location of the YAML configuration file
    :type yaml_file_location: str
    :param logger: The logger for debugging purposes
    :type logger: object
    :param shall_pretty_print: If true, the configuration parser prints basic information to the console
    :type shall_pretty_print: bool
    """
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

    # Always export
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

    DECIMAL_SEPARATOR_POINT = "Point"
    DECIMAL_SEPARATOR_COMMA = "Comma"

    def __init__(
        self,
        yaml_file_location: str,
        logger: object,
        shall_pretty_print: bool = False
    ):
        self.__logger = logger
        self.__shall_pretty_print = shall_pretty_print
        
        # Porperties for Jira connection
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
        self.__decimal_separator: str = ExporterConfig.DECIMAL_SEPARATOR_COMMA # cannot be empty
        self.__time_zone: str = ""

        # Parse YAML config file to populate all properties
        self.__load_yaml_file(yaml_file_location)

    
    ##################
    ### PROPERTIES ###
    ##################


    @property # Read only
    def logger(
        self
    ) -> object:
        return self.__logger


    # Porperties for Jira connection

    @property
    def domain(
        self
    ) -> str:
        return self.__domain

    @domain.setter
    def domain(
        self,
        value: str
    ):
        if re.match(r"^https://[^/]+\.atlassian\.net$", value):
            self.__domain = value
        else:
            raise ValueError(f"The given domain '{value}' does not fit the pattern 'https://[YOUR-NAME].atlassian.net'. Please check the YAML configuration file.")
        self.__log_attribute(ExporterConfig.YAML__CONNECTION, ExporterConfig.YAML__CONNECTION__DOMAIN, value)


    @property
    def username(
        self
    ) -> str:
        return self.__username

    @username.setter
    def username(
        self,
        value: str
    ):
        self.__username = value
        self.__log_attribute(ExporterConfig.YAML__CONNECTION, ExporterConfig.YAML__CONNECTION__USERNAME, value)


    @property
    def api_token(
        self
    ) -> str:
        return self.__api_token

    @api_token.setter
    def api_token(
        self,
        value: str
    ):
        self.__api_token = value
        self.__log_attribute(ExporterConfig.YAML__CONNECTION, ExporterConfig.YAML__CONNECTION__API_TOKEN, value)


    # Properties for JQL request

    @property
    def jql_query(
        self
    ) -> str:
        return self.__jql_query

    @jql_query.setter
    def jql_query(
        self,
        value: str
    ):
        self.__jql_query = value
        self.logger.debug(f"JQL query generated: {value}")


    @property
    def max_results(
        self
    ) -> int:
        return self.__max_results

    @max_results.setter
    def max_results(
        self,
        value: int
    ):
        self.__max_results = value
        self.__log_attribute(ExporterConfig.YAML__SEARCH_CRITERIA, ExporterConfig.YAML__SEARCH_CRITERIA__MAX_RESULTS, str(value))


    # Properties for issue field export

    @property
    def standard_issue_fields(
        self
    ) -> dict:
        return self.__standard_issue_fields


    @property
    def standard_issue_field_id_flagged(
        self
    ) -> str:
        return self.__standard_issue_field_id_flagged


    @property
    def custom_issue_fields(
        self
    ) -> dict:
        return self.__custom_issue_fields


    @property
    def standard_field_prefix(
        self
    ) -> str:
        return self.__standard_field_prefix

    @standard_field_prefix.setter
    def standard_field_prefix(
        self,
        value: str
    ) -> None:
        self.__standard_field_prefix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__STANDARD_FIELD_PREFIX, str(value))


    @property
    def custom_field_prefix(
        self
    ) -> str:
        return self.__custom_field_prefix

    @custom_field_prefix.setter
    def custom_field_prefix(
        self,
        value: str
    ) -> None:
        self.__custom_field_prefix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__CUSTOM_FIELD_PREFIX, str(value))


    @property
    def issue_field_id_postfix(
        self
    ) -> str:
        return self.__issue_field_id_postfix
    
    @issue_field_id_postfix.setter
    def issue_field_id_postfix(
        self,
        value: str
    ) -> None:
        self.__issue_field_id_postfix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__ISSUE_FIELD_ID_POSTFIX, str(value))


    # Properties for workflow timestamp export

    @property
    def workflow(
        self
    ) -> Workflow:
        return self.__workflow


    @property
    def has_workflow(
        self
    ) -> bool:
        return self.workflow is not None and self.workflow.number_of_statuses > 0


    @property
    def status_category_prefix(
        self
    ) -> str:
        return self.__status_category_prefix
    
    @status_category_prefix.setter
    def status_category_prefix(
        self,
        value: str
    ) -> None:
        self.__status_category_prefix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__STATUS_CATEGORY_PREFIX, str(value))


    # Other properties

    @property
    def decimal_separator(
        self
    ) -> str:
        return self.__decimal_separator
    
    @decimal_separator.setter
    def decimal_separator(
        self,
        value: str
    ) -> None:
        self.__decimal_separator = value
        self.__log_attribute(ExporterConfig.YAML__MANDATORY, ExporterConfig.YAML__MANDATORY__DECIMAL_SEPARATOR, str(value))


    @property
    def time_zone(
        self
    ) -> str:
        return self.__time_zone
    
    @time_zone.setter
    def time_zone(
        self,
        value: str
    ) -> None:
        self.__time_zone = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__TIME_ZONE, str(value))


    ######################
    ### PUBLIC METHODS ###
    ######################


    def __load_yaml_file(
        self,
        file_location: str
    ) -> None:
        """
        Loads the YAML config file from the given location.

        :param file_location: The location of the YAML configuration file
        :type file_location: str

        :raise ValueError: Whenever something is missing or erroneous in the YAML file

        :return: None
        """
        self.logger.debug("Start loading YAML configurtation file.")

        if self.__shall_pretty_print:
            print("Process YAML config file...")

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

        # Ceck all mandatory attributes    
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
        
        if self.__shall_pretty_print:
            print(" ... done.")
        
        self.logger.debug("YAML configuration file successfully loaded.")


    #######################
    ### SUPPORT METHODS ###
    #######################


    def __jql_list_of_values(
        self,
        issue_field: str,
        values: list
    ) -> str:
        """
        Builds the JQL string originating from a list list of values for a certain issue field.

        :param issue_field: The issue field like 'project' or 'issue_types'
        :type issue_field: str
        :param values: The whole list of values like 'Story', 'Bug' for 'issue_types'
        :type values: list

        :return: The JQL like "issuetype IN(TYPE1, TYPE2, ...)"
        :rtype: str
        """
        jql_query = issue_field + " IN("
        for value in values:
            jql_query += "'" + value + "', "
        jql_query = jql_query[:-2] + ")"
        
        return jql_query


    def __check_mandatory_attribute(
        self,
        data: dict,
        attribute: str
    ) -> str:
        """
        Checks if a mandatory attribute inside the YAML configuration
        file is properly set

        :param data: The raw data from the YAML configuration file
        :type data: dict
        :param attribute: The name of the mandatory attribute
        :type attribute: str

        :raise ValueError: If section "Mandatory" or the mandatory attribute is missing

        :return: The value of the attribute
        :rtype: str
        """
        if ExporterConfig.YAML__MANDATORY in data:
            if attribute in data[ExporterConfig.YAML__MANDATORY]:
                return data[ExporterConfig.YAML__MANDATORY][attribute]
            else:
                raise ValueError(f"Mandatory attribute '{attribute}' is missing in YAML config file.")    
        else:
            raise ValueError(f"Section '{ExporterConfig.YAML__MANDATORY}' is missing in YAML config file.")


    def __check_date(
        self,
        date_string: str
    ) -> bool:
        """
        Checks if the date format of a date attribute is correct.
        That means it follows the format YYYY-MM-DD.

        :param date_string: The date string from the YAML configuration file
        :type date_string: str

        :raise ValueError: If the date format is incorrect

        :return: True if the date format is correct, False otherwise
        :rtype: bool
        """
        try:
            datetime.datetime.strptime(str(date_string), "%Y-%m-%d")
            return True
        except (ValueError, TypeError):
            return False
    

    def __log_attribute(
        self,
        section: str,
        attribute_name: str,
        value
    ) -> None:
        """
        Logs a given attribute and its value.
        Is used inside the setter methods.

        :param section: The section of the attribute like "Workflow" or "Mandatory"
        :type section: str
        :param attribute_name: The name of the attribute
        :type attribute_name: str
        :param value: The value of the given attribute
        :type value: any

        :return: None
        """
        self.logger.debug(f"YAML attribute '{section} > {attribute_name}' has been set to '{str(value)}'.")