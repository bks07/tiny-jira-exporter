# coding: UTF-8
from .issue_field import IssueField

class StandardIssueField(IssueField):
    """
    """
    def __init__(self, name: str, id: str, shall_fetch: bool = False, shall_export_to_csv: bool = False):
        super().__init__(name, id, shall_fetch, shall_export_to_csv)