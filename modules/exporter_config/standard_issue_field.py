# coding: UTF-8
from .issue_field import IssueField

class StandardIssueField(IssueField):
    """
    A helper class that stores the configuration of a standard issue field.
    Helps to distinguish from custom issue fields by using isinstance()
    """
    def __init__(
        self,
        name: str,
        id: str,
        shall_fetch: bool = False,
        shall_export_to_csv: bool = False
    ):
        super().__init__(
            name,
            id,
            shall_fetch,
            shall_export_to_csv
        )