from .issue_field_type import IssueFieldType

class IssueFieldTypeUser(IssueFieldType):
    """
    Handle Jira user fields with account ID and display name extraction.

    Processes user field data from Jira API responses that contain user objects
    with accountId and displayName properties. Commonly used for fields like
    assignee, reporter, and user picker custom fields. Provides access to both
    the internal account ID and human-readable display name.

    The class validates input data structure and handles missing or malformed
    user data gracefully. Supports UTF-8 encoding for international names and
    provides clean fallbacks for empty or invalid user references.

    Example:
        user_field = IssueFieldTypeUser("assignee", "Assignee", False)
        user_field.data = {"accountId": "123abc", "displayName": "John Doe"}
        print(user_field.value)     # "John Doe"
        print(user_field.value_id)  # "123abc"

    Attributes:
        VALUE_ID_KEY: JSON key for user account identifier.
        VALUE_NAME_KEY: JSON key for user display name.
    """
    VALUE_ID_KEY = "accountId"
    VALUE_NAME_KEY = "displayName"

    @property
    def data(
        self
    ) -> dict:
        """
        Get the raw user data from Jira API.

        Returns the stored user object containing accountId and displayName
        properties as received from the Jira API response. This provides access
        to the complete user data structure for debugging or advanced processing.

        Returns:
            Dictionary containing user data with 'accountId' and 'displayName' keys,
            or empty dictionary if no user is assigned to this field.
        """
        return self._data

    @data.setter
    def data(
        self,
        value: dict
    ) -> None:
        """
        Set user data from Jira API response and extract display values.

        Processes the user object from Jira API, validating the required
        accountId and displayName fields. Extracts and converts both values
        to UTF-8 strings for safe CSV export. Handles None values and
        invalid data structures with appropriate error handling.

        Args:
            value: User object dictionary from Jira API containing accountId
                   and displayName, or None for unassigned user fields.

        Raises:
            ValueError: If value is not None/dict or missing required keys.
        """
        if value is None:
            self._data = {}
            self._value_id = ""
            self._value = ""
        elif not isinstance(value, dict) or \
            self.VALUE_ID_KEY not in value or \
            self.VALUE_NAME_KEY not in value:
            # Reset to safe defaults before raising exception
            self._data = {}
            self._value_id = ""
            self._value = ""
            raise ValueError(f"User field '{self.name}' must be a dict with '{self.VALUE_ID_KEY}' and '{self.VALUE_NAME_KEY}' keys.")
        else:
            self._data = value
            self._value_id = IssueFieldType.string_to_utf8(self._data.get(self.VALUE_ID_KEY, ""))
            self._value = IssueFieldType.string_to_utf8(self._data.get(self.VALUE_NAME_KEY, ""))
    
    @property
    def has_value_id(
        self
    ) -> bool:
        """
        Check if this user field type supports internal ID values.

        User fields always contain structured data with both the user's display
        name (for human readability) and account ID (for system operations and
        API references). This dual representation enables exports to include
        either or both values depending on reporting requirements.

        The account ID is particularly important for system integrations, user
        tracking across name changes, and maintaining referential integrity
        when users update their display names.

        Returns:
            Always True for user fields, indicating that both value (display name)
            and value_id (account ID) properties are available and meaningful.
        """
        return True
