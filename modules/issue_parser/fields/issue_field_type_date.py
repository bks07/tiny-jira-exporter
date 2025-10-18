from datetime import datetime
from .issue_field_type import IssueFieldType

class IssueFieldTypeDate(IssueFieldType):
    """
    Represents a date issue field, formatting dates for CSV export.
    """
    DATE_PATTERN = "%Y-%m-%d"


    @property
    def data(
        self
    ) -> str:
        return self._data

    @data.setter
    def data(self, value: str) -> None:
        if isinstance(value, str) and value:
            try:
                dt = datetime.strptime(value, IssueFieldTypeDate.DATE_PATTERN)
                self._data = dt.strftime(IssueFieldTypeDate.DATE_PATTERN)
            except ValueError:
                self._data = ""
        else:
            self._data = ""
    

    def get_value_for_csv(self):
        """
        Returns the value as a string, with semicolons escaped.

        :return: Date string in 'YYYY-MM-DD' format
        """
        # Ensure the value is a string and properly encoded
        return self._ensure_utf8(self.data)


    def get_value_id_for_csv(self):
        """
        Returns the ID of the value as a string, with semicolons escaped.

        :return: Empty string since date fields do not have an ID
        """         
        return ""