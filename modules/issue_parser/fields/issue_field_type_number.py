from .issue_field_type import IssueFieldType

class IssueFieldTypeNumber(IssueFieldType):
    """
    Represents a short text issue field, escaping semicolons for semicolon-delimited CSV.
    """

    @property
    def data(
        self
    ) -> str:
        return self._data

    @data.setter
    def data(
        self,
        value: str
    ) -> None:
        if value is None or not isinstance(value, str) or len(value) == 0:
            self._data = ""
        else:
            self._data = str(value)


    def get_value_for_csv(self):
        """
        Returns the value as a string, with semicolons escaped.

        :param value: The value to be exported
        :return: String with semicolons escaped
        """
        # Ensure the value is a string and properly encoded
        return IssueFieldType.string_to_utf8(self.data)


    def get_value_id_for_csv(self):
        """
        Returns the ID of the value as a string, with semicolons escaped.

        :return: Empty string since date fields do not have an ID
        """         
        return ""