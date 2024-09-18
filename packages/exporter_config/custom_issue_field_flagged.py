# coding: UTF-8

from issue_field import IssueField

class CustomIssueFieldFlagged(IssueField):
    """
    """
    def __init__(self) -> None:
        super().__init__("Flagged")

    def parse_value(self, raw_value: object) -> str:
        """
        """
        return ""