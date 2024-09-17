# coding: utf8

import datetime
import yaml

from issue_field import IssueField
from custom_issue_field import CustomIssueField
from custom_issue_field_parent import CustomIssueFieldParent
from custom_issue_field_flagged import CustomIssueFieldFlagged
from workflow import Workflow

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
    YAML__MANDATORY__PARENT = "Parent Field ID"
    YAML__MANDATORY__FLAGGED = "Flagged Field ID"
    YAML__MANDATORY__DECIMAL_SEPARATOR = "Decimal Separator"
    YAML__MISC = "Misc"
    YAML__MISC__STANDARD_FIELD_PREFIX = "Standard Field Prefix"
    YAML__MISC__CUSTOM_FIELD_PREFIX = "Custom Field Prefix"
    YAML__MISC__STATUS_CATEGORY_PREFIX = "Status Category Prefix"
    YAML__MISC__TIME_ZONE = "Time Zone"
    
    ISSUE_FIELD_NAME_PARENT = "Parent"
    ISSUE_FIELD_NAME_FLAGGED = "Flagged"

    DECIMAL_SEPARATOR_POINT = "Point"
    DECIMAL_SEPARATOR_COMMA = "Comma"

    def __init__(self, yaml_file_location: str, logger: object):
        self.__logger = logger
        
        # Porperties for Jira connection
        self.__domain: str = ""
        self.__username: str = ""
        self.__api_token: str = ""

        # Properties for JQL request
        self.__jql_query: str = ""
        self.__max_results: int = 100

        # Properties for issue field export
        self.__fields_to_fetch: list = []
        self.__default_fields = {
            # Always show in csv export
            "issueID": "id",
            "issueKey": "key",
            "issueType": "issuetype"
        }
        self.__standard_fields: dict = {
            "Summary": "summary",
            "Reporter": "reporter",
            "Assignee": "assignee",
            "Summary": "summary",
            "Status": "status",
            "Resolution": "resolution",
            "Priority": "priority",
            "Created": "created",
            "Resolved": "resolved",
            self.ISSUE_FIELD_NAME_PARENT: "", # it's a custom field that must be defined inside the YAML config file
            "Labels": "labels",
            self.ISSUE_FIELD_NAME_FLAGGED: "" # it's a custom field that must be defined inside the YAML config file
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
    ### Properties ###
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
        self.__domain = value

    @property
    def username(self) -> str:
        return self.__username

    @username.setter
    def username(self, value: str):
        self.__username = value

    @property
    def api_token(self) -> str:
        return self.__api_token

    @api_token.setter
    def api_token(self, value: str):
        self.__api_token = value

    # Properties for JQL request

    @property
    def jql_query(self) -> str:
        return self.__jql_query

    @property
    def max_results(self) -> int:
        return self.__max_results

    # Properties for issue field export

    @property
    def fields_to_fetch(self) -> list:
        return self.__fields_to_fetch

    @property
    def standard_field_flagged(self) -> CustomIssueFieldFlagged:
        return self.__standard_field_flagged

    @property
    def standard_field_parent(self) -> CustomIssueFieldParent:
        return self.__standard_field_parent

    @property
    def standard_field_prefix(self) -> str:
        return self.__standard_field_prefix

    @property
    def custom_field_prefix(self) -> str:
        return self.__custom_field_prefix

    # Workflow timestamp export

    @property
    def workflow(self) -> Workflow:
        return self.__workflow

    @property
    def status_category_prefix(self) -> str:
        return self.__status_category_prefix
    
    # Other properties

    @property
    def decimal_separator(self) -> str:
        return self.__decimal_separator

    @property
    def time_zone(self) -> str:
        return self.__time_zone


    ######################
    ### Public methods ###
    ######################


    def has_workflow(self) -> bool:
        return self.workflow is not None and self.workflow.numberOfStatuses() > 0


    ######################
    ### Business logic ###
    ######################


    def __load_yaml_file(self, file_location: str):
        """
        Loads the YAML config file from the given location.

        :param file_location: The location of the YAML configuration file
        :type file_location: str

        :raise ValueError: Whenever something is missing or erroneous in the YAML file
        """
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
                self.__domain = data[ExporterConfig.YAML__CONNECTION][ExporterConfig.YAML__CONNECTION__DOMAIN]

            if ExporterConfig.YAML__CONNECTION__USERNAME in data[ExporterConfig.YAML__CONNECTION]:
                self.__username = data[ExporterConfig.YAML__CONNECTION][ExporterConfig.YAML__CONNECTION__USERNAME]
            
            if ExporterConfig.YAML__CONNECTION__API_TOKEN in data[ExporterConfig.YAML__CONNECTION]:
                self.__api_token = data[ExporterConfig.YAML__CONNECTION][ExporterConfig.YAML__CONNECTION__API_TOKEN]
        

        # Set up the JQL query to retrieve the right issues
        if ExporterConfig.YAML__SEARCH_CRITERIA__FILTER in data[ExporterConfig.YAML__SEARCH_CRITERIA]:
            # Creates a query where it selects the given filter
            self.__jql_query = "filter = '" + data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__FILTER] + "'" 
        elif ExporterConfig.YAML__SEARCH_CRITERIA__PROJECTS in data[ExporterConfig.YAML__SEARCH_CRITERIA] and len(data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__PROJECTS]) > 0:
            # Creates a default JQL query like "project IN(PKEY1, PKEY2) ORDER BY issuekey ASC
            self.__jql_query = self.__jql_list_of_values("project", data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__PROJECTS])

            if ExporterConfig.YAML__SEARCH_CRITERIA__ISSUE_TYPES in data[ExporterConfig.YAML__SEARCH_CRITERIA] and \
                len(data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__ISSUE_TYPES]) > 0:
                self.__jql_query += " AND " + self.__jql_list_of_values("issuetype", data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__ISSUE_TYPES])
            
            # Issues created after a certain date
            if ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_CREATED_DATE in data[ExporterConfig.YAML__SEARCH_CRITERIA]:
                exclude_created_date = data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_CREATED_DATE]
                if self.__check_date(exclude_created_date):
                    self.__jql_query += f" AND created >= '{exclude_created_date}'"
            # Issues resolved after a certain date
            if ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_RESOLVED_DATE in data[ExporterConfig.YAML__SEARCH_CRITERIA]:
                exclude_resolved_date = data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_RESOLVED_DATE]
                if self.__check_date(exclude_resolved_date):
                    self.__jql_query += f" AND (resolved IS EMPTY OR resolved >= '{exclude_resolved_date}')"

            self.__jql_query += " ORDER BY issuekey ASC"       
        else:
            raise ValueError("Couldn't build JQL query. No project key or filter defined in YAML configuration file.")
        
        self.__logger.debug(self.__jql_query)


        # Define the maximum search results
        if ExporterConfig.YAML__SEARCH_CRITERIA__MAX_RESULTS in data[ExporterConfig.YAML__SEARCH_CRITERIA]:
            self.__max_results = data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__MAX_RESULTS]


        # Ceck all mandatory attributes    
        if self.__check_mandatory_field(data, ExporterConfig.YAML__MANDATORY__DECIMAL_SEPARATOR):
            match data[ExporterConfig.YAML__MANDATORY][ExporterConfig.YAML__MANDATORY__DECIMAL_SEPARATOR]:
                case ExporterConfig.DECIMAL_SEPARATOR_POINT:
                    self.__decimal_separator = ExporterConfig.DECIMAL_SEPARATOR_POINT
                case ExporterConfig.DECIMAL_SEPARATOR_COMMA:
                    self.__decimal_separator = ExporterConfig.DECIMAL_SEPARATOR_COMMA
                case _:
                    raise ValueError(f"Please check the value for the attribute {ExporterConfig.YAML__MANDATORY} > {ExporterConfig.YAML__MANDATORY__DECIMAL_SEPARATOR}.")

        if self.__check_mandatory_field(data, ExporterConfig.YAML__MANDATORY__PARENT):
           self.__standard_field_parent = CustomIssueFieldParent()

        if self.__check_mandatory_field(data, ExporterConfig.YAML__MANDATORY__FLAGGED):
            self.__standard_field_flagged = CustomIssueFieldFlagged()
        

        # Set the additional field default field names
        if ExporterConfig.YAML__STANDARD_FIELDS in data:
            for name, id in self.__standard_fields.items():
                if name in self.__always_show_in_export or \
                    (name in data[ExporterConfig.YAML__STANDARD_FIELDS] and \
                    bool(data[ExporterConfig.YAML__STANDARD_FIELDS][name])):
                    match name:
                        case self.ISSUE_FIELD_NAME_PARENT:
                            self.__fields_to_fetch.append(CustomIssueFieldParent(name, id))
                        case self.ISSUE_FIELD_NAME_FLAGGED:
                            self.__fields_to_fetch.append(CustomIssueFieldFlagged(name, id))
                        case _:
                            self.fields_to_fetch.append(self._default_fields_internal_names[key])

        # Set up all defined custom fields
        if ExporterConfig.YAML__CUSTOM_FIELDS in data and isinstance(data[ExporterConfig.YAML__CUSTOM_FIELDS], dict):
            self.custom_fields = dict(data[ExporterConfig.YAML__CUSTOM_FIELDS])
            for custom_field_id in self._custom_fields.values():
                self.__fields_to_fetch.append(custom_field_id)

        if ExporterConfig.YAML__MISC in data:
            if ExporterConfig.YAML__MISC__CUSTOM_FIELD_PREFIX in data[ExporterConfig.YAML__MISC]:
                self.custom_field_prefix = data[ExporterConfig.YAML__MISC][ExporterConfig.YAML__MISC__CUSTOM_FIELD_PREFIX]
            
            if ExporterConfig.YAML__MISC__STATUS_CATEGORY_PREFIX in data[ExporterConfig.YAML__MISC]:
                self.status_category_prefix = data[ExporterConfig.YAML__MISC][ExporterConfig.YAML__MISC__STATUS_CATEGORY_PREFIX]
            
            if ExporterConfig.YAML__MISC__TIME_ZONE in data[ExporterConfig.YAML__MISC]:
                self.time_zone = data[ExporterConfig.YAML__MISC][ExporterConfig.YAML__MISC__TIME_ZONE]


        # Set up all workflow-related information.
        if ExporterConfig.YAML__WORKFLOW in data and data[ExporterConfig.YAML__WORKFLOW] is not None:
            self.__workflow = Workflow(data[ExporterConfig.YAML__WORKFLOW])


    #######################
    ### Support methods ###
    #######################


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

    # GET MANDATORIY VALUE
    def __check_mandatory_field(self, data:dict, field:str):
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ValueError: ...
        """
        if ExporterConfig.YAML__MANDATORY in data:
            if field not in data[ExporterConfig.YAML__MANDATORY]:
                raise ValueError(f"Mandatory attribute '{field}' is missing in YAML config file.")    
        else:
            raise ValueError(f"Section '{ExporterConfig.YAML__MANDATORY}' is missing in YAML config file.")


    def __check_date(self, date_string: str) -> bool:
        """...
        ...: ...

        :return bool:
        """
        return bool(datetime.datetime.strptime(date_string, "%Y-%m-%d"))