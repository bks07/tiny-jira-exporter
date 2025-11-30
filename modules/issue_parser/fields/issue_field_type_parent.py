from .issue_field_type import IssueFieldType

class IssueFieldTypeParent(IssueFieldType):
    """
    Handle Jira parent field references that link issues in hierarchical relationships.

    Processes the parent field from Jira API responses that establishes hierarchical
    relationships between issues, such as epic-story, story-subtask, or custom
    parent-child relationships. The field contains structured data with both the
    parent issue key (for human readability) and internal ID (for system operations).

    This field type extracts both the parent issue key (e.g., "PROJ-123") and the
    internal issue ID from Jira's parent field structure. Both values are available
    for export, enabling reports to show parent relationships using either the
    user-friendly key or the system ID.

    Ensures proper UTF-8 encoding for international characters in issue keys and
    provides robust error handling for missing or malformed parent data. Essential
    for reporting on issue hierarchies, epic progress, and project structure analysis.

    Example:
        >>> parent_field = IssueFieldTypeParent("parent", "Parent", False)
        >>> parent_field.data = {"key": "PROJ-123", "id": "10456"}
        >>> print(parent_field.value)     # "PROJ-123"
        >>> print(parent_field.value_id)  # "10456"

    Note:
        Parent fields always provide both display key and internal ID values,
        making them suitable for tracking issue hierarchies and relationships.
    """

    @property
    def data(
        self
    ) -> dict:
        """
        Get the raw parent field data from Jira API.

        Returns the stored dictionary object as received from the Jira API
        response, containing parent issue information including key and ID,
        or empty dictionary if no parent relationship exists.

        Returns:
            Dictionary containing parent issue data with 'key' and 'id' properties,
            or empty dictionary if no parent is set.
        """
        return self._data

    @data.setter
    def data(
        self,
        value: dict
    ) -> None:
        """
        Set parent field data from Jira API response and extract key and ID values.

        Validates that the input is a dictionary containing parent issue information
        and extracts both the issue key (for display) and internal ID (for system
        operations). Handles None values for issues without parent relationships
        and provides appropriate error handling for malformed data.

        For valid dictionary input, extracts the parent issue key and ID, converting
        them to UTF-8 encoded strings for safe CSV export. Missing keys or IDs are
        handled gracefully with empty string defaults.

        Args:
            value: Dictionary from Jira API containing parent issue data with
                   'key' and 'id' properties, or None for issues without parents.

        Raises:
            ValueError: If value is not None/dict, indicating malformed parent data.
        """
        if value is None:
            self._data = {}
            self._value = ""
            self._value_id = ""
        elif not isinstance(value, dict):
            self._data = {}
            self._value = ""
            self._value_id = ""
            raise ValueError("Parent field must be a dictionary containing issue key and ID.")
        else:
            self._data = value
            self._value = IssueFieldType.string_to_utf8(self._data["key"] if "key" in self._data else "")
            self._value_id = IssueFieldType.string_to_utf8(self._data["id"] if "id" in self._data else "")

    @property
    def has_value_id(
        self
    ) -> bool:
        """
        Check if this parent field type supports internal ID values.

        Parent fields always contain structured data with both the parent issue
        key (for display) and internal ID (for system operations) from Jira's
        API responses. This enables exports to include either the user-friendly
        issue key or the internal ID used by Jira for relationships.

        Returns:
            Always True for parent fields, indicating that both value (issue key)
            and value_id (internal ID) properties are available and meaningful.
        """
        return True
