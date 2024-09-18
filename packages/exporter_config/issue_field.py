# coding: UTF-8
from abc import ABC, abstractmethod # Abstract base class

class IssueField:
    """
    """
    def __init__(self, name: str, id: str, fetch: bool = False, export_to_csv: bool = False):
        # Porperties for Jira connection
        self.__name: str = name
        self.__id: str = id
        self.__fetch: bool = fetch
        self.__export_to_csv = export_to_csv
        

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
    def fetch(self) -> bool:
        return self.__fetch
    
    @fetch.setter
    def fetch(self, value: bool):
        self.__fetch = value

    @property
    def export_to_csv(self) -> bool:
        return self.__export_to_csv
    
    @export_to_csv.setter
    def export_to_csv(self, value: bool):
        self.__export_to_csv = value

    @abstractmethod
    def parse_value(self, raw_value: object) -> str:
        pass