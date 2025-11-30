from .issue_field_type import IssueFieldType

class IssueFieldTypeIdName(IssueFieldType):
    """
    Handle Jira fields that contain structured objects with both ID and name properties.

    Processes field types from Jira API responses that return objects containing
    both internal identifiers and human-readable display names. This includes
    status, priority, issue type, resolution, and similar fields that have
    structured representations in Jira's data model.

    The class extracts both the internal ID (used by Jira for relationships and
    operations) and the display name (shown to users) from the field data. Both
    values are made available for export, allowing reports to include either or
    both depending on configuration requirements.

    Ensures proper UTF-8 encoding for international characters in both ID and
    name components, providing safe CSV export formatting.

    Example:
        >>> status_field = IssueFieldTypeIdName("status", "Status", False)
        >>> status_field.data = {"id": "10001", "name": "In Progress"}
        >>> print(status_field.value)     # "In Progress"
        >>> print(status_field.value_id)  # "10001"

    Note:
        This field type always provides both value and value_id properties,
        making it suitable for fields where both internal and display
        representations are meaningful.
    """
    VALUE_ID_KEY = "id"
    VALUE_NAME_KEY = "name"

    @property
    def data(
        self
    ) -> dict:
        """
        Get the raw structured data from Jira API.

        Returns the stored dictionary object as received from the Jira API
        response, containing both 'id' and 'name' properties, or empty
        dictionary if no data has been set.

        Returns:
            Dictionary containing 'id' and 'name' keys with their values,
            or empty dictionary if unset.
        """
        return self._data

    @data.setter
    def data(
        self,
        value: dict
    ) -> None:
        """
        Set structured data from Jira API response and extract ID and name values.

        Validates that the input is a dictionary containing both 'id' and 'name'
        keys as expected from Jira's structured field responses. Extracts both
        the internal ID and display name, converting them to UTF-8 encoded strings
        for safe CSV export.

        Handles None values by resetting to empty state. For valid dictionary input,
        populates both the value (display name) and value_id (internal ID) properties
        from the corresponding dictionary keys.

        Args:
            value: Dictionary from Jira API with 'id' and 'name' keys,
                   or None for empty fields.

        Raises:
            ValueError: If value is not None/dict or missing required 'id'/'name' keys.
        """
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
        """
        Check if this field type supports internal ID values.

        ID-name fields always contain structured objects with both internal IDs
        and display names from Jira's API responses. This enables exports to
        include either the user-friendly display name or the internal ID used
        by Jira for system operations.

        Returns:
            Always True for ID-name fields, indicating that both value and
            value_id properties are available and meaningful.
        """
        return True
