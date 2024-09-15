# Coding: UTF-8

import re
from issue_field import IssueField

class CustomIssueField(IssueField):

    CUSTOM_FIELD_ID_PATTERN = r"^customfield_\d+$"

    def __init__(self, name: str = "", id: str = ""):
        if re.match(CustomIssueField.CUSTOM_FIELD_ID_PATTERN, id):
            super().__init__(name, id)
        else:
            raise ValueError(f"The given ID '{id}' is invalid for a custom field. A custom field id must always follow the pattern 'customfield_XXXXX'.")