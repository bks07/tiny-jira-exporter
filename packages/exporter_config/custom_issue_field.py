# coding: UTF-8

from issue_field import IssueField

class CustomIssueField(IssueField):
    """
    """
    def __init__(self, name: str, internal_name: str, prefix: str = ""):
        super().__init__(name, internal_name)
        self._prefix = prefix

    @property
    def prefix(self) -> str:
        return self._prefix
    
    @prefix.setter
    def prefix(self, value: str):
        self._prefix = value

    def get_full_name(self) -> str:
        """
        """
        return self.prefix + self.name