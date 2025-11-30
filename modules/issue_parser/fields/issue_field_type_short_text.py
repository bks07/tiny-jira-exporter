from .issue_field_type import IssueFieldType

class IssueFieldTypeShortText(IssueFieldType):
    """
    Handle string-based Jira fields containing plain text content.

    Processes text fields from Jira API responses including summaries, descriptions,
    single-line text custom fields, and other string-based data. Ensures proper
    UTF-8 encoding for international characters and provides safe CSV export
    formatting by handling special characters and encoding issues.

    This field type represents the most common Jira field format and serves as
    the fallback handler for unknown or unmapped schema types. It validates input
    data to ensure string format and provides robust error handling for invalid
    data types while maintaining data integrity.

    The class performs automatic UTF-8 conversion to ensure compatibility with
    international character sets and prevents CSV export issues caused by
    encoding mismatches. Text content is preserved exactly as received from
    Jira's API without modification beyond encoding normalization.

    Example:
        >>> text_field = IssueFieldTypeShortText("summary", "Summary", False)
        >>> text_field.data = "Project requirements analysis"
        >>> print(text_field.value)  # "Project requirements analysis"
        
        >>> # Handling international characters
        >>> text_field.data = "Müller's requirements für das Projekt"
        >>> print(text_field.value)  # "Müller's requirements für das Projekt"

    Note:
        Text fields contain only display text without separate internal ID values,
        making them suitable for descriptive content but not for relational data.
    """

    @property
    def data(
        self
    ) -> str:
        """
        Get the raw text data as received from Jira API.

        Returns the stored string value exactly as received from the Jira API
        response, before any UTF-8 encoding conversion is applied. This provides
        access to the original data for debugging or validation purposes.

        Returns:
            Original string data from Jira API response, or empty string
            if no data has been set or if invalid data was provided.
        """
        return self._data

    @data.setter
    def data(
        self,
        value: str
    ) -> None:
        """
        Set text data from Jira API response and prepare for CSV export.

        Validates that the input is a string value and converts it to UTF-8
        encoding for safe CSV export. The conversion process ensures that
        international characters, special symbols, and unicode content are
        properly handled and won't cause encoding issues during export.

        Handles None values by resetting to empty state, and provides clear
        error reporting for invalid data types while maintaining field
        consistency. Both the original data and the UTF-8 converted value
        are stored for different access patterns.

        Args:
            value: String value from Jira API containing text content,
                   or None for empty/unset fields.

        Raises:
            ValueError: If value is not None and not a string type,
                       indicating malformed field data from the API.

        Note:
            The UTF-8 conversion is applied automatically to ensure
            safe CSV export regardless of the original text encoding.
        """
        if value is None:
            self._data = ""
            self._value = ""
        elif not isinstance(value, str):
            self._data = ""
            self._value = ""
            raise ValueError("Short text field must be a string.")
        else:
            self._data = str(value)
            self._value = IssueFieldType.string_to_utf8(self._data)

    @property
    def has_value_id(
        self
    ) -> bool:
        """
        Check if this text field type supports internal ID values.

        Text fields contain only string content without separate internal
        identifiers or relational data. Unlike complex field types such as
        users, statuses, or components, plain text fields have no meaningful
        internal ID representation beyond their text content.

        This distinction is important for export configuration where some
        field types can export both display names and internal IDs, while
        text fields only provide the display text.

        Returns:
            Always False for text fields, indicating that the value_id
            property is not available or meaningful for this field type.
        """
        return False
