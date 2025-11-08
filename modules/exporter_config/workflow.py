# coding: UTF-8

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
    def __init__(
        self,
        workflow: dict,
        logger: object
    ) -> None:
        self.__categories: list = []
        self.__status_category_mapping: dict = {}
        self.__logger = logger

        self.__logger.debug("Start loading workflow.")

        for status_category in workflow:
            self.__categories.append(status_category)
            self.__logger.debug(f"Created status category: {status_category}")
            for status in workflow[status_category]:
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