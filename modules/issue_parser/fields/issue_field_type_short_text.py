from .issue_field_type import IssueFieldType

class IssueFieldTypeShortText(IssueFieldType):
    """
    Handle simple string-based Jira fields with text content.

    Processes text fields from Jira API responses including summary, description,
    single-line text custom fields, and other string-based data. Ensures proper
    UTF-8 encoding for international characters and provides safe CSV export
    formatting for text content.

    This field type handles the most common Jira field format and serves as
    the fallback type for unknown schema types. It validates input data to
    ensure string format and provides robust error handling for invalid data.

    Example:
        text_field = IssueFieldTypeShortText("summary", "Summary", False)
        text_field.data = "Project requirements analysis"
        print(text_field.value)  # "Project requirements analysis"

    Note:
        Text fields do not have separate internal ID values, only display text.
    """

    @property
    def data(
        self
    ) -> str:
        """
        Get the raw text data from Jira API.

        Returns the stored string value as received from the Jira API
        response, or empty string if no data has been set.

        Returns:
            Raw string data, or empty string if unset/invalid.
        """
        return self._data

    @data.setter
    def data(
        self,
        value: str
    ) -> None:
        """
        Set text data from Jira API response and process for export.

        Validates that the input is a string value and converts it to UTF-8
        for safe CSV export. Handles None values and invalid data types
        with appropriate error reporting.

        Args:
            value: String value from Jira API, or None for empty fields.

        Raises:
            ValueError: If value is not None and not a string type.
        """
        if value is None or not isinstance(value, str):
            self._data = ""
            raise ValueError("Short text field must be a string.")
        else:
            self._data = str(value)
            self._value = IssueFieldType.string_to_utf8(self._data)

    @property
    def has_value_id(
        self
    ) -> bool:
        """
        Check if this field type supports internal ID values.

        Text fields only contain string content without separate internal
        identifiers, so this property always returns False to indicate
        that value_id property is not meaningful for this field type.

        Returns:
            Always False for text fields (no internal ID available).
        """
        return False
