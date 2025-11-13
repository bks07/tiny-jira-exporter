from .issue_field_type import IssueFieldType

class IssueFieldTypeShortText(IssueFieldType):
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
        if value is None or not isinstance(value, str):
            self._data = ""
            raise ValueError("Short text field must be a string.")
        else:
            self._data = str(value)

    @property
    def value(
        self
    ) -> str:
        return IssueFieldType.string_to_utf8(self._data)

    @property
    def has_value_id(
        self
    ) -> bool:
        return False

    @property
    def value_id(
        self
    ) -> str:
        return ""  # Short text fields do not have an associated ID
    
    @property
    def has_value_id(
        self
    ) -> bool:
        return False # Short text fields do not have an associated ID