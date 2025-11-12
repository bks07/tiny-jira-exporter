# coding: UTF-8
from datetime import datetime
from pytz import timezone, UTC

class Workflow:
    """
    Represents a Jira workflow configuration with status categories and transitions.

    This class manages the relationship between Jira statuses and their categories
    as defined in the YAML configuration. It provides methods to query status
    information, category mappings, and positional data for workflow analysis.

    The workflow structure follows a "category: [status1, status2, ...]" format
    where each category contains multiple statuses, and each status belongs to
    exactly one category.

    Args:
        workflow: Dictionary mapping category names to lists of status names.
        logger: Logger instance for debug and informational messages.

    Example:
        >>> workflow_config = {
        ...     "To Do": ["Open", "Reopened"],
        ...     "In Progress": ["In Development", "In Review"],
        ...     "Done": ["Resolved", "Closed"]
        ... }
        >>> workflow = Workflow(workflow_config, logger)
        >>> workflow.category_of_status("Open")
        'To Do'
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


    def category_of_status(self, status: str) -> str:
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


    def index_of_category(self, category: str) -> int:
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


    def get_status_by_index(self, index: int) -> str:
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


    def index_of_status(self, status: str) -> int:
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



    ######################
    ### PARSE WORKFLOW ###
    ######################


    def parse_status_changelog(
        self,
        status_changelog: dict,
        issue_creation_date: str
    ) -> dict:
        """
        Parses a given workflow defintion and returns the timestamps
        for each category based on status transitions.

        :param issue_id: The id of an issue
        :type issue_id: int
        :param issue_creation_date: The first category will always be set to the creation date of the issue
        :type issue_creation_date: str

        :return: The list of catogies with the timestamp ("category: YYYY-MM-DD")
        :rtype: dict
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


    def __set_transition_dates(
        self,
        category_dates: dict,
        start_status: str,
        destination_status: str,
        date: str
    ) -> dict:
        """
        Sets the transition dates for categories based on the date of the
        history event and the start status to the destination status.
        Also recognizes when an issue has moved backwards in the workflow.
        Since this is a strict Kanban-oriented logic, the script will erase all
        timestamps once an issue has been moved back.

        :param category_dates: The dictionary with the timestamps so far
        :type category_dates: dict
        :param start_status: The status the issue was before it got transitioned
        :type start_status: str
        :param destination_status: The status the issue got transitioned to
        :type destination_status: str
        :param date: The date of the history event (when the transition happened)
        :type date: str

        :return: The updated transition categories
        :rtype: dict
        """
        category_start_status = self.category_of_status(start_status)
        category_destination_status = self.category_of_status(destination_status)

        position_start_status = self.index_of_status(start_status)
        position_destination_status = self.index_of_status(destination_status)

        category_start_status_index = self.index_of_category(category_start_status)
        category_destination_status_index = self.index_of_category(category_destination_status)

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
                column_name: str = self.config.status_category_prefix + self.config.workflow.categories[category_index+1]
                # __timestamp_to_date returns a YYYY-MM-DD string now
                category_dates[column_name] = Workflow.convert_date(date)
        # The case, when an issue has moved backward to a previous category
        else:
            for category_index in range(category_destination_status_index, category_start_status_index):
                self.logger.debug(f"Unset date for category: {category_index+1}")
                column_name: str = self.config.status_category_prefix + self.config.workflow.categories[category_index+1]
                category_dates[column_name] = None

        return category_dates

    def convert_date(self, datetime_str: str, date_pattern: str) -> str:
        """
        Converts a given date string to a date in the specified format and timezone.

        :param date_str: The input date string (typically in ISO format)
        :type date_str: str

        :param date_pattern: The date format pattern to use for output
        :type date_pattern: str

        :return: The converted date string in the configured date format
        :rtype: str
        """
        # Parse the input date string (handle both 'Z' suffix and timezone info)
        if datetime_str.endswith('Z'):
            dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(datetime_str)
        # Convert to the configured timezone
        if dt.tzinfo is None:
            dt = UTC.localize(dt)
        
        target_tz = timezone(self.time_zone)
        dt_converted = dt.astimezone(target_tz)
        
        # Format according to the provided date pattern
        return dt_converted.strftime(date_pattern)