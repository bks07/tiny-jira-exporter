# coding: utf8

from atlassian import Jira
import pandas as pd

from modules.exporter_config.exporter_config import ExporterConfig
from modules.issue_parser.workflow import Workflow
from modules.issue_parser.progress_bar import ProgressBar
from .fields.issue_field_type import IssueFieldType
from .fields.issue_field_type_factory import IssueFieldTypeFactory
from .fields.issue_field_type_date import IssueFieldTypeDate

class IssueParser:
    """
    Orchestrates Jira issue fetching, parsing, and CSV export operations.

    This class serves as the main coordinator for the issue export process. It connects
    to Jira instances (Cloud or Server/Data Center), executes JQL queries to fetch
    issues, parses field data according to their types, processes workflow transitions
    for time-in-status analysis, and exports the results to CSV format.

    Key responsibilities:
    - Establishing authenticated connections to Jira instances
    - Dynamically determining field types from Jira schema metadata
    - Fetching issues using configured JQL queries and field selections
    - Parsing complex field types (dates, users, arrays, custom fields)
    - Computing workflow category timestamps from status change history
    - Exporting structured data to CSV with configurable formatting

    The parser supports both standard Jira fields and custom fields, handles various
    field types through a factory pattern, and provides progress feedback during
    long-running operations.

    Args:
        logger: Logger instance for debug and informational messages.
        config: ExporterConfig instance containing all configuration values loaded
               from the YAML configuration file.
        pretty_print: When True, displays user-friendly progress messages during
                     processing operations.

    Example:
        >>> config = ExporterConfig(logger)
        >>> config.load_yaml_file("config.yaml")
        >>> parser = IssueParser(logger, config, pretty_print=True)
        >>> issues = parser.fetch_and_parse_issues()
        >>> parser.export_to_csv(issues, "output.csv")
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
        """
        Logger instance for debug and informational messages.

        Returns:
            The logger object configured during initialization.
        """
        return self.__logger

    @property
    def shall_pretty_print(self) -> bool:
        """
        Whether to display user-friendly progress messages during operations.

        Returns:
            True if pretty-printing is enabled, False otherwise.
        """
        return self.__shall_pretty_print

    @property
    def config(self) -> ExporterConfig:
        """
        Configuration instance containing all export settings and credentials.

        Returns:
            The ExporterConfig object with loaded YAML configuration values.
        """
        return self.__config
    
    @config.setter
    def config(self, value: ExporterConfig) -> None:
        """
        Update the configuration instance.

        Args:
            value: New ExporterConfig instance to use for subsequent operations.
        """
        self.__config = value
    
    @property
    def fields_to_fetch(self) -> dict:
        """
        Mapping of prepared field IDs to their corresponding field type processors.

        Returns:
            Dictionary mapping Jira field IDs to IssueFieldType instances that
            handle parsing and formatting for each field type.
        """
        return self.__fields_to_fetch
    

    ######################
    ### PUBLIC METHODS ###
    ######################

    def fetch_and_parse_issues(self) -> list:
        """
        Execute the complete issue fetching and parsing workflow.

        This method orchestrates the entire process of connecting to Jira, determining
        field types, fetching issues based on the configured JQL query, and parsing
        all field data into structured format ready for export.

        The process includes:
        1. Establishing authenticated connection to the Jira instance
        2. Fetching field schema information to determine proper parsing types
        3. Preparing standard and custom fields based on configuration
        4. Executing JQL query to retrieve matching issues
        5. Parsing all field values using appropriate field type handlers
        6. Processing workflow transitions for time-in-status analysis (if enabled)

        Returns:
            List of dictionaries where each dictionary represents a parsed issue
            with all selected fields and their formatted values.

        Raises:
            ValueError: If JQL query execution fails or returns invalid data.
            ConnectionError: If unable to connect to the Jira instance.

        Note:
            This method displays progress information if pretty_print is enabled.
            Large result sets may take considerable time to process due to API
            rate limits and workflow history requests.
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
        parsed_issues = self.__parse_issues(issues, jira)
        self.__pretty_print("... done.")
        self.logger.info("All fetched issues parsed successfully.")

        return parsed_issues


    def export_to_csv(
        self,
        parsed_issues: list,
        file_location: str
    ) -> None:
        """
        Export parsed issue data to a CSV file with configurable formatting.

        Converts the structured issue data into a pandas DataFrame and writes it
        to a CSV file using semicolon delimiters and UTF-8 encoding. The output
        format is suitable for import into spreadsheet applications and data
        analysis tools.

        Args:
            parsed_issues: List of dictionaries containing parsed issue data as
                          returned by fetch_and_parse_issues().
            file_location: Absolute or relative path where the CSV file should be
                          written, including the filename and .csv extension.

        Raises:
            IOError: If unable to write to the specified file location.
            PermissionError: If insufficient permissions to create the file.

        Note:
            The CSV uses semicolon (;) separators to handle comma-containing field
            values correctly. All text is encoded in UTF-8 to support international
            characters in issue content.
        """
        self.logger.debug("Write CSV file.")

        self.__pretty_print(f"Write CSV output file to '{file_location}'.")
        
        if self.config.csv_separator == ExporterConfig.CSV_SEPARATOR_COMMA:
            csv_separator = ","
        else:
            csv_separator = ";"

        try:
            df = pd.DataFrame.from_dict(parsed_issues)
            df.to_csv(file_location, index=False, sep=csv_separator, encoding="utf-8")
            
            self.__pretty_print(" ... done.")
            
            self.logger.debug("CSV file successfully written.")
        except Exception as error:
            self.logger.critical(error)


    #######################
    ### PRIVATE METHODS ###
    #######################


    def __connect_to_jira(
        self,
        jira_instance = None # Class for mock testing
    ) -> Jira:
        """
        Establish authenticated connection to Jira instance.

        Creates a connection to either Jira Cloud or Server/Data Center instance
        based on the configuration. Uses the configured domain, username, and
        API token/password for authentication.

        Args:
            jira_instance: Optional Jira instance for testing purposes. When
                          provided, this instance is returned instead of
                          creating a new connection.

        Returns:
            Authenticated Jira client instance ready for API operations.

        Note:
            Cloud instances use API tokens while Server instances may use
            passwords. The connection type is determined by the is_cloud
            configuration setting.
        """
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
        """
        Retrieve field schema information from Jira to determine field types.

        Queries Jira's field metadata to build a mapping of field IDs to their
        schema types. This information is essential for creating appropriate
        field type handlers that can correctly parse and format field values.

        Args:
            jira: Authenticated Jira client instance.

        Returns:
            Dictionary mapping field IDs to their schema type strings
            (e.g., 'string', 'datetime', 'array', 'user').
        """
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
        Prepare standard Jira fields for data fetching based on configuration.

        Configures field handlers for built-in Jira fields (status, assignee, created, etc.)
        specified in the configuration. When workflow analysis is enabled, ensures the status
        field is always included even if not explicitly configured.

        Args:
            schema_type_map: Dictionary mapping field IDs to their schema types.
        """
        # Decide for all standard fields
        added_fields = []
        for standard_field_id, standard_field_name in self.config.standard_issue_fields.items():
            self.__prepare_fields_to_fetch(
                schema_type_map,
                standard_field_id,
                standard_field_name,
                fetch_only=False
            )
            added_fields.append(standard_field_name)
        if self.config.has_workflow:
            # Make sure that the status field is always fetched when workflow analysis is enabled
            if not ExporterConfig.ISSUE_FIELD_NAME__STATUS in added_fields:
                self.__prepare_fields_to_fetch(
                    schema_type_map,
                    ExporterConfig.STANDARD_ISSUE_FIELDS[ExporterConfig.ISSUE_FIELD_NAME__STATUS],
                    ExporterConfig.ISSUE_FIELD_NAME__STATUS,
                    fetch_only=True
                )
            # Make sure that the created field is always fetched when workflow analysis is enabled
            if not ExporterConfig.ISSUE_FIELD_NAME__CREATED in added_fields:
                self.__prepare_fields_to_fetch(
                    schema_type_map,
                    ExporterConfig.STANDARD_ISSUE_FIELDS[ExporterConfig.ISSUE_FIELD_NAME__CREATED],
                    ExporterConfig.ISSUE_FIELD_NAME__CREATED,
                    fetch_only=True
                )
        

    def __prepare_custom_fields_to_fetch(self, schema_type_map: dict) -> None:
        """
        Prepare custom Jira fields for data fetching based on configuration.

        Configures field handlers for custom fields (customfield_*) specified
        in the configuration. Custom fields are typically organization-specific
        extensions to the standard Jira schema.

        Args:
            schema_type_map: Dictionary mapping field IDs to their schema types.
        """
        for custom_field_id, custom_field_name in self.config.custom_issue_fields.items():
            self.__prepare_fields_to_fetch(
                schema_type_map,
                custom_field_id,
                custom_field_name,
                fetch_only=False
            )


    def __prepare_fields_to_fetch(
        self,
        schema_type_map: dict,
        field_id: str,
        field_name: str,
        fetch_only: bool
    ) -> None:
        """
        Prepare a single field for fetching from Jira based on its schema type.

        Creates an appropriate field type handler based on the field's schema type
        and adds it to the fields collection. The handler determines how field
        values are parsed and formatted for export.

        Args:
            schema_type_map: Dictionary mapping field IDs to their schema types.
            field_id: Jira field identifier (e.g., 'status', 'customfield_10001').
            field_name: Human-readable field name for export headers.
            fetch_only: If True, field is fetched but excluded from export.
        """
        schema_type = schema_type_map.get(field_id)
        self.logger.debug(f"Prepare field '{field_name}' (ID: {field_id}) with schema type '{schema_type}'.")
        issue_field_type:IssueFieldType = IssueFieldTypeFactory.create_field_type(
            schema_type,
            field_name,
            field_id,
            fetch_only,
            self.logger
        )
        if issue_field_type is None:
            self.logger.debug(f"Skipping field '{field_name}' (ID: {field_id}) due to unknown schema type '{schema_type}'.")
        else:
            self.fields_to_fetch[field_id] = issue_field_type
            self.logger.debug(f"Added field to fetch list with field type class: {issue_field_type.__class__.__name__}. {'' if fetch_only else 'Included in export.'}")
        

    def __fetch_issues(self, jira) -> list:
        """
        Fetch issues from Jira using the configured JQL query.

        Executes the JQL query with the prepared field list to retrieve
        issue data from Jira. Only requests the specific fields that have
        been configured for export to optimize network performance.

        Args:
            jira: Authenticated Jira client instance.

        Returns:
            List of issue dictionaries containing the requested field data.

        Raises:
            ValueError: If the JQL query fails or Jira returns an error.
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


    def __parse_issues(self, issues_response: list, jira: Jira) -> list:
        """
        Parse raw Jira issue data into structured format for export.

        Processes each issue using the configured field type handlers to extract
        and format field values. When workflow analysis is enabled, calculates
        time-in-status information for each issue. Displays progress during
        processing for large datasets.

        Args:
            issues_response: List of raw issue dictionaries from Jira API.
            jira: Authenticated Jira client for additional data fetching.

        Returns:
            List of parsed issue dictionaries ready for CSV export.
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
                    
                    parsed_issue_fields[column_name] = field.value

                    if self.config.export_value_ids and field.has_value_id:
                        parsed_issue_fields[column_name + self.config.issue_field_id_postfix] = field.value_id
                
                # Store the created date for workflow analysis later on
                if field_id_created == id and self.config.has_workflow:
                    issue_created_date = field.value

            
            # If workflow analysis is enabled, parse the status category timestamps
            if self.config.has_workflow:
                category_timestamps = workflow.parse_status_changelog(
                    jira.get_issue_status_changelog(issue_id),
                    issue_created_date
                )
                parsed_issue_fields.update(category_timestamps)
            
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
        """
        Display a progress message to the console if pretty printing is enabled.

        Provides user feedback during long-running operations when the
        shall_pretty_print configuration option is enabled. Used to show
        progress through the main workflow stages.

        Args:
            message: Progress message to display to the user.
        """
        if self.shall_pretty_print:
            print(message)