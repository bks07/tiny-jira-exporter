# coding: utf8

import datetime
import yaml
import re

from issue_field import IssueField

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
    YAML__DEFAULT_FIELDS = "Default Issue Fields"
    YAML__CUSTOM_FIELDS = "Custom Issue Fields"
    YAML__WORKFLOW = "Workflow"
    YAML__MANDATORY = "Mandatory"
    YAML__MANDATORY__FLAGGED = "Flagged Field ID"
    YAML__MANDATORY__DECIMAL_SEPARATOR = "Decimal Separator"
    YAML__MISC = "Misc"
    YAML__MISC__STATUS_CATEGORY_PREFIX = "Status Category Prefix"
    YAML__MISC__CUSTOM_FIELD_PREFIX = "Custom Field Prefix"
    YAML__MISC__TIME_ZONE = "Time Zone"
    
    DECIMAL_SEPARATOR_POINT = "Point"
    DECIMAL_SEPARATOR_COMMA = "Comma"

    CUSTOM_FIELD_PATTERN = r"^customfield_\d+$"

    def __init__(self, yaml_file_location: str, logger: object):
        self._logger = logger
        
        # Porperties for Jira connection
        self._domain: str = ""
        self._username: str = ""
        self._api_token: str = ""

        # Properties for JQL request
        self._jql_query: str = ""
        self._issue_types: list = []
        self._exclude_created_date: str = ""
        self._exclude_resolved_date: str = ""
        self._max_results: int = 100

        # Properties for default field export
        self._default_fields: list = []
        self._default_fields_internal_names: dict = {
            "issueID": "id",
            "issueKey": "key",
            "issueType": "issuetype",
            "Summary": "summary",
            "Reporter": "reporter",
            "Assignee": "assignee",
            "Summary": "summary",
            "Status": "status",
            "Resolution": "resolution",
            "Priority": "priority",
            "Created": "created",
            "Resolved": "resolved",
            "Labels": "labels",
            "Flagged": "" # it's a custom field that must be defined inside the YAML config file
        }
        self._field_id_flagged: str = ""

        # Custom field export
        self._custom_field_prefix: str = ""
        self._custom_fields: dict = {}

        # List of all fields that should be included in the export
        self._fields_to_fetch: list = [
            IssueField("issueID", "id"), # always required and exported to CSV
            IssueField("issueKey", "key"), # always required and exported to CSV
            IssueField("issuetype", "issueType"), # always required and exported to CSV
            IssueField("Status", "status"), # always required for workflow parser, optional output to CSV
            IssueField("Created", "created"), # always required for workflow parser, optional output to CSV
            IssueField("Summary", "summary") # always required for progress bar, optional output to CSV
        ]

        # Workflow timestamp export
        self._status_category_prefix: str = ""
        self._status_categories: str = []
        self._status_category_mapping: dict = {}        

        # Other properties
        self._decimal_separator: str = ExporterConfig.DECIMAL_SEPARATOR_COMMA # cannot be empty
        self._time_zone: str = ""

        # Parse YAML config file to populate all properties
        self._load_yaml_file(yaml_file_location)

    
    #################################
    ### Setter and getter methods ###
    #################################

    @property # Read only
    def logger(self) -> object:
        return self._logger

    # Porperties for Jira connection

    @property
    def domain(self) -> str:
        return self._domain

    @domain.setter
    def domain(self, value: str):
        self._domain = value

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str):
        self._username = value

    @property
    def api_token(self) -> str:
        return self._api_token

    @api_token.setter
    def api_token(self, value: str):
        self._api_token = value

    # Properties for JQL request

    @property
    def jql_query(self) -> str:
        return self._jql_query

    @jql_query.setter
    def jql_query(self, value: str):
        self._jql_query = value

    @property
    def issue_types(self) -> list:
        return self._issue_types
    
    @issue_types.setter
    def issue_types(self, value: list):
        self._issue_types = value

    @property
    def exclude_created_date(self) -> str:
        return self._exclude_created_date
    
    @exclude_created_date.setter
    def exclude_created_date(self, value: str):
        if bool(datetime.datetime.strptime(value, "%Y-%m-%d")):
            self._exclude_created_date = value
        else:
            raise ValueError("Incorrect date format for exclude created date: {value}")

    @property
    def exclude_resolved_date(self) -> str:
        return self._exclude_resolved_date
    
    @exclude_resolved_date.setter
    def exclude_resolved_date(self, value: str):
        if bool(datetime.datetime.strptime(value, "%Y-%m-%d")):
            self._exclude_resolved_date = value
        else:
            raise ValueError("Incorrect date format for exclude resolved date: {value}")

    @property
    def max_results(self) -> int:
        return self._max_results
    
    @max_results.setter
    def max_results(self, value: int):
        self._max_results = value

    # Properties for default field export

    @property
    def default_fields(self) -> list:
        return self._default_fields

    @default_fields.setter
    def default_fields(self, value: list):
        self._default_fields = value
    
    @property # read only
    def default_fields_internal_names(self) -> dict:
        return self._default_fields_internal_names

    @property
    def field_id_flagged(self) -> str:
        return self._field_id_flagged

    @field_id_flagged.setter
    def field_id_flagged(self, value: str):
        self._field_id_flagged = value

    # Custom field export

    @property
    def custom_field_prefix(self) -> str:
        return self._custom_field_prefix

    @custom_field_prefix.setter
    def custom_field_prefix(self, value: int):
        self._custom_field_prefix = value

    @property
    def custom_fields(self) -> dict:
        return self._custom_fields

    @custom_fields.setter
    def custom_fields(self, value: dict):
        self._custom_fields = value

    # List of all fields that should be included in the export

    @property
    def fields_to_fetch(self) -> list:
        return self._fields_to_fetch

    @fields_to_fetch.setter
    def fields_to_fetch(self, value: list):
        self._fields_to_fetch = value


    # Workflow timestamp export

    @property
    def status_category_prefix(self) -> str:
        return self._status_category_prefix
    
    @status_category_prefix.setter
    def status_category_prefix(self, value: str):
        self._status_category_prefix = value

    @property
    def status_categories(self) -> list:
        return self._status_categories

    @status_categories.setter
    def status_categories(self, value: list):
        self._status_categories = value

    @property
    def status_category_mapping(self) -> dict:
        return self._status_category_mapping

    @status_category_mapping.setter
    def status_category_mapping(self, value: dict):
        self._status_category_mapping = value

    # Other properties

    @property
    def decimal_separator(self) -> str:
        return self._decimal_separator

    @decimal_separator.setter
    def decimal_separator(self, value: str):
        self._decimal_separator = value

    @property
    def time_zone(self) -> str:
        return self._time_zone

    @time_zone.setter
    def time_zone(self, value: str):
        self._time_zone = value


    ######################
    ### Public methods ###
    ######################

      
    def get_status_category_from_status(self, status:str):
        if status not in self._status_category_mapping:
            raise ValueError("Unable to get status category. Status not defined.")
        return self._status_category_mapping[status] # Add 'Category:' as prefix so its not confused with other fields


    def get_custom_field_id(self, custom_field_name:str) -> str:
        if custom_field_name not in self._custom_fields:
            raise ValueError("Custom field does not exist")
        return self._custom_fields[custom_field_name]


    def has_workflow(self) -> bool:
            return len(self._status_categories) > 0
    

    def has_default_fields(self) -> bool:
        return len(self._default_fields) > 0


    def has_custom_fields(self) -> bool:
        return len(self._custom_fields) > 0


    ######################
    ### Business logic ###
    ######################


    def _load_yaml_file(self, file_location: str):
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
            raise ValueError("Mandatory configuarion properties are missing in YAML file.")

        # Set up the Jira access data, this part of the configuration is optional.
        if ExporterConfig.YAML__CONNECTION in data:
            if ExporterConfig.YAML__CONNECTION__DOMAIN in data[ExporterConfig.YAML__CONNECTION]:
                self.domain = data[ExporterConfig.YAML__CONNECTION][ExporterConfig.YAML__CONNECTION__DOMAIN]

            if ExporterConfig.YAML__CONNECTION__USERNAME in data[ExporterConfig.YAML__CONNECTION]:
                self.username = data[ExporterConfig.YAML__CONNECTION][ExporterConfig.YAML__CONNECTION__USERNAME]
            
            if ExporterConfig.YAML__CONNECTION__API_TOKEN in data[ExporterConfig.YAML__CONNECTION]:
                self.api_token = data[ExporterConfig.YAML__CONNECTION][ExporterConfig.YAML__CONNECTION__API_TOKEN]
        

        # Set up the JQL query to retrieve the right issues
        if ExporterConfig.YAML__SEARCH_CRITERIA__FILTER in data[ExporterConfig.YAML__SEARCH_CRITERIA]:
            # Creates a query where it selects the given filter
            jql_query = "filter = '" + data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__FILTER] + "'" 
        elif ExporterConfig.YAML__SEARCH_CRITERIA__PROJECTS in data[ExporterConfig.YAML__SEARCH_CRITERIA] and len(data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__PROJECTS]) > 0:
            # Creates a default JQL query like "project IN(PKEY1, PKEY2) ORDER BY issuekey ASC
            jql_query = self._jql_list_of_values("project", data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__PROJECTS])

            if ExporterConfig.YAML__SEARCH_CRITERIA__ISSUE_TYPES in data[ExporterConfig.YAML__SEARCH_CRITERIA] and \
                len(data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__ISSUE_TYPES]) > 0:
                jql_query += " AND " + self._jql_list_of_values("issuetype", data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__ISSUE_TYPES])
            
            # Issues created after a certain date
            if ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_CREATED_DATE in data[ExporterConfig.YAML__SEARCH_CRITERIA]:
                exclude_created_date = data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_CREATED_DATE]
                if exclude_created_date != None and exclude_created_date != "":
                    jql_query += f" AND created >= '{exclude_created_date}'"
            # Issues resolved after a certain date
            if ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_RESOLVED_DATE in data[ExporterConfig.YAML__SEARCH_CRITERIA]:
                exclude_resolved_date = data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__EXCLUDE_RESOLVED_DATE]
                if exclude_resolved_date != None and exclude_resolved_date != "":
                    jql_query += f" AND (resolved IS EMPTY OR resolved >= '{exclude_resolved_date}')"

            jql_query += " ORDER BY issuekey ASC"       
        else:
            raise ValueError("Couldn't build JQL query. No project key or filter defined in YAML configuration file.")
        
        self._logger.debug(jql_query)
        self._jql_query = jql_query

        # Set up the defined issue types
        if ExporterConfig.YAML__SEARCH_CRITERIA__ISSUE_TYPES in data[ExporterConfig.YAML__SEARCH_CRITERIA]:
            for issue_type in data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__ISSUE_TYPES]:
                self._issue_types.append(issue_type)

        # Define the maximum search results
        if ExporterConfig.YAML__SEARCH_CRITERIA__MAX_RESULTS in data[ExporterConfig.YAML__SEARCH_CRITERIA]:
            self._max_results = data[ExporterConfig.YAML__SEARCH_CRITERIA][ExporterConfig.YAML__SEARCH_CRITERIA__MAX_RESULTS]

        # Ceck all mandatory attributes
        self._set_mandatory_decimal_separator(data)
        field_id_flagged = self._set_mandatory_flagged_field(data)

        # Set the additional field default field names
        if ExporterConfig.YAML__DEFAULT_FIELDS in data:
            for key, value in data[ExporterConfig.YAML__DEFAULT_FIELDS].items():
                if isinstance(value, bool) and value == True:
                    self._default_fields.append(key)
                    match key:
                        case "Flagged":
                            self._default_fields_internal_names[key] = field_id_flagged
                            self._fields_to_fetch.append(field_id_flagged)
                        case _:
                            if key in self._default_fields_internal_names.keys() and key not in self._fields_to_fetch:
                                self._fields_to_fetch.append(self._default_fields_internal_names[key])
                            else:
                                raise ValueError(f"Unknown default field: {key}")

        # Set up all defined custom fields
        if ExporterConfig.YAML__CUSTOM_FIELDS in data and isinstance(data[ExporterConfig.YAML__CUSTOM_FIELDS], dict):
            self._custom_fields = dict(data[ExporterConfig.YAML__CUSTOM_FIELDS])
            for custom_field_id in self._custom_fields.values():
                self._fields_to_fetch.append(custom_field_id)

        if ExporterConfig.YAML__MISC in data:
            if ExporterConfig.YAML__MISC__CUSTOM_FIELD_PREFIX in data[ExporterConfig.YAML__MISC]:
                self._custom_field_prefix = data[ExporterConfig.YAML__MISC][ExporterConfig.YAML__MISC__CUSTOM_FIELD_PREFIX]
            
            if ExporterConfig.YAML__MISC__STATUS_CATEGORY_PREFIX in data[ExporterConfig.YAML__MISC]:
                self._status_category_prefix = data[ExporterConfig.YAML__MISC][ExporterConfig.YAML__MISC__STATUS_CATEGORY_PREFIX]
            
            if ExporterConfig.YAML__MISC__TIME_ZONE in data[ExporterConfig.YAML__MISC]:
                self._time_zone = data[ExporterConfig.YAML__MISC][ExporterConfig.YAML__MISC__TIME_ZONE]

        # Set up all workflow-related information.
        # This must be done at the very end since it requires
        # the misc variable 'category prefix'.
        if ExporterConfig.YAML__WORKFLOW in data:
            self._status_categories = []
            for status_category in data[ExporterConfig.YAML__WORKFLOW]:
                prefixed_status_category = self.get_status_category_prefix() + status_category
                self._status_categories.append(prefixed_status_category)
                for status in data[ExporterConfig.YAML__WORKFLOW][status_category]:
                    self._status_category_mapping[status] = prefixed_status_category


    #######################
    ### Support methods ###
    #######################


    def _jql_list_of_values(self, issue_field: str, values: list) -> str:
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


    def _set_mandatory_flagged_field(self, data: dict) -> str:
        """
        The flagged field is a custom field inside Jira and must be set
        in order to have it present inside the configuration.

        :param data: The whole config data
        :type data: dict

        :raise ValueError: If the issue 

        :return: The field id of the custom field
        :rtype: str
        """
        self._check_mandatory_field(data, ExporterConfig.YAML__MANDATORY__FLAGGED)
        if self._check_custom_field_pattern(data[ExporterConfig.YAML__MANDATORY][ExporterConfig.YAML__MANDATORY__FLAGGED]):
            self._field_id_flagged = data[ExporterConfig.YAML__MANDATORY][ExporterConfig.YAML__MANDATORY__FLAGGED]
            return self._field_id_flagged
        else:
            raise ValueError(f"Please check the value for the attribute {ExporterConfig.YAML__MANDATORY} > {ExporterConfig.YAML__MANDATORY__FLAGGED}.")


    def _set_mandatory_decimal_separator(self, data:dict):
        """
        Checks and sets wheter a point or a comma should be used as
        decimal separator. This is a mandatory attribute inside the
        YAML configuration file.

        Args:
            data (dict) : The whole config data

        Returns:
            void

        Raises:
            ValueError: If not set correct inside the YAML file
        """
        self._check_mandatory_field(data, ExporterConfig.YAML__MANDATORY__DECIMAL_SEPARATOR)
        match data[ExporterConfig.YAML__MANDATORY][ExporterConfig.YAML__MANDATORY__DECIMAL_SEPARATOR]:
            case ExporterConfig.DECIMAL_SEPARATOR_POINT:
                self._decimal_separator = ExporterConfig.DECIMAL_SEPARATOR_POINT
            case ExporterConfig.DECIMAL_SEPARATOR_COMMA:
                self._decimal_separator = ExporterConfig.DECIMAL_SEPARATOR_COMMA
            case _:
                raise ValueError(f"Please check the value for the attribute {ExporterConfig.YAML__MANDATORY} > {ExporterConfig.YAML__MANDATORY__DECIMAL_SEPARATOR}.")

    
    def _check_mandatory_field(self, data:dict, field:str):
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
        

    def _check_custom_field_pattern(self, custom_field_id:str) -> bool:
        """
        Checks if the name 'customfield_xxxxx' is set correct.

        Args:
            name (str)  : The custom field id

        Returns:
            bool: True if the the pattern matches correctly.

        Raises:
            None
        """
        return re.match(self.CUSTOM_FIELD_PATTERN, custom_field_id)