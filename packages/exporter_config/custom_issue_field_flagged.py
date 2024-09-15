# coding: UTF-8

from issue_field import IssueField

class CustomIssueFieldFlagged(IssueField):
    """
    """
    def __init__(self, id: str) -> None:
        super().__init__("Flagged", id)

    def parse_value(self, raw_value: object) -> str:
        """
        """
        return ""