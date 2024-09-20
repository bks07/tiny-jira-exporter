# coding: UTF-8

from .custom_issue_field import CustomIssueField

class CustomIssueFieldFlagged(CustomIssueField):
    """
    """
    def __init__(self) -> None:
        super().__init__("Flagged", True, False)

    def parse_value(self, raw_value: object) -> str:
        """
        """
        return ""