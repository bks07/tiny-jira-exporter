# coding: UTF-8
from abc import ABC, abstractmethod # Abstract base class

class IssueField:
    """
    """
    def __init__(self, name: str = "", id: str = ""):
        # Porperties for Jira connection
        self._name: str = name
        self._id: str = id

    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str):
        self._name = NameError

    @property
    def id(self) -> str:
        return self._id
    
    @id.setter
    def id(self, value: str):
        self._id = value

    @abstractmethod
    def parse_value(self, raw_value: object):
        pass