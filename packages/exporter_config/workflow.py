# coding: UTF-8

class Workflow:
    def __init__(self, workflow: dict) -> None:
        self.__categories: list = []
        self.__status_category_mapping: dict = {}

        for status_category in workflow:
            self.__categories.append(status_category)
            for status in workflow[status_category]:
                self.__status_category_mapping[status] = status_category


    ##################
    ### Properties ###
    ##################


    @property
    def statuses(self) -> list:
        return list(self.__status_category_mapping.keys())

    @property
    def categories(self) -> list:
        return self.__categories


    ######################
    ### Public methods ###
    ######################


    def get_category_of_status(self, status:str):
        if status not in self.statuses:
            raise ValueError("Unable to get status category. Status not defined.")
        return self.__status_category_mapping[status] # Add 'Category:' as prefix so its not confused with other fields


    def get_status_by_position(self, position: int) -> str:
        max_position: int = self.numberOfStatuses - 1
        if max_position < 0:
            raise ValueError("There are no statuses defined for the given workflow.")
        elif position > max_position:
            raise ValueError(f"Status at postion {position} does not exist. Max position is {max_position}.")
        else:
            return self.statuses[position]


    def get_status_position(self, status: str) -> int:
        if (status not in self.statuses):
            raise ValueError(f"Position of status '{status}' could not be determined. Statues does not exist.")
        return self.statuses.index(status)
    

    def numberOfStatuses(self) -> int:
        return len(self.statuses)
    

    def numberOfCategories(self) -> int:
        return len(self.categories)