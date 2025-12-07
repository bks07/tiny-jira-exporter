from .issue_field_type import IssueFieldType

class IssueFieldTypeOption(IssueFieldType):
    """
    Handle Jira option fields containing structured objects with both ID and value properties.

    Processes option-type fields from Jira API responses including select lists, radio buttons,
    cascading select fields, and multi-select fields that return option objects with internal
    identifiers and display values. This field type is commonly used for custom fields that
    present users with predefined choices from a configured option set.

    The class extracts both the internal option ID (used by Jira for data storage and
    relationships) and the display value (shown to users in the interface) from Jira's
    option field structure. Both values are made available for export, enabling reports
    to include either the user-friendly display value or the internal ID depending on
    analysis and integration requirements.

    Option fields use 'value' instead of 'name' for the display text, distinguishing
    them from other structured field types. This reflects Jira's internal representation
    where option fields store the selected choice as a 'value' property rather than 'name'.

    Ensures proper UTF-8 encoding for international characters in both ID and value
    components, providing safe CSV export formatting and supporting global Jira instances
    with multilingual option configurations.

    Example:
        >>> option_field = IssueFieldTypeOption("customfield_10050", "Priority Level", False)
        >>> option_field.data = {"id": "10201", "value": "High Priority"}
        >>> print(option_field.value)     # "High Priority"
        >>> print(option_field.value_id)  # "10201"
        
        >>> # Multi-language support
        >>> option_field.data = {"id": "10202", "value": "Priorité Élevée"}
        >>> print(option_field.value)     # "Priorité Élevée" (properly encoded)

    Note:
        This field type always provides both value and value_id properties,
        making it suitable for option fields where both internal references
        and human-readable displays are required for comprehensive reporting.
    """
    VALUE_ID_KEY = "id"
    VALUE_VALUE_KEY = "value"  # Option fields use 'value' instead of 'name'

    @property
    def data(
        self
    ) -> dict:
        """
        Get the raw option field data from Jira API.

        Returns the stored dictionary object as received from the Jira API
        response for option-type fields. Contains both the internal option ID
        and the display value as configured in Jira's option schemes.

        Returns:
            Dictionary containing 'id' and 'value' keys with their respective
            data, or empty dictionary if no option is selected or data is unset.

        Example:
            >>> option_field.data
            {'id': '10201', 'value': 'High Priority'}
            >>> 
            >>> # Empty option field
            >>> empty_field.data
            {}
        """
        return self._data

    @data.setter
    def data(
        self,
        value: dict
    ) -> None:
        """
        Set option field data from Jira API response and extract ID and value components.

        Validates that the input is a dictionary containing both 'id' and 'value'
        keys as expected from Jira's option field responses. Extracts both the
        internal option ID (used for data storage and API operations) and the
        display value (shown to users), converting them to UTF-8 encoded strings
        for safe CSV export with international character support.

        Handles None values by resetting to empty state, which represents fields
        where no option has been selected. For valid dictionary input, populates
        both the value (display text) and value_id (internal identifier) properties
        from the corresponding dictionary keys with proper encoding.

        Args:
            value: Dictionary from Jira API containing option data with 'id' and
                   'value' keys, or None for fields with no selected option.
                   Expected format: {"id": "10201", "value": "Option Display Text"}

        Raises:
            ValueError: If value is not None/dict or missing required 'id'/'value' keys.
                       This indicates malformed option data from the Jira API or
                       incorrect field configuration.

        Example:
            >>> # Set option field with selection
            >>> option_field.data = {"id": "10201", "value": "High Priority"}
            >>> print(option_field.value)     # "High Priority"
            >>> print(option_field.value_id)  # "10201"
            
            >>> # Clear option field (no selection)
            >>> option_field.data = None
            >>> print(option_field.value)     # ""
            >>> print(option_field.value_id)  # ""
        """
        if value is None:
            self._data = {}
            self._value_id = ""
            self._value = ""
        elif not isinstance(value, dict) or \
            self.VALUE_ID_KEY not in value or \
            self.VALUE_VALUE_KEY not in value:
            raise ValueError(f"Option field '{self.name}' must be a dict with '{self.VALUE_ID_KEY}' and '{self.VALUE_VALUE_KEY}' keys.")
        else:
            self._data = value
            self._value_id = IssueFieldType.string_to_utf8(self._data.get(self.VALUE_ID_KEY, ""))
            self._value = IssueFieldType.string_to_utf8(self._data.get(self.VALUE_VALUE_KEY, ""))

    @property
    def has_value_id(
        self
    ) -> bool:
        """
        Check if this option field type supports internal ID values.

        Option fields always contain structured objects with both internal option IDs
        and display values from Jira's API responses. This dual representation enables
        exports to include either the user-friendly display value or the internal ID
        used by Jira for option storage, relationships, and API operations.

        The internal ID is particularly useful for:
        - Data consistency when option display values change
        - Integration with other systems that reference option IDs
        - Maintaining referential integrity in data exports
        - API operations that require option identifiers

        Returns:
            Always True for option fields, indicating that both value (display text)
            and value_id (internal option ID) properties are available and meaningful
            for comprehensive reporting and analysis.

        Example:
            >>> option_field.has_value_id
            True
            >>> # Both display value and internal ID are available
            >>> print(f"Display: {option_field.value}, ID: {option_field.value_id}")
            Display: High Priority, ID: 10201
        """
        return True
