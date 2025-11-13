# coding: UTF-8
from datetime import datetime
from pytz import UTC

class Workflow:
    """
    Parses Jira workflow transitions and calculates time-in-status metrics.

    This class analyzes issue status change logs to determine when issues moved
    between workflow categories. It tracks forward and backward transitions,
    applying Kanban-style logic where moving backward resets later timestamps.

    The workflow processes status changelog entries to build a timeline of category
    transitions, enabling time-tracking analysis for workflow optimization and
    reporting purposes.

    Key features:
    - Maps individual statuses to workflow categories
    - Calculates entry dates for each workflow category
    - Handles backward transitions by clearing future timestamps
    - Supports timezone conversions for date formatting

    Args:
        status_mapping: Dictionary mapping category names to lists of status names.
        time_zone: Timezone string for date conversions (defaults to UTC).
        date_pattern: Date format pattern for output (defaults to %Y-%m-%d).
        status_category_prefix: Prefix for status category column names.
        logger: Logger instance for debug and informational messages.

    Example:
        >>> status_map = {
        ...     "To Do": ["Open", "Reopened"],
        ...     "In Progress": ["In Development", "Code Review"],
        ...     "Done": ["Resolved", "Closed"]
        ... }
        >>> workflow = Workflow(status_map, "UTC", "%Y-%m-%d", "Status_", logger)
        >>> changelog = [
        ...     {"from": "Open", "to": "In Development", "date": "2023-01-15T10:00:00Z"},
        ...     {"from": "In Development", "to": "Resolved", "date": "2023-01-20T15:30:00Z"}
        ... ]
        >>> results = workflow.parse_status_changelog(changelog, "2023-01-10")
    """
    DEFAULT_TIME_ZONE = "UTC"
    DEFAULT_DATE_PATTERN = "%Y-%m-%d"

    def __init__(
        self,
        status_mapping: dict,
        time_zone: str,
        date_pattern: str,
        status_category_prefix: str,
        logger: object
    ) -> None:
        self.__categories: list = []
        self.__status_category_mapping: dict = {}
        self.__logger = logger
        self.__time_zone = time_zone or Workflow.DEFAULT_TIME_ZONE
        self.__date_pattern = date_pattern or Workflow.DEFAULT_DATE_PATTERN
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
        All status names defined in the workflow.

        Returns:
            List of all status names across all categories, in the order
            they were processed during initialization.
        """
        return list(self.__status_category_mapping.keys())

    @property
    def categories(self) -> list:
        """
        All category names defined in the workflow.

        Returns:
            List of category names in the order they appear in the
            configuration file.
        """
        return self.__categories

    @property
    def number_of_statuses(self) -> int:
        """
        Total count of statuses across all categories.

        Returns:
            The number of individual statuses defined in the workflow.
        """
        return len(self.statuses)
    
    @property
    def number_of_categories(self) -> int:
        """
        Total count of status categories in the workflow.

        Returns:
            The number of categories defined in the workflow.
        """
        return len(self.categories)

    @property
    def date_pattern(self) -> str:
        """
        Date pattern used for parsing and formatting dates.

        Returns:
            The date pattern string.
        """
        return self.__date_pattern
    
    @property
    def time_zone(self) -> str:
        """
        Time zone used for date and time conversions.

        Returns:
            The time zone string.
        """
        return self.__time_zone
    
    @property
    def status_category_prefix(self) -> str:
        """
        Prefix used for status category columns in exports.

        Returns:
            The status category prefix string.
        """
        return self.__status_category_prefix

    @property
    def logger(self) -> object:
        """
        Logger instance for logging messages.

        Returns:
            The logger object used for debug and informational output.
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
        Parse issue status changelog to extract category transition timestamps.

        Analyzes the complete status change history of an issue to determine when
        it moved between workflow categories. The method handles both forward and
        backward transitions, applying Kanban logic where backward moves reset
        timestamps for subsequent categories.

        The first category is always set to the issue creation date, representing
        the initial workflow state. Subsequent categories receive timestamps based
        on when status transitions moved the issue into those categories.

        Args:
            status_changelog: List of status transition dictionaries containing
                            'from', 'to', and 'date' keys for each transition.
            issue_creation_date: Creation date of the issue in ISO format, used
                               to timestamp the first workflow category.

        Returns:
            Dictionary mapping prefixed category names to their entry dates.
            Categories not yet reached have None values. Date format follows
            the configured date_pattern.

        Example:
            >>> changelog = [
            ...     {"from": "Open", "to": "In Progress", "date": "2023-01-15T10:00:00Z"}
            ... ]
            >>> result = workflow.parse_status_changelog(changelog, "2023-01-10")
            >>> # Returns: {"Status_To Do": "2023-01-10", "Status_In Progress": "2023-01-15", ...}
        """
        categories = {}
        transitions = []
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
        Update category timestamps based on a single status transition.

        Processes one status change event to update the category timeline. The method
        implements Kanban-style workflow logic where forward movements set timestamps
        for intermediate categories, while backward movements clear future timestamps
        to maintain workflow integrity.

        Three scenarios are handled:
        1. Same category: No timestamp changes (status change within category)
        2. Forward movement: Sets timestamps for all intermediate categories  
        3. Backward movement: Clears timestamps for all future categories

        Args:
            category_dates: Current dictionary of category timestamps being built.
            start_status: The status before this transition occurred.
            destination_status: The status after this transition occurred.
            date: ISO datetime string when the transition happened.

        Returns:
            Updated category_dates dictionary with modified timestamps based on
            the transition direction and Kanban workflow rules.

        Note:
            Backward transitions reset all future category timestamps to None,
            reflecting that the issue must re-progress through those stages.
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
            self.logger.debug(f"Same category, no dates to set.")
            return category_dates
        # The normal case, where the issue has been moved forward
        elif category_start_status_index < category_destination_status_index:
            for category_index in range(category_start_status_index, category_destination_status_index):
                self.logger.debug(f"Set date {date} for category: {category_index+1}")
                column_name: str = self.status_category_prefix + self.categories[category_index+1]
                # __timestamp_to_date returns a YYYY-MM-DD string now
                category_dates[column_name] = Workflow.convert_date(date, Workflow.DEFAULT_DATE_PATTERN, self.time_zone)
        # The case, when an issue has moved backward to a previous category
        else:
            for category_index in range(category_destination_status_index, category_start_status_index):
                self.logger.debug(f"Unset date for category: {category_index+1}")
                column_name: str = self.status_category_prefix + self.categories[category_index+1]
                category_dates[column_name] = None

        return category_dates


    def __category_of_status(self, status: str) -> str:
        """
        Find the category that contains the specified status.

        Args:
            status: The name of the status to look up.

        Returns:
            The name of the category containing the status.

        Raises:
            ValueError: If the status is not defined in the workflow configuration.

        Example:
            >>> workflow.category_of_status("In Development")
            'In Progress'
        """
        if status not in self.statuses:
            raise ValueError(f"Unable to get status category. Status '{status}' not defined inside YAML configuration file.")
        return self.__status_category_mapping[status]


    def __index_of_category(self, category: str) -> int:
        """
        Get the positional index of a category in the workflow.

        The index represents the order in which categories were defined
        in the configuration file, starting from 0.

        Args:
            category: The name of the category to find.

        Returns:
            The zero-based index position of the category.

        Raises:
            ValueError: If the category is not defined in the workflow configuration.

        Example:
            >>> workflow.index_of_category("In Progress")
            1
        """
        if category not in self.categories:
            raise ValueError(f"Unable to get status category. Category '{category}' not defined inside YAML configuration file.")
        return int(self.categories.index(category))


    def __get_status_by_index(self, index: int) -> str:
        """
        Retrieve a status name by its positional index.

        Args:
            index: The zero-based position in the statuses list.

        Returns:
            The name of the status at the specified index.

        Raises:
            ValueError: If the index is out of bounds or no statuses are defined.

        Example:
            >>> workflow.get_status_by_index(0)
            'Open'
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
        Find the positional index of a status in the workflow.

        Args:
            status: The name of the status to locate.

        Returns:
            The zero-based index position of the status in the statuses list.

        Raises:
            ValueError: If the status is not defined in the workflow configuration.

        Example:
            >>> workflow.index_of_status("In Development")
            2
        """
        if (status not in self.statuses):
            raise ValueError(f"Position of status '{status}' could not be determined. Statues does not exist.")
        return self.statuses.index(status)


    #############################
    ### Public static methods ###
    #############################


    @staticmethod
    def convert_date(datetime_str: str, date_pattern: str, time_zone: str) -> str:
        """
        Convert ISO datetime string to formatted date in specified timezone.

        Handles timezone conversion from ISO format timestamps (with or without 'Z'
        suffix) to a target timezone, then formats the result according to the
        specified date pattern.

        Args:
            datetime_str: Input datetime in ISO format (e.g., "2023-01-15T10:30:00Z"
                         or "2023-01-15T10:30:00+00:00").
            date_pattern: Python strftime pattern for output formatting 
                         (e.g., "%Y-%m-%d" for "2023-01-15").
            time_zone: Target timezone string for conversion (e.g., "UTC", "US/Eastern").

        Returns:
            Formatted date string in the target timezone according to the
            specified pattern.

        Example:
            >>> Workflow.convert_date("2023-01-15T10:30:00Z", "%Y-%m-%d", "UTC")
            '2023-01-15'
            >>> Workflow.convert_date("2023-01-15T10:30:00Z", "%m/%d/%Y", "US/Eastern") 
            '01/15/2023'
        """
        # Parse the input date string (handle both 'Z' suffix and timezone info)
        if datetime_str.endswith('Z'):
            dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(datetime_str)
        # Convert to the configured timezone
        if dt.tzinfo is None:
            dt = UTC.localize(dt)
        
        #target_tz = timezone(time_zone)
        dt_converted = dt.astimezone(time_zone)
        
        # Format according to the provided date pattern
        return dt_converted.strftime(date_pattern)