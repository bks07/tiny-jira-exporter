from .issue_field_type import IssueFieldType

class IssueFieldTypeIdName(IssueFieldType):
    """
    Represents a short text issue field, escaping semicolons for semicolon-delimited CSV.
    """
    VALUE_ID_KEY = "id"
    VALUE_NAME_KEY = "name"

    @property
    def data(
        self
    ) -> dict:
        return self._data

    @data.setter
    def data(
        self,
        value: dict
    ) -> None:
        if value is None:
            self._data = {}
            self._value_id = ""
            self._value = ""
        elif not isinstance(value, dict) or \
            self.VALUE_ID_KEY not in value or \
            self.VALUE_NAME_KEY not in value:
            raise ValueError(f"IdName field must be a dict with '{self.VALUE_ID_KEY}' and '{self.VALUE_NAME_KEY}' keys.")
        else:
            self._data = value
            self._value_id = IssueFieldType.string_to_utf8(self._data.get(self.VALUE_ID_KEY, ""))
            self._value = IssueFieldType.string_to_utf8(self._data.get(self.VALUE_NAME_KEY, ""))

    @property
    def has_value_id(
        self
    ) -> bool:
        return True
