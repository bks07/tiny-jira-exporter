# coding: utf8

import datetime
import yaml
import re

from .standard_issue_field import StandardIssueField
from .custom_issue_field import CustomIssueField
from .custom_issue_field_flagged import CustomIssueFieldFlagged
from .workflow import Workflow

class ExporterConfig:
    """
    Reads out a YAML configuration file and provides all configuration date
    to the IssueParser class (strong coupling).

    :param yaml_file_location: The file location of the YAML configuration file
    :type yaml_file_location: str
    :param logger: The logger for debugging purposes
    :type logger: object
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
    YAML__MISC__STATUS_CATEGORY_PREFIX = "Status Category Prefix"
    YAML__MISC__TIME_ZONE = "Time Zone"

    ISSUE_FIELD_NAME_ISSUE_KEY = "Key"
    ISSUE_FIELD_NAME_ISSUE_ID = "ID"
    ISSUE_FIELD_NAME_ISSUE_TYPE = "Type"
    ISSUE_FIELD_NAME_SUMMARY = "Summary"
    ISSUE_FIELD_NAME_REPORTER = "Reporter"
    ISSUE_FIELD_NAME_ASSIGNEE = "Assignee"
    ISSUE_FIELD_NAME_STATUS = "Status"
    ISSUE_FIELD_NAME_RESOLUTION = "Resolution"
    ISSUE_FIELD_NAME_PRIORITY = "Priority"
    ISSUE_FIELD_NAME_CREATED = "Created"
    ISSUE_FIELD_NAME_UPDATED = "Updated"
    ISSUE_FIELD_NAME_RESOLVED = "Resolved"
    ISSUE_FIELD_NAME_LABELS = "Labels"
    ISSUE_FIELD_NAME_PARENT = "Parent"
    ISSUE_FIELD_NAME_FLAGGED = "Flagged"

    DECIMAL_SEPARATOR_POINT = "Point"
    DECIMAL_SEPARATOR_COMMA = "Comma"

    def __init__(self, yaml_file_location: str, logger: object, shall_pretty_print: bool = False):
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
        self.__issue_fields: dict = {
            ExporterConfig.ISSUE_FIELD_NAME_ISSUE_KEY: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_ISSUE_KEY, "key", True, True),
            ExporterConfig.ISSUE_FIELD_NAME_ISSUE_ID: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_ISSUE_ID, "id", True, True),
            ExporterConfig.ISSUE_FIELD_NAME_ISSUE_TYPE: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_ISSUE_TYPE, "issuetype"),
            ExporterConfig.ISSUE_FIELD_NAME_REPORTER: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_REPORTER, "reporter"),
            ExporterConfig.ISSUE_FIELD_NAME_ASSIGNEE: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_ASSIGNEE, "assignee"),
            ExporterConfig.ISSUE_FIELD_NAME_SUMMARY: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_SUMMARY, "summary"),
            ExporterConfig.ISSUE_FIELD_NAME_STATUS: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_STATUS, "status"),
            ExporterConfig.ISSUE_FIELD_NAME_RESOLUTION: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_RESOLUTION, "resolution"),
            ExporterConfig.ISSUE_FIELD_NAME_PRIORITY: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_PRIORITY, "priority"),
            ExporterConfig.ISSUE_FIELD_NAME_CREATED: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_CREATED, "created"),
            ExporterConfig.ISSUE_FIELD_NAME_UPDATED: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_UPDATED, "updated"),
            ExporterConfig.ISSUE_FIELD_NAME_RESOLVED: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_RESOLVED, "resolved"),
            ExporterConfig.ISSUE_FIELD_NAME_LABELS: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_LABELS, "labels"),
            ExporterConfig.ISSUE_FIELD_NAME_PARENT: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_PARENT, "parent"),
            ExporterConfig.ISSUE_FIELD_NAME_ASSIGNEE: StandardIssueField(ExporterConfig.ISSUE_FIELD_NAME_ASSIGNEE, "assignee"),
            ExporterConfig.ISSUE_FIELD_NAME_FLAGGED: CustomIssueFieldFlagged() # It's a locked custom field that must be defined inside the YAML config file
        }
        self.__standard_field_prefix: str = ""
        self.__custom_field_prefix: str = ""

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
    def logger(self) -> object:
        return self.__logger

    # Porperties for Jira connection

    @property
    def domain(self) -> str:
        return self.__domain

    @domain.setter
    def domain(self, value: str):
        if re.match(r"^https://[\w]+\.atlassian\.net$", value):
            self.__domain = value
        else:
            print("LOL!")
            raise ValueError(f"The given domain '{value}' does not fit the pattern 'https://[YOUR-NAME].atlassian.net'. Please check the YAML configuration file.")
        self.__log_attribute(ExporterConfig.YAML__CONNECTION, ExporterConfig.YAML__CONNECTION__DOMAIN, value)

    @property
    def username(self) -> str:
        return self.__username

    @username.setter
    def username(self, value: str):
        self.__username = value
        self.__log_attribute(ExporterConfig.YAML__CONNECTION, ExporterConfig.YAML__CONNECTION__USERNAME, value)
        

    @property
    def api_token(self) -> str:
        return self.__api_token

    @api_token.setter
    def api_token(self, value: str):
        self.__api_token = value
        self.__log_attribute(ExporterConfig.YAML__CONNECTION, ExporterConfig.YAML__CONNECTION__API_TOKEN, value)

    # Properties for JQL request

    @property
    def jql_query(self) -> str:
        return self.__jql_query

    @jql_query.setter
    def jql_query(self, value: str):
        self.__jql_query = value
        self.logger.debug(f"JQL query generated: {value}")

    @property
    def max_results(self) -> int:
        return self.__max_results

    @max_results.setter
    def max_results(self, value: int):
        self.__max_results = value
        self.__log_attribute(ExporterConfig.YAML__SEARCH_CRITERIA, ExporterConfig.YAML__SEARCH_CRITERIA__MAX_RESULTS, str(value))

    # Properties for issue field export
    @property
    def issue_fields(self) -> dict:
        return self.__issue_fields

    @property
    def fields_to_fetch(self) -> list:
        return_fields: list = []
        for field in self.issue_fields.values():
            if field.shall_fetch:
                return_fields.append(field.id)
        return return_fields

    @property
    def standard_field_prefix(self) -> str:
        return self.__standard_field_prefix

    @standard_field_prefix.setter
    def standard_field_prefix(self, value: str) -> None:
        self.__standard_field_prefix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__STANDARD_FIELD_PREFIX, str(value))

    @property
    def custom_field_prefix(self) -> str:
        return self.__custom_field_prefix

    @custom_field_prefix.setter
    def custom_field_prefix(self, value: str) -> None:
        self.__custom_field_prefix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__STANDARD_FIELD_PREFIX, str(value))

    # Workflow timestamp export

    @property
    def workflow(self) -> Workflow:
        return self.__workflow

    @property
    def status_category_prefix(self) -> str:
        return self.__status_category_prefix
    
    @status_category_prefix.setter
    def status_category_prefix(self, value: str) -> None:
        self.__status_category_prefix = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__STATUS_CATEGORY_PREFIX, str(value))
    
    # Other properties

    @property
    def decimal_separator(self) -> str:
        return self.__decimal_separator
    
    @decimal_separator.setter
    def decimal_separator(self, value: str) -> None:
        self.__decimal_separator = value
        self.__log_attribute(ExporterConfig.YAML__MANDATORY, ExporterConfig.YAML__MANDATORY__DECIMAL_SEPARATOR, str(value))

    @property
    def time_zone(self) -> str:
        return self.__time_zone
    
    @time_zone.setter
    def time_zone(self, value: str) -> None:
        self.__time_zone = value
        self.__log_attribute(ExporterConfig.YAML__MISC, ExporterConfig.YAML__MISC__TIME_ZONE, str(value))


    ######################
    ### PUBLIC METHODS ###
    ######################


    def has_workflow(self) -> bool:
        return self.workflow is not None and self.workflow.number_of_statuses > 0


    ######################
    ### BUSINESS LOGIC ###
    ######################


    def __load_yaml_file(self, file_location: str):
        """
        Loads the YAML config file from the given location.

        :param file_location: The location of the YAML configuration file
        :type file_location: str

        :raise ValueError: Whenever something is missing or erroneous in the YAML file
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
            jql_query = "filter = '" + data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__FILTER] + "'"
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
        

        self.issue_fields[ExporterConfig.ISSUE_FIELD_NAME_FLAGGED].id = self.__check_mandatory_attribute(data, ExporterConfig.YAML__MANDATORY__FLAGGED)
        self.logger.debug(f"ID for issue field '{ExporterConfig.ISSUE_FIELD_NAME_FLAGGED}': {self.issue_fields[ExporterConfig.ISSUE_FIELD_NAME_FLAGGED].id}")
            
        # Decide for all standard fields
        if ExporterConfig.YAML__STANDARD_FIELDS in data:
            for name, export_to_csv in data[ExporterConfig.YAML__STANDARD_FIELDS].items():
                if name in self.issue_fields.keys():
                    match name:
                        case ExporterConfig.ISSUE_FIELD_NAME_ISSUE_ID | ExporterConfig.ISSUE_FIELD_NAME_ISSUE_KEY:
                            # Always export the issue key and ID to the CSV file
                            self.issue_fields[name].shall_fetch = True
                            self.issue_fields[name].export_to_csv = True
                        case ExporterConfig.ISSUE_FIELD_NAME_SUMMARY | ExporterConfig.ISSUE_FIELD_NAME_STATUS:
                            # Always fetch but export to CSV file is optional
                            self.issue_fields[name].shall_fetch = True
                            self.issue_fields[name].export_to_csv = bool(export_to_csv)
                        case _:
                            # Both, fetching and exporting to CSV file are optional
                            self.issue_fields[name].shall_fetch = bool(export_to_csv) # Only fetch, if issue field should be shown in csv file
                            self.issue_fields[name].export_to_csv = bool(export_to_csv)
                else:
                    raise ValueError(f"Unknown standard issue field '{name}' defined in YAML configuration file.")

        # Set up all defined custom fields
        if ExporterConfig.YAML__CUSTOM_FIELDS in data and isinstance(data[ExporterConfig.YAML__CUSTOM_FIELDS], dict):
            for custom_field_name, custom_field_id in data[ExporterConfig.YAML__CUSTOM_FIELDS].items():
                self.__add_custom_field(custom_field_id, custom_field_name)

        if ExporterConfig.YAML__MISC in data:
            if ExporterConfig.YAML__MISC__STANDARD_FIELD_PREFIX in data[ExporterConfig.YAML__MISC]:
                self.standard_field_prefix = data[ExporterConfig.YAML__MISC][ExporterConfig.YAML__MISC__STANDARD_FIELD_PREFIX]

            if ExporterConfig.YAML__MISC__CUSTOM_FIELD_PREFIX in data[ExporterConfig.YAML__MISC]:
                self.custom_field_prefix = data[ExporterConfig.YAML__MISC][ExporterConfig.YAML__MISC__CUSTOM_FIELD_PREFIX]
            
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


    def __add_custom_field(self, id: str, name: str) -> None:
        if name not in self.issue_fields.keys():
            self.issue_fields[name] = CustomIssueField(name, True, True)
            self.issue_fields[name].id = id
            self.logger.debug(f"Added custom field '{name}' with id '{id}'.")
        else:
            raise ValueError(f"Custom field with redundant name '{name}'. Check your YAML configuration file.")

    def __jql_list_of_values(self, issue_field: str, values: list) -> str:
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
            jql_query += value + ", "
        jql_query = jql_query[:-2] + ")"
        
        return jql_query


    def __check_mandatory_attribute(self, data: dict, attribute: str) -> str:
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ValueError: ...
        """
        if ExporterConfig.YAML__MANDATORY in data:
            if attribute in data[ExporterConfig.YAML__MANDATORY]:
                return data[ExporterConfig.YAML__MANDATORY][attribute]
            else:
                raise ValueError(f"Mandatory attribute '{attribute}' is missing in YAML config file.")    
        else:
            raise ValueError(f"Section '{ExporterConfig.YAML__MANDATORY}' is missing in YAML config file.")


    def __check_date(self, date_string: str) -> bool:
        """...
        ...: ...

        :return bool:
        """
        return bool(datetime.datetime.strptime(str(date_string), "%Y-%m-%d"))
    

    def __log_attribute(self, section: str, attribute_name: str, value) -> None:
        self.logger.debug(f"YAML attribute '{section} > {attribute_name}' has been set to '{str(value)}'.")