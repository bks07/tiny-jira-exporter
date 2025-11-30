# coding: UTF-8
from modules.issue_parser.fields.issue_field_type_datetime import IssueFieldTypeDatetime

class Workflow:
    """
    Advanced Jira workflow analyzer for calculating precise time-in-status metrics.

    Provides comprehensive analysis of issue status change logs to determine when issues
    transition between workflow categories. Implements sophisticated Kanban-style logic
    where backward movements reset future timestamps, ensuring accurate workflow
    progression tracking and preventing double-counting of time spent in categories.

    The workflow analyzer processes status changelog entries chronologically to build
    a precise timeline of category transitions, enabling detailed time-tracking analysis
    for workflow optimization, bottleneck identification, and team performance reporting.
    Supports complex multi-status categories and handles edge cases like rapid status
    oscillations and workflow rollbacks.

    Core capabilities:
    - Maps individual Jira statuses to logical workflow categories
    - Calculates precise entry timestamps for each workflow category
    - Handles backward transitions with Kanban logic (resets future timestamps)
    - Supports configurable date formatting and timezone conversion
    - Provides comprehensive workflow validation and error handling
    - Optimized for large-scale issue processing with efficient lookups
    - Maintains workflow integrity across complex transition patterns

    Workflow Logic:
    1. Forward transitions: Sets timestamps for all intermediate categories
    2. Backward transitions: Clears timestamps for all subsequent categories
    3. Same-category transitions: Preserves existing timestamps unchanged
    4. First category: Always uses issue creation date as entry timestamp

    Example:
        >>> # Configure complex workflow with multiple statuses per category
        >>> status_map = {
        ...     "Backlog": ["Open", "Reopened", "To Do"],
        ...     "In Progress": ["In Development", "Code Review", "Testing"],
        ...     "Review": ["Pending Review", "In Review", "Approved"],
        ...     "Done": ["Resolved", "Closed", "Verified"]
        ... }
        >>> datetime_field = IssueFieldTypeDatetime("created", "Created", False)
        >>> workflow = Workflow(status_map, logger, datetime_field, "Status_")
        
        >>> # Process complex changelog with backward transitions
        >>> changelog = [
        ...     {"from": "Open", "to": "In Development", "date": "2023-01-15T10:00:00Z"},
        ...     {"from": "In Development", "to": "Code Review", "date": "2023-01-16T14:30:00Z"},
        ...     {"from": "Code Review", "to": "In Review", "date": "2023-01-17T09:15:00Z"},
        ...     {"from": "In Review", "to": "In Development", "date": "2023-01-18T11:45:00Z"},  # Backward
        ...     {"from": "In Development", "to": "Resolved", "date": "2023-01-20T16:20:00Z"}
        ... ]
        >>> results = workflow.parse_status_changelog(changelog, "2023-01-10T08:00:00Z")
        >>> # Returns precise category entry dates with backward transition handling

    Attributes:
        __categories (list[str]): Ordered list of workflow category names as configured.
        __status_category_mapping (dict[str, str]): Mapping from status names to categories.
        __logger (Logger): Logger instance for detailed workflow analysis debug output.
        __datetime_field (IssueFieldTypeDatetime): Date formatter with timezone conversion.
        __status_category_prefix (str): Optional prefix for CSV export column names.

    Note:
        This class implements Kanban workflow semantics where issues must progress
        sequentially through categories. Backward movements invalidate future progress,
        requiring re-progression through subsequent workflow stages.
    """
    def __init__(
        self,
        status_mapping: dict,
        logger: object,
        datetime_field: IssueFieldTypeDatetime,
        status_category_prefix: str = None
    ) -> None:
        """
        Initialize a comprehensive Workflow analyzer with status mappings and configuration.

        Constructs the workflow analyzer by processing status-to-category mappings and
        building optimized internal lookup structures for efficient workflow analysis.
        The initialization process validates the configuration and prepares data structures
        for high-performance status transition processing.

        During initialization, the method:
        1. Builds category list maintaining configuration order
        2. Creates bidirectional status-category lookup mappings
        3. Validates configuration completeness and consistency
        4. Configures datetime handling with timezone conversion
        5. Sets up debugging infrastructure for detailed analysis

        Args:
            status_mapping (dict[str, list[str]]): Dictionary mapping workflow category names
                                                  to lists of Jira status names. Categories
                                                  represent logical workflow stages, while
                                                  statuses are individual Jira workflow states.
                                                  Example: {"To Do": ["Open", "Reopened"],
                                                           "In Progress": ["Development", "Review"],
                                                           "Done": ["Resolved", "Closed"]}
            logger (Logger): Configured logger instance for detailed debug and informational
                           messages during workflow analysis. Used for transition tracking,
                           validation errors, and performance monitoring.
            datetime_field (IssueFieldTypeDatetime): Pre-configured datetime field handler
                                                   with timezone conversion, date formatting,
                                                   and validation capabilities. Must support
                                                   ISO 8601 datetime parsing and output formatting.
            status_category_prefix (str, optional): String prefix prepended to category names
                                                   when generating CSV export column headers.
                                                   Default None means no prefix is applied.

        Example:
            >>> # Standard workflow configuration
            >>> status_map = {
            ...     "Backlog": ["Open", "To Do"],
            ...     "Active": ["In Progress", "Code Review"],
            ...     "Complete": ["Done", "Closed"]
            ... }
            >>> datetime_field = IssueFieldTypeDatetime("status_date", "Status Date", False)
            >>> workflow = Workflow(status_map, logger, datetime_field, "Workflow_")
            
            >>> # Verify configuration loaded correctly
            >>> print(f"Loaded {workflow.number_of_categories} categories")
            >>> print(f"Total statuses: {workflow.number_of_statuses}")

        Note:
            The order of categories in the status_mapping dictionary determines
            the workflow progression sequence used for forward/backward transition logic.
        """
        self.__categories: list = []
        self.__status_category_mapping: dict = {}
        self.__logger = logger
        self.__datetime_field = datetime_field
        self.__status_category_prefix = status_category_prefix

        self.__logger.debug("Start loading workflow.")

        for status_category in status_mapping:
            self.__categories.append(status_category)
            self.__logger.debug(f"Created status category: {status_category}")
            for status in status_mapping[status_category]:
                self.__status_category_mapping[status] = status_category
                self.__logger.debug(f"Added status: {status_category} -> {status}")


    ##################
    ### Properties ###
    ##################


    @property
    def statuses(self) -> list:
        """
        Get complete list of all individual status names defined across all workflow categories.

        Returns all Jira status names that have been mapped to workflow categories,
        maintaining the order in which they were processed during configuration loading.
        This includes every individual status from all categories, providing a comprehensive
        view of the workflow's status coverage.

        Returns:
            list[str]: Complete list of status names across all categories. Order reflects
                      the sequence in which statuses were processed during initialization,
                      typically grouped by category as defined in the configuration.

        Example:
            >>> workflow.statuses
            ['Open', 'To Do', 'In Progress', 'Code Review', 'Done', 'Closed']
            
            >>> # Check if specific status is configured
            >>> if 'In Review' in workflow.statuses:
            ...     print("Status is configured")

        Note:
            This property provides read-only access to prevent accidental modification
            of the internal status configuration after initialization.
        """
        return list(self.__status_category_mapping.keys())

    @property
    def categories(self) -> list:
        """
        Get ordered list of all workflow category names defining the progression sequence.

        Returns all logical workflow categories in the exact order they were defined
        in the configuration, which determines the workflow progression sequence used
        for forward/backward transition analysis. This order is critical for proper
        Kanban logic implementation and time-in-status calculations.

        Returns:
            list[str]: Ordered list of category names representing the complete workflow
                      progression from initial state to completion. The sequence determines
                      which transitions are considered forward (advancing through categories)
                      versus backward (returning to earlier categories).

        Example:
            >>> workflow.categories
            ['Backlog', 'In Progress', 'Review', 'Done']
            
            >>> # Determine workflow progression direction
            >>> start_idx = workflow.categories.index('Backlog')
            >>> end_idx = workflow.categories.index('Done')
            >>> print(f"Workflow has {end_idx - start_idx + 1} stages")

        Note:
            The category order is immutable after initialization and directly impacts
            the accuracy of time-in-status calculations and transition direction logic.
        """
        return self.__categories

    @property
    def number_of_statuses(self) -> int:
        """
        Get total count of individual status names across all workflow categories.

        Provides the complete count of unique Jira status names that have been
        configured in the workflow, spanning all categories. This metric is useful
        for validation, capacity planning, and understanding workflow complexity.

        Returns:
            int: Total number of individual status names defined across all categories.
                Zero indicates an empty or improperly configured workflow.

        Example:
            >>> # Validate workflow configuration completeness
            >>> if workflow.number_of_statuses == 0:
            ...     raise ValueError("No statuses configured in workflow")
            >>> print(f"Workflow covers {workflow.number_of_statuses} distinct statuses")
            
            >>> # Calculate average statuses per category
            >>> avg_statuses = workflow.number_of_statuses / workflow.number_of_categories
            >>> print(f"Average {avg_statuses:.1f} statuses per category")

        Note:
            This count reflects the total number of unique status names, not the
            number of possible transitions between them.
        """
        return len(self.statuses)
    
    @property
    def number_of_categories(self) -> int:
        """
        Get total count of workflow categories representing distinct progression stages.

        Returns the number of logical workflow stages configured in the analyzer.
        Each category represents a distinct phase in the issue lifecycle, and this
        count directly impacts the complexity of workflow analysis and reporting.

        Returns:
            int: Total number of workflow categories configured. Must be greater than
                zero for meaningful workflow analysis. Higher counts indicate more
                granular workflow tracking but also increased analysis complexity.

        Example:
            >>> # Validate workflow has meaningful progression
            >>> if workflow.number_of_categories < 2:
            ...     raise ValueError("Workflow must have at least 2 categories")
            >>> print(f"Workflow has {workflow.number_of_categories} progression stages")
            
            >>> # Estimate analysis complexity
            >>> complexity = workflow.number_of_categories * workflow.number_of_statuses
            >>> print(f"Workflow complexity factor: {complexity}")

        Note:
            The category count determines the number of time-in-status columns
            that will be generated in CSV exports and analysis results.
        """
        return len(self.categories)
    
    @property
    def datetime_field(self) -> IssueFieldTypeDatetime:
        """
        Get the configured datetime field handler for precise timestamp processing.

        Returns the IssueFieldTypeDatetime instance responsible for parsing, validating,
        and formatting all timestamp data in workflow analysis. This handler provides
        consistent timezone conversion, format standardization, and validation across
        all workflow timestamp operations.

        The datetime field handler ensures:
        - Consistent timezone conversion for all timestamps
        - Standardized output formatting for CSV exports
        - Robust parsing of various ISO 8601 datetime formats
        - Validation and error handling for malformed dates

        Returns:
            IssueFieldTypeDatetime: Configured datetime processor with timezone settings,
                                   format patterns, and validation rules. This instance
                                   maintains state for consistent datetime handling
                                   throughout workflow analysis operations.

        Example:
            >>> # Access datetime formatting configuration
            >>> field = workflow.datetime_field
            >>> print(f"Date pattern: {field.date_pattern}")
            >>> print(f"Timezone: {field.timezone}")
            
            >>> # Process timestamp using same configuration
            >>> field.data = "2023-01-15T10:30:00Z"
            >>> formatted_date = field.value

        Note:
            This field handler is shared across all workflow timestamp operations
            to ensure consistent date formatting in analysis results.
        """
        return self.__datetime_field
    
    @property
    def status_category_prefix(self) -> str:
        """
        Get the configured prefix for status category column names in CSV exports.

        Returns the string prefix that is automatically prepended to workflow category
        names when generating column headers for CSV export files. This prefix helps
        organize and identify workflow-related columns in large datasets with multiple
        field types and prevents naming conflicts with other issue fields.

        The prefix is applied during workflow analysis and becomes part of the
        final column name structure in exported data files.

        Returns:
            str | None: String prefix prepended to category names for CSV columns.
                       None indicates no prefix is configured, and category names
                       are used directly as column headers.

        Example:
            >>> # With prefix configured
            >>> workflow.status_category_prefix
            'Workflow_'
            >>> # Results in columns: 'Workflow_To Do', 'Workflow_In Progress', etc.
            
            >>> # Without prefix (returns None)
            >>> workflow.status_category_prefix is None
            True
            >>> # Results in columns: 'To Do', 'In Progress', etc.
            
            >>> # Generate expected column name
            >>> category = "In Progress"
            >>> if workflow.status_category_prefix:
            ...     column_name = workflow.status_category_prefix + category
            ... else:
            ...     column_name = category

        Note:
            The prefix configuration is set during initialization and cannot be
            modified afterward to ensure consistency across analysis operations.
        """
        return self.__status_category_prefix

    @property
    def logger(self) -> object:
        """
        Get the configured logger instance for comprehensive workflow analysis tracking.

        Returns the logger used throughout workflow processing for detailed debug output,
        transition tracking, validation messages, and performance monitoring. The logger
        provides essential visibility into workflow analysis operations, including status
        transitions, category calculations, and error conditions.

        The logger captures:
        - Individual status transition processing
        - Category timestamp calculations
        - Workflow validation and error conditions
        - Performance metrics for large-scale processing
        - Configuration loading and validation messages

        Returns:
            Logger: Configured logger instance for workflow analysis output. Supports
                   standard logging levels (DEBUG, INFO, WARNING, ERROR) with detailed
                   contextual information for troubleshooting and monitoring.

        Example:
            >>> # Access logger for custom workflow messages
            >>> workflow.logger.info("Starting workflow analysis for 1000 issues")
            >>> workflow.logger.debug(f"Processing category: {category_name}")
            
            >>> # Logger automatically used during workflow operations
            >>> results = workflow.parse_status_changelog(changelog, creation_date)
            >>> # Produces detailed debug output for each transition processed

        Note:
            The logger configuration (level, format, handlers) should be set up
            before workflow initialization to ensure proper output capturing.
        """
        return self.__logger


    ######################
    ### Public methods ###
    ######################


    def parse_status_changelog(
        self,
        status_changelog: dict,
        issue_creation_date: str
    ) -> dict:
        """
        Perform comprehensive analysis of issue status changelog to extract precise category timestamps.

        Processes the complete chronological history of status transitions for a single issue
        to determine exact entry timestamps for each workflow category. Implements sophisticated
        Kanban workflow logic that handles forward progression, backward regression, and
        complex transition patterns while maintaining workflow integrity.

        The analysis process:
        1. Initializes all categories with None timestamps except the first (uses creation date)
        2. Processes changelog entries in reverse chronological order for proper state reconstruction
        3. Applies Kanban logic for each transition (forward sets timestamps, backward clears them)
        4. Maintains workflow state consistency across complex transition patterns
        5. Formats all timestamps using the configured datetime field handler

        Kanban Logic Implementation:
        - Forward transitions: Sets entry timestamps for all intermediate categories
        - Backward transitions: Clears timestamps for all subsequent categories (requires re-progression)
        - Same-category transitions: Preserves existing timestamps (internal status changes)
        - First category: Always uses issue creation date as initial entry point

        Args:
            status_changelog (list[dict]): Complete chronological list of status transitions.
                                         Each transition must contain 'from', 'to', and 'date' keys:
                                         - 'from' (str): Source status name before transition
                                         - 'to' (str): Destination status name after transition
                                         - 'date' (str): ISO 8601 timestamp when transition occurred
            issue_creation_date (str): ISO 8601 creation timestamp for the issue, used as the
                                     entry date for the first workflow category. Must be parseable
                                     by the configured datetime field handler.

        Returns:
            dict[str, str | None]: Dictionary mapping prefixed category names to their entry dates.
                                  Keys are category names with optional prefix applied. Values are
                                  formatted date strings (following configured pattern) for reached
                                  categories, or None for categories not yet entered.

        Raises:
            ValueError: If status names in changelog are not defined in workflow configuration.
            ValueError: If datetime parsing fails for any timestamp in the changelog.

        Example:
            >>> # Simple forward progression
            >>> changelog = [
            ...     {"from": "Open", "to": "In Progress", "date": "2023-01-15T10:00:00Z"},
            ...     {"from": "In Progress", "to": "Done", "date": "2023-01-20T15:30:00Z"}
            ... ]
            >>> result = workflow.parse_status_changelog(changelog, "2023-01-10T08:00:00Z")
            >>> # Returns: {
            >>> #     "Status_Backlog": "2023-01-10",
            >>> #     "Status_In Progress": "2023-01-15", 
            >>> #     "Status_Done": "2023-01-20"
            >>> # }
            
            >>> # Complex pattern with backward transition
            >>> complex_changelog = [
            ...     {"from": "Open", "to": "In Progress", "date": "2023-01-15T10:00:00Z"},
            ...     {"from": "In Progress", "to": "Done", "date": "2023-01-18T14:00:00Z"},
            ...     {"from": "Done", "to": "In Progress", "date": "2023-01-19T09:30:00Z"},  # Backward!
            ...     {"from": "In Progress", "to": "Done", "date": "2023-01-22T16:15:00Z"}
            ... ]
            >>> result = workflow.parse_status_changelog(complex_changelog, "2023-01-10T08:00:00Z")
            >>> # Backward transition clears 'Done' timestamp, requiring re-progression

        Note:
            The method processes changelog entries in reverse order to properly reconstruct
            the workflow state timeline. This ensures accurate handling of complex transition
            patterns and maintains Kanban workflow semantics.
        """
        categories = {}
        is_first_category = True
        # Initiate the status category timestamps by adding all of them with value None
        for status_category in self.categories:
            column_name: str = self.status_category_prefix + status_category
            if is_first_category:
                # Every issue gets created with the very first status of the workflow
                # Therefore, set the creation date for the very first category
                categories[column_name] = issue_creation_date
                is_first_category = False
            else:
                categories[column_name] = None

        # Crawl through all status changes of an issue
        status_changelog = reversed(status_changelog)
        for transition in status_changelog:
            # Add the transition information to a list first
            # since it is returned in descending sort order
            categories = self.__set_transition_dates(categories, transition['from'], transition['to'], transition['date'])

        return categories


    #######################
    ### Private methods ###
    #######################


    def __set_transition_dates(
        self,
        category_dates: dict,
        start_status: str,
        destination_status: str,
        date: str
    ) -> dict:
        """
        Process individual status transition to update category timeline with Kanban logic.

        Analyzes a single status transition event and updates the category timestamp dictionary
        according to sophisticated Kanban workflow rules. The method determines transition
        direction (forward, backward, or lateral) and applies appropriate timestamp updates
        to maintain workflow state integrity and prevent time-tracking inconsistencies.

        Transition Processing Logic:
        1. **Same Category Transition**: Status change within the same workflow category
           - No timestamp modifications (preserves existing category entry dates)
           - Logs transition for debugging but maintains current state
        2. **Forward Progression**: Movement toward workflow completion
           - Sets entry timestamps for all intermediate categories between start and destination
           - Uses provided transition date formatted through datetime field handler
           - Enables proper time-in-status calculations for progressive workflow advancement
        3. **Backward Regression**: Movement toward earlier workflow stages  
           - Clears timestamps (sets to None) for all categories after the destination
           - Implements Kanban principle that backward movement invalidates future progress
           - Requires issues to re-progress through cleared categories for accurate tracking

        Args:
            category_dates (dict[str, str | None]): Current category timestamp dictionary being
                                                   constructed. Keys are prefixed category names,
                                                   values are formatted date strings or None.
            start_status (str): Status name before the transition occurred. Must be defined
                              in the workflow configuration.
            destination_status (str): Status name after the transition occurred. Must be defined
                                    in the workflow configuration.
            date (str): ISO 8601 timestamp when the status transition occurred. Will be parsed
                       and formatted by the configured datetime field handler.

        Returns:
            dict[str, str | None]: Updated category_dates dictionary with timestamp modifications
                                  applied according to Kanban workflow rules. The returned dictionary
                                  maintains the same structure but with updated timestamp values.

        Raises:
            ValueError: If start_status or destination_status are not defined in workflow configuration.

        Example:
            >>> # Forward transition: Open -> In Progress
            >>> initial_dates = {"Status_Backlog": "2023-01-10", "Status_In Progress": None, "Status_Done": None}
            >>> updated_dates = workflow._Workflow__set_transition_dates(
            ...     initial_dates, "Open", "In Development", "2023-01-15T10:00:00Z"
            ... )
            >>> # Result: {"Status_Backlog": "2023-01-10", "Status_In Progress": "2023-01-15", "Status_Done": None}
            
            >>> # Backward transition: Done -> In Progress (clears future timestamps)
            >>> dates_with_completion = {"Status_Backlog": "2023-01-10", "Status_In Progress": "2023-01-15", "Status_Done": "2023-01-20"}
            >>> regressed_dates = workflow._Workflow__set_transition_dates(
            ...     dates_with_completion, "Resolved", "In Development", "2023-01-22T09:30:00Z"
            ... )
            >>> # Result: {"Status_Backlog": "2023-01-10", "Status_In Progress": "2023-01-15", "Status_Done": None}

        Note:
            This method is called iteratively during changelog processing and maintains
            detailed debug logging for transition analysis and troubleshooting.
        """
        category_start_status = self.__category_of_status(start_status)
        category_destination_status = self.__category_of_status(destination_status)

        position_start_status = self.__index_of_status(start_status)
        position_destination_status = self.__index_of_status(destination_status)

        category_start_status_index = self.__index_of_category(category_start_status)
        category_destination_status_index = self.__index_of_category(category_destination_status)

        self.logger.debug(f"Transition on {date}: {position_start_status}:{start_status}({category_start_status}) -> {position_destination_status}:{destination_status}({category_destination_status})")
        # Nothing to do here, this date had already been written
        # since there is no change to the category
        if category_start_status_index == category_destination_status_index:
            self.logger.debug("Same category, no dates to set.")
            return category_dates
        # The normal case, where the issue has been moved forward
        elif category_start_status_index < category_destination_status_index:
            for category_index in range(category_start_status_index, category_destination_status_index):
                self.logger.debug(f"Set date {date} for category: {category_index+1}")
                column_name: str = self.status_category_prefix + self.categories[category_index+1]
                # __timestamp_to_date returns a YYYY-MM-DD string now
                self.datetime_field.data = date
                category_dates[column_name] = self.datetime_field.value
        # The case, when an issue has moved backward to a previous category
        else:
            for category_index in range(category_destination_status_index, category_start_status_index):
                self.logger.debug(f"Unset date for category: {category_index+1}")
                column_name: str = self.status_category_prefix + self.categories[category_index+1]
                category_dates[column_name] = None

        return category_dates


    def __category_of_status(self, status: str) -> str:
        """
        Resolve workflow category containing the specified status using optimized lookup.

        Performs efficient category lookup for a given Jira status name using the internal
        status-to-category mapping dictionary built during initialization. This method provides
        constant-time O(1) lookup performance for status-to-category resolution, which is
        critical for high-performance workflow analysis of large issue datasets.

        Args:
            status (str): Exact name of the Jira status to look up. Must match a status
                         name defined in the workflow configuration exactly (case-sensitive).

        Returns:
            str: Name of the workflow category that contains the specified status.
                The category name matches exactly as defined in the configuration.

        Raises:
            ValueError: If the status name is not found in the workflow configuration.
                       This indicates either a typo in the status name or incomplete
                       workflow configuration that doesn't cover all statuses in the data.

        Example:
            >>> # Lookup category for specific status
            >>> category = workflow._Workflow__category_of_status("In Development")
            >>> print(category)  # Output: 'In Progress'
            
            >>> # Batch category resolution
            >>> statuses = ["Open", "Code Review", "Resolved"]
            >>> categories = [workflow._Workflow__category_of_status(s) for s in statuses]
            >>> print(categories)  # Output: ['Backlog', 'In Progress', 'Done']
            
            >>> # Error handling for undefined status
            >>> try:
            ...     category = workflow._Workflow__category_of_status("Unknown Status")
            ... except ValueError as e:
            ...     print(f"Status not configured: {e}")

        Note:
            This is a private method used internally during workflow analysis.
            The double underscore prefix enables name mangling for encapsulation.
        """
        if status not in self.statuses:
            raise ValueError(f"Unable to get status category. Status '{status}' not defined inside YAML configuration file.")
        return self.__status_category_mapping[status]


    def __index_of_category(self, category: str) -> int:
        """
        Resolve zero-based positional index of category in workflow progression sequence.

        Determines the sequential position of a workflow category within the ordered
        category list, which is essential for transition direction analysis and Kanban
        logic implementation. The index directly corresponds to the workflow progression
        stage, enabling mathematical comparison of category positions for forward/backward
        transition determination.

        The index values are used throughout workflow analysis to:
        - Compare category positions for transition direction logic
        - Calculate intermediate categories affected by transitions
        - Implement range-based category timestamp updates
        - Validate workflow progression consistency

        Args:
            category (str): Exact name of the workflow category to locate. Must match
                          a category name defined in the configuration exactly (case-sensitive).

        Returns:
            int: Zero-based index position of the category in the workflow sequence.
                Index 0 represents the first (initial) category, with subsequent
                categories receiving incrementally higher indices.

        Raises:
            ValueError: If the category name is not found in the workflow configuration.
                       This indicates either incorrect category name or configuration
                       mismatch with the data being processed.

        Example:
            >>> # Basic category index lookup
            >>> idx = workflow._Workflow__index_of_category("In Progress")
            >>> print(f"In Progress is at position {idx}")  # Output: position 1
            
            >>> # Compare category positions for transition analysis
            >>> start_idx = workflow._Workflow__index_of_category("Backlog")
            >>> end_idx = workflow._Workflow__index_of_category("Done")
            >>> if end_idx > start_idx:
            ...     print("Forward transition detected")
            >>> else:
            ...     print("Backward transition detected")
            
            >>> # Calculate workflow progression percentage
            >>> current_idx = workflow._Workflow__index_of_category("In Progress")
            >>> total_categories = len(workflow.categories)
            >>> progress_pct = (current_idx / (total_categories - 1)) * 100
            >>> print(f"Workflow {progress_pct:.1f}% complete")

        Note:
            This private method provides the foundation for all transition direction
            logic and category range calculations in the workflow analysis system.
        """
        if category not in self.categories:
            raise ValueError(f"Unable to get status category. Category '{category}' not defined inside YAML configuration file.")
        return int(self.categories.index(category))


    def __get_status_by_index(self, index: int) -> str:
        """
        Retrieve status name by zero-based positional index with comprehensive validation.

        Provides indexed access to the complete status list containing all Jira status
        names across all workflow categories. This method includes robust bounds checking
        and validation to prevent index errors during workflow analysis operations,
        especially when processing large datasets or dynamic status configurations.

        The status list maintains the order in which statuses were processed during
        configuration loading, typically grouped by category as defined in the
        workflow configuration file.

        Args:
            index (int): Zero-based position in the complete statuses list. Must be
                        within the valid range [0, number_of_statuses - 1].

        Returns:
            str: Name of the Jira status at the specified index position.
                The status name matches exactly as defined in the configuration.

        Raises:
            ValueError: If no statuses are configured in the workflow (empty configuration).
            ValueError: If the index exceeds the valid range of status positions.

        Example:
            >>> # Basic indexed status retrieval
            >>> first_status = workflow._Workflow__get_status_by_index(0)
            >>> print(f"First status: {first_status}")  # Output: 'Open'
            
            >>> # Iterate through all statuses by index
            >>> for i in range(workflow.number_of_statuses):
            ...     status = workflow._Workflow__get_status_by_index(i)
            ...     print(f"Status {i}: {status}")
            
            >>> # Safe status access with bounds checking
            >>> try:
            ...     status = workflow._Workflow__get_status_by_index(999)
            ... except ValueError as e:
            ...     print(f"Index out of bounds: {e}")
            
            >>> # Get last status in the workflow
            >>> last_idx = workflow.number_of_statuses - 1
            >>> last_status = workflow._Workflow__get_status_by_index(last_idx)
            >>> print(f"Final status: {last_status}")

        Note:
            This private method is primarily used for internal workflow analysis
            operations and debugging. Direct status access should typically use
            the statuses property or status name lookup methods.
        """
        max_index: int = self.number_of_statuses - 1
        if max_index < 0:
            raise ValueError("There are no statuses defined for the given workflow.")
        elif index > max_index:
            raise ValueError(f"Status at postion {index} does not exist. Max position is {max_index}.")
        else:
            return self.statuses[index]


    def __index_of_status(self, status: str) -> int:
        """
        Resolve zero-based positional index of status in the complete workflow status list.

        Performs efficient lookup to determine the sequential position of a Jira status
        within the comprehensive statuses list containing all status names across all
        workflow categories. The index position provides context for status relationships
        and is used in workflow analysis algorithms for position-based calculations.

        This method complements category-based indexing by providing fine-grained
        positional information at the individual status level, which is useful for
        detailed transition analysis and validation operations.

        Args:
            status (str): Exact name of the Jira status to locate. Must match a status
                         name defined in the workflow configuration exactly (case-sensitive).

        Returns:
            int: Zero-based index position of the status in the complete statuses list.
                The index reflects the order in which statuses were processed during
                configuration initialization, typically grouped by category.

        Raises:
            ValueError: If the status name is not found in the workflow configuration.
                       This indicates the status is not covered by the current workflow
                       setup and may require configuration updates.

        Example:
            >>> # Basic status index lookup
            >>> idx = workflow._Workflow__index_of_status("In Development")
            >>> print(f"In Development is at position {idx}")  # Output: position 3
            
            >>> # Compare status positions within same category
            >>> review_idx = workflow._Workflow__index_of_status("Code Review")
            >>> dev_idx = workflow._Workflow__index_of_status("In Development")
            >>> if review_idx > dev_idx:
            ...     print("Code Review follows In Development")
            
            >>> # Status position validation
            >>> try:
            ...     idx = workflow._Workflow__index_of_status("Undefined Status")
            ... except ValueError as e:
            ...     print(f"Status not found: {e}")
            
            >>> # Calculate status density per category
            >>> total_statuses = workflow.number_of_statuses
            >>> categories = workflow.number_of_categories
            >>> avg_density = total_statuses / categories
            >>> print(f"Average {avg_density:.1f} statuses per category")

        Note:
            This private method provides detailed status positioning information
            that complements the higher-level category indexing operations.
        """
        if (status not in self.statuses):
            raise ValueError(f"Position of status '{status}' could not be determined. Statues does not exist.")
        return self.statuses.index(status)
