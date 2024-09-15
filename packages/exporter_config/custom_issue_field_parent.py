# coding: UTF-8

from custom_issue_field import CustomIssuefield

class CustomIssueFieldParent(CustomIssueField):
    """
    """
    def __init__(self, name: str, id: str) -> None:
        super().__init__("Parent", id)

    def parse_value(self, raw_value: object) -> str:
        """
        """
        return ""