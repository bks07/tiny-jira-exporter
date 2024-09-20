# coding: UTF-8

from .custom_issue_field import CustomIssueField

class CustomIssueFieldParent(CustomIssueField):
    """
    """
    def __init__(self) -> None:
        super().__init__("Parent", True, False)

    def parse_value(self, raw_value: object) -> str:
        """
        """
        return ""