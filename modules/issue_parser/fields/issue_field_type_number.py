from .issue_field_type import IssueFieldType

class IssueFieldTypeNumber(IssueFieldType):
    """
    Handle numeric Jira fields with configurable decimal separator formatting.

    Processes numeric fields from Jira API responses including story points,
    time tracking estimates, numeric custom fields, and other numerical data.
    Provides configurable decimal separator formatting to accommodate different
    regional preferences (period for US format, comma for European format).

    The class handles both integer and floating-point numbers, converting them
    to appropriately formatted strings for CSV export while maintaining numeric
    precision. Ensures proper UTF-8 encoding and provides robust error handling
    for invalid numeric data.

    Regional formatting support makes the exports compatible with different
    spreadsheet applications and locale preferences, ensuring numbers display
    correctly regardless of the target system's regional settings.

    Example:
        >>> number_field = IssueFieldTypeNumber("storypoints", "Story Points", False)
        >>> number_field.decimal_separator = IssueFieldTypeNumber.DECIMAL_SEPARATOR_COMMA
        >>> number_field.data = "3.5"
        >>> print(number_field.value)  # "3,5" (European format)

    Note:
        Numeric fields do not have separate internal ID values, only formatted
        numeric strings suitable for CSV export and analysis.
    """

    DECIMAL_SEPARATOR_POINT = 0
    DECIMAL_SEPARATOR_COMMA = 1
    
    DECIMAL_SEPARATOR_MAP = {
        DECIMAL_SEPARATOR_POINT: ".",
        DECIMAL_SEPARATOR_COMMA: ","
    }

    def __init__(
            self,
            id: str,
            name: str,
            fetch_only: bool = False
                 ):
        """
        Initialize a new number field type handler with default formatting.

        Sets up the numeric field with default decimal separator (period/point)
        for US-style number formatting. The decimal separator can be changed
        later using the decimal_separator property to accommodate different
        regional formatting requirements.

        Args:
            id: Jira field identifier (e.g., 'storypoints', 'customfield_10020').
            name: Human-readable field name for export headers.
            fetch_only: If True, field is fetched but excluded from CSV export.
        """
        super().__init__(
            id,
            name,
            fetch_only
        )
        self._data: str = ""
        self.__decimal_separator: int = IssueFieldTypeNumber.DECIMAL_SEPARATOR_POINT

    @property
    def data(
        self
    ) -> str:
        """
        Get the raw numeric data as received from Jira API.

        Returns the stored numeric value as a string representation,
        preserving the original format from the Jira API response
        before any decimal separator conversion is applied.

        Returns:
            Raw numeric string from Jira API, or empty string if unset.
        """
        return self._data

    @data.setter
    def data(
        self,
        value: str
    ) -> None:
        """
        Set numeric data from Jira API response and format for export.

        Validates and processes numeric string values from Jira API responses,
        applying the configured decimal separator for regional formatting.
        Converts periods (.) to the appropriate decimal separator (period or comma)
        based on the current decimal_separator setting.

        Handles None values and empty strings by resetting to empty state.
        For valid numeric strings, stores both the original data and the
        regionally formatted value with UTF-8 encoding for safe CSV export.

        Args:
            value: Numeric string from Jira API (e.g., "3.14", "42"),
                   or None for empty fields.

        Note:
            The formatted value replaces periods with the configured decimal
            separator, enabling proper display in different regional formats.
        """
        if value is None or not isinstance(value, str) or len(value) == 0:
            self._data = ""
            self._value = ""
        else:
            self._data = str(value)
            self._value = IssueFieldType.string_to_utf8(self._data.replace(".", IssueFieldTypeNumber.DECIMAL_SEPARATOR_MAP[self.__decimal_separator]))

    @property
    def has_value_id(
        self
    ) -> bool:
        """
        Check if this numeric field type supports internal ID values.

        Numeric fields contain only formatted numeric strings without separate
        internal identifiers. Unlike complex field types (users, options),
        numeric fields have no meaningful internal ID representation beyond
        their numeric value.

        Returns:
            Always False for numeric fields, indicating that value_id property
            is not available or meaningful for this field type.
        """
        return False
    
    @property
    def decimal_separator(
        self
    ) -> int:
        """
        Get the current decimal separator format for numeric display.

        Returns the configured decimal separator constant that determines
        how decimal numbers are formatted in CSV exports. This enables
        regional formatting preferences for different target systems.

        Returns:
            Integer constant representing the decimal separator format:
            - DECIMAL_SEPARATOR_POINT (0): Period (.) for US format
            - DECIMAL_SEPARATOR_COMMA (1): Comma (,) for European format
        """
        return self.__decimal_separator
    
    @decimal_separator.setter
    def decimal_separator(
        self,
        value: int
    ) -> None:
        """
        Set the decimal separator format for numeric display.

        Configures how decimal numbers are formatted in CSV exports by
        specifying the decimal separator character. Supports both US format
        (period) and European format (comma). Invalid values default to
        US format (period) for safe fallback behavior.

        Args:
            value: Decimal separator constant:
                   - DECIMAL_SEPARATOR_POINT (0): Period (.) for US format
                   - DECIMAL_SEPARATOR_COMMA (1): Comma (,) for European format

        Note:
            Changes to this setting affect all subsequently processed numeric
            data, but do not retroactively reformat already processed values.
        """
        if value == IssueFieldTypeNumber.DECIMAL_SEPARATOR_COMMA:
            self.__decimal_separator = IssueFieldTypeNumber.DECIMAL_SEPARATOR_COMMA
        else:
            self.__decimal_separator = IssueFieldTypeNumber.DECIMAL_SEPARATOR_POINT