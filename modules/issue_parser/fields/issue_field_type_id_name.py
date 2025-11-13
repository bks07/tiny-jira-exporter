from .issue_field_type import IssueFieldType

class IssueFieldTypeIdName(IssueFieldType):
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
        value: dict
    ) -> None:
        if value is None or \
            not isinstance(value, dict) or \
            "name" not in value or \
            "id" not in value:
            self._data = ""
            raise ValueError("IdName field must be a dict with 'id' and 'name' keys.")
        else:
            self._data = value

    @property
    def value(
        self
    ) -> str:
        return IssueFieldType.string_to_utf8(self._data.get("name", ""))
    
    @property
    def value_id(
        self
    ) -> str:
        return IssueFieldType.string_to_utf8(self._data.get("id", ""))
    
    @property
    def has_value_id(
        self
    ) -> bool:
        return True