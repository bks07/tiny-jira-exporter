# coding: UTF-8

class IssueField:
    """
    """
    def __init__(self, name: str, id: str, shall_fetch: bool = False, shall_export_to_csv: bool = False):
        # Porperties for Jira connection
        self.__name: str = name
        self.__id: str = id
        self.__shall_fetch: bool = shall_fetch
        self.__shall_export_to_csv = shall_export_to_csv
        

    @property
    def name(self) -> str:
        return self.__name
    
    @name.setter
    def name(self, value: str):
        self.__name = value

    @property
    def id(self) -> str:
        return self.__id
    
    @id.setter
    def id(self, value: str):
        self.__id = value

    @property
    def shall_fetch(self) -> bool:
        return self.__shall_fetch
    
    @shall_fetch.setter
    def shall_fetch(self, value: bool):
        self.__shall_fetch = value

    @property
    def shall_export_to_csv(self) -> bool:
        return self.__shall_export_to_csv
    
    @shall_export_to_csv.setter
    def export_to_csv(self, value: bool):
        self.__shall_export_to_csv = value