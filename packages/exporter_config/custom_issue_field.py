# Coding: UTF-8

import re
from issue_field import IssueField

class CustomIssueField(IssueField):

    CUSTOM_FIELD_ID_PATTERN = r"^customfield_\d+$"

    def __init__(self, name: str, fetch: bool = False, export_to_csv: bool = False):
        self.__id: str = ""
        super().__init__(name, "", fetch, export_to_csv)


    @property
    def id(self) -> str:
        return self.__id
    
    @id.setter
    def id(self, value: str):
        if re.match(CustomIssueField.CUSTOM_FIELD_ID_PATTERN, value):
            self.__id = value
        else:
            raise ValueError(f"The given ID '{value}' is invalid for a custom field. A custom field id must always follow the pattern 'customfield_XXXXX'.")