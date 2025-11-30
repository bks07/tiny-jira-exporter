from .issue_field_type import IssueFieldType

class IssueFieldTypeFlagged(IssueFieldType):
    """
    Handle Jira's flagged field which indicates issue priority or attention status.

    Processes the special "flagged" field from Jira API responses that marks
    issues as having elevated priority, impediments, or requiring special attention.
    The field is represented as a list in Jira's API - an empty list means not flagged,
    while a non-empty list (typically containing values like "Impediment") indicates
    the issue is flagged.

    This field type converts the list-based API representation to simple TRUE/FALSE
    string values for clear CSV export formatting, making it easy to filter and
    analyze flagged issues in reports and dashboards.

    Despite being stored as a custom field in Jira (customfield_*), it's treated
    as a standard field for export purposes due to its widespread use and
    standardized behavior across Jira instances.

    Example:
        >>> flagged_field = IssueFieldTypeFlagged("customfield_10001", "Flagged", False)
        >>> flagged_field.data = [{"value": "Impediment"}]  # Issue is flagged
        >>> print(flagged_field.value)  # "TRUE"
        
        >>> flagged_field.data = []  # Issue is not flagged  
        >>> print(flagged_field.value)  # "FALSE"

    Note:
        Flagged fields do not have separate internal ID values, only boolean status.
        The field is classified as a standard field for export consistency despite
        its custom field storage in Jira.
    """
    @property
    def is_custom_field(
        self
    ) -> bool:
        """
        Override to classify flagged field as standard for export purposes.

        Although the flagged field is technically stored as a custom field in Jira
        (customfield_*), it's treated as a standard field in exports due to its
        widespread use and standardized behavior. This ensures it appears in the
        standard fields section of CSV exports rather than custom fields.

        Returns:
            Always False to classify this field as standard rather than custom,
            ensuring consistent export formatting and field grouping.
        """
        return False


    @property
    def data(
        self
    ) -> list:
        """
        Get the raw flagged field data from Jira API.

        Returns the stored list value as received from the Jira API response.
        An empty list indicates the issue is not flagged, while a non-empty
        list indicates the issue is flagged.

        Returns:
            List representing flagged status, or empty list if not flagged.
        """
        return self._data

    @data.setter
    def data(
        self,
        value: list
    ) -> None:
        """
        Set flagged field data from Jira API response and convert to boolean status.

        Processes the list-based flagged field from Jira API and converts it
        to a simple TRUE/FALSE string value for CSV export. An empty list or
        None indicates not flagged (FALSE), while any non-empty list indicates
        flagged (TRUE).

        Args:
            value: List value from Jira API representing flagged status,
                   or None for unflagged issues.

        Raises:
            ValueError: If value is not None and not a list type.
        """
        if value is None:
            self._data = []
            self._value = "FALSE"
        elif not isinstance(value, list):
            # Reset to safe defaults before raising exception
            self._data = []
            self._value = "FALSE"
            raise ValueError("Flagged field must be a list or None.")
        else:
            self._data = value
            self._value = "TRUE" if len(value) > 0 else "FALSE"


    @property
    def has_value_id(
        self
    ) -> bool:
        """
        Check if this flagged field type supports internal ID values.

        Flagged fields contain only boolean status information (TRUE/FALSE) without
        separate internal identifiers. Unlike complex field types (users, options),
        the flagged field has no meaningful internal ID representation beyond its
        boolean state.

        Returns:
            Always False for flagged fields, indicating that value_id property
            is not available or meaningful due to the field's boolean nature.
        """
        return False
