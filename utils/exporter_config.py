# coding: utf8

import yaml

class ExporterConfig:
    YAML__CONNECTION = "Connection"
    YAML__CONNECTION__DOMAIN = "Domain"
    YAML__CONNECTION__USERNAME = "Username"
    YAML__CONNECTION__API_TOKEN = "API Token"
    YAML__SEARCH_CRITERIA = "Search Criteria"
    YAML__SEARCH_CRITERIA__PROJECTS = "Projects"
    YAML__SEARCH_CRITERIA__ISSUE_TYPES = "Issue Types"
    YAML__SEARCH_CRITERIA__FILTER = "Filter"
    YAML__SEARCH_CRITERIA__MAX_RESULTS = "Max Results"
    YAML__WORKFLOW = "Workflow" 
    YAML__CUSTOM_FIELDS = "Custom Fields"
    YAML__MANDATORY = "Additional Mandatory"
    YAML__MANDATORY_FLAGGED = "Flagged Field ID"
    YAML__MISC = "Misc"
    YAML__MISC__STATUS_CATEGORY_PREFIX = "Status Category Prefix"
    YAML__MISC__CUSTOM_FIELD_PREFIX = "Custom Field Prefix"
    YAML__MISC__DECIMAL_SEPARATOR = "Decimal Separator"
    YAML__MISC__TIME_ZONE = "Time Zone"
    
    DECIMAL_SEPARATOR_POINT = "Point"
    DECIMAL_SEPARATOR_COMMA = "Comma"

    def __init__(self, yaml_file_location:str):
        self._domain = ""
        self._username = ""
        self._api_token = ""
        self._jql_query = ""
        self._issue_types = []
        self._max_results = 100
        self._status_categories = []
        self._status_category_mapping = {}
        self._custom_fields = {}
        self._field_id_flagged = ""
        self._custom_field_prefix = ""
        self._status_category_prefix = ""
        self._decimal_separator = self.DECIMAL_SEPARATOR_COMMA # cannot be empty
        self._time_zone = ""

        self._load_yaml_file(yaml_file_location)

    """ Setter and getter methods.
    """

    def set_domain(self, domain:str):
        self._domain = domain
        return None
    
    def set_username(self, username:str):
        self._username = username
        return None
    
    def set_api_token(self, api_token:str):
        self._api_token = api_token
        return None

    def get_domain(self) -> str:
        return self._domain
    
    def get_username(self) -> str:
        return self._username
    
    def get_api_token(self) -> str:
        return self._api_token

    def get_jql_query(self) -> str:
        return self._jql_query

    def get_issue_types(self) -> str:
        return self._issue_types
    
    def get_max_results(self) -> str:
        return self._max_results
    
    def has_workflow(self) -> bool:
        return len(self._status_categories) > 0
    
    def get_status_categories(self) -> list:
        return self._status_categories
        
    def get_status_category_from_status(self, status:str):
        if status not in self._status_category_mapping:
            raise ValueError("Unable to get status category. Status not defined.")
        return self._status_category_mapping[status] # Add 'Category:' as prefix so its not confused with other fields
     
    def get_status_category_mapping(self) -> dict:
        return self._status_category_mapping

    def has_custom_fields(self) -> bool:
        return len(self._custom_fields) > 0

    def get_custom_fields(self) -> dict:
        return self._custom_fields
    
    def get_custom_field_id(self, custom_field_name:str) -> str:
        if custom_field_name not in self._custom_fields:
            raise ValueError("Custom field does not exist")
        return self._custom_fields[custom_field_name]
    
    def get_field_id_flagged(self) -> str:
        return self._field_id_flagged

    def get_custom_field_prefix(self) -> str:
        return self._custom_field_prefix

    def get_status_category_prefix(self) -> str:
        return self._status_category_prefix
    
    def get_decimal_separator(self) -> str:
        return self._decimal_separator
    
    def get_time_zone(self) -> str:
        return self._time_zone

    """ Helper methods.
    """

    def _load_yaml_file(self, file_location:str):
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """
        # Open the YAML file in read mode
        with open(file_location, "r") as file:
            # Parse the contents using safe_load()
            data = yaml.safe_load(file)
        
        # Set up the Jira access data, this part of the configuration is optional.
        if self.YAML__CONNECTION in data:
            if self.YAML__CONNECTION__DOMAIN in data[self.YAML__CONNECTION]:
                self._domain = data[self.YAML__CONNECTION][self.YAML__CONNECTION__DOMAIN]

            if self.YAML__CONNECTION__USERNAME in data[self.YAML__CONNECTION]:
                self._username = data[self.YAML__CONNECTION][self.YAML__CONNECTION__USERNAME]
            
            if self.YAML__CONNECTION__API_TOKEN in data[self.YAML__CONNECTION]:
                self._api_token = data[self.YAML__CONNECTION][self.YAML__CONNECTION__API_TOKEN]

        if self.YAML__SEARCH_CRITERIA not in data:
            raise ValueError("No search criteria defined in YAML config file.")
        
        # Set up the JQL query to retrieve the right issues
        if self.YAML__SEARCH_CRITERIA__PROJECTS in data[self.YAML__SEARCH_CRITERIA] and len(data[self.YAML__SEARCH_CRITERIA][self.YAML__SEARCH_CRITERIA__PROJECTS]) > 0:
            # Creates a default JQL query like "project IN(PKEY1, PKEY2) ORDER BY issuekey ASC
            jql_query = "project IN("
            for project_key in data[self.YAML__SEARCH_CRITERIA][self.YAML__SEARCH_CRITERIA__PROJECTS]:
                jql_query += project_key + ", "
            jql_query = jql_query[:-2]

            jql_query += self._issue_type_jql_string(data)

            jql_query += " ORDER BY issuekey ASC"
        
        elif self.YAML__SEARCH_CRITERIA__FILTER in data[self.YAML__SEARCH_CRITERIA]:
            # Creates a query where it selects the given filter
            jql_query = "filter = '" + data[self.YAML__SEARCH_CRITERIA][self.YAML__SEARCH_CRITERIA__FILTER] + "'"
            jql_query += self._issue_type_jql_string(data)
        
        else:
            raise ValueError("Couldn't build JQL query. No project key or filter defined in YAML configuration file.")
        
        self._jql_query = jql_query

        # Set up the defined issue types
        if self.YAML__SEARCH_CRITERIA__ISSUE_TYPES in data[self.YAML__SEARCH_CRITERIA]:
            for issue_type in data[self.YAML__SEARCH_CRITERIA][self.YAML__SEARCH_CRITERIA__ISSUE_TYPES]:
                self._issue_types.append(issue_type)

        # Define the maximum search results
        if self.YAML__SEARCH_CRITERIA__MAX_RESULTS in data[self.YAML__SEARCH_CRITERIA]:
            self._max_results = data[self.YAML__SEARCH_CRITERIA][self.YAML__SEARCH_CRITERIA__MAX_RESULTS]

        # Set up all defined custom fields
        if self.YAML__CUSTOM_FIELDS in data:
            self._custom_fields = data[self.YAML__CUSTOM_FIELDS]

        if self.YAML__MANDATORY not in data:
            raise ValueError("Mandatory fields missing in YAML file.")

        if self.YAML__MANDATORY_FLAGGED not in data[self.YAML__MANDATORY] or data[self.YAML__MANDATORY][self.YAML__MANDATORY_FLAGGED] == "":
            raise ValueError("Flagged field ID not defined in YAML file.")
        self._field_id_flagged = data[self.YAML__MANDATORY][self.YAML__MANDATORY_FLAGGED]

        if self.YAML__MISC in data:
            if self.YAML__MISC__CUSTOM_FIELD_PREFIX in data[self.YAML__MISC]:
                self._custom_field_prefix = data[self.YAML__MISC][self.YAML__MISC__CUSTOM_FIELD_PREFIX]
            
            if self.YAML__MISC__STATUS_CATEGORY_PREFIX in data[self.YAML__MISC]:
                self._status_category_prefix = data[self.YAML__MISC][self.YAML__MISC__STATUS_CATEGORY_PREFIX]

            if self.YAML__MISC__DECIMAL_SEPARATOR in data[self.YAML__MISC]:
                match data[self.YAML__MISC][self.YAML__MISC__DECIMAL_SEPARATOR]:
                    case self.DECIMAL_SEPARATOR_POINT:
                        self._decimal_separator = self.DECIMAL_SEPARATOR_POINT
                    case _:
                        self._decimal_separator = self.DECIMAL_SEPARATOR_COMMA
            
            if self.YAML__MISC__TIME_ZONE in data[self.YAML__MISC]:
                self._time_zone = data[self.YAML__MISC][self.YAML__MISC__TIME_ZONE]

        # Set up all workflow-related information.
        # This must be done at the very end since it requires
        # the misc variable 'category prefix'.
        if self.YAML__WORKFLOW in data:
            self._status_categories = []
            for status_category in data[self.YAML__WORKFLOW]:
                prefixed_status_category = self.get_status_category_prefix() + status_category
                self._status_categories.append(prefixed_status_category)
                for status in data[self.YAML__WORKFLOW][status_category]:
                    self._status_category_mapping[status] = prefixed_status_category

        return None


    def _issue_type_jql_string(self, data:dict) -> str:
        """...

        Args:
            ...: ...

        Returns:
            ...

        Raises:
            ...: ...
        """
        jql_query = ""
        if self.YAML__SEARCH_CRITERIA in data \
            and self.YAML__SEARCH_CRITERIA__ISSUE_TYPES in data[self.YAML__SEARCH_CRITERIA] \
            and len(data[self.YAML__SEARCH_CRITERIA][self.YAML__SEARCH_CRITERIA__ISSUE_TYPES]) > 0:
            
            jql_query += " AND issuetype IN("
            for issue_type in data[self.YAML__SEARCH_CRITERIA][self.YAML__SEARCH_CRITERIA__ISSUE_TYPES]:
                jql_query += issue_type + ", "
            jql_query = jql_query[:-2] + ")"
        
        return jql_query