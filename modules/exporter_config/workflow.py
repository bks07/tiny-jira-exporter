# coding: UTF-8

class Workflow:
    """
    Stors all information of the workflow as defined
    inside the YAML configuration file.

    :param workflow: All fields and categories of the workflow following "category: status".
    :type workflow: dict
    :param logger: The logger object
    :type logger: object
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
    def statuses(
        self
    ) -> list:
        return list(self.__status_category_mapping.keys())

    @property
    def categories(
        self
    ) -> list:
        return self.__categories

    @property
    def number_of_statuses(
        self
    ) -> int:
        return len(self.statuses)
    
    @property
    def number_of_categories(
        self
    ) -> int:
        return len(self.categories)


    ######################
    ### Public methods ###
    ######################


    def category_of_status(
        self,
        status: str
    ) -> str:
        """
        Returns the category of a given status.

        :param status: The name of the status.
        :type status: str

        :raise ValueError: If the status category cannot be found since the status is not defined inside the YAML configuration file.

        :return: The name of the category
        :rtype: str
        """
        if status not in self.statuses:
            raise ValueError("Unable to get status category. Status not defined.")
        return self.__status_category_mapping[status]


    def index_of_category(
        self,
        category: str
    ) -> int:
        """
        Returns the index number of the category.

        :param category: The category to look for
        :type category: int

        :raise ValueError: If category is not defined in YAML configuration file.

        :return: The index of the category
        :rtype: int
        """
        if category not in self.categories:
            raise ValueError("Unable to get status category. Category not defined.")
        return int(self.categories.index(category))


    def get_status_by_index(
        self,
        index: int
    ) -> str:
        """
        Retuns a given status based on it's index

        :param index: The position inside the list of statuses
        :type index: int

        :raise ValueError: If the index is out of bounds

        :return: The status name
        :rtype: str
        """
        max_index: int = self.number_of_statuses - 1
        if max_index < 0:
            raise ValueError("There are no statuses defined for the given workflow.")
        elif index > max_index:
            raise ValueError(f"Status at postion {index} does not exist. Max position is {max_index}.")
        else:
            return self.statuses[index]


    def index_of_status(
        self,
        status: str
    ) -> int:
        """
        Returns the index of a given status

        :param status: The name of the status
        :type status: str

        :raise ValueError: If the status is not defined inside the YAML configuration file.

        :return: The index of the status
        :rtype: int
        """
        if (status not in self.statuses):
            raise ValueError(f"Position of status '{status}' could not be determined. Statues does not exist.")
        return self.statuses.index(status)