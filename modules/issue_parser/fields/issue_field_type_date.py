from datetime import datetime
from .issue_field_type import IssueFieldType

class IssueFieldTypeDate(IssueFieldType):
    """
    Handle date-type Jira fields with configurable formatting for CSV export.

    Processes date fields from Jira API responses including due dates, custom date
    fields, and other date-only values (without time components). Provides flexible
    date formatting using strftime patterns and ensures proper UTF-8 encoding for
    international date representations.

    This field type handles date parsing and validation, converting Jira's standard
    date format (YYYY-MM-DD) into configurable export formats. It provides robust
    error handling for invalid date strings and ensures consistent date formatting
    across all exported data.

    Example:
        >>> date_field = IssueFieldTypeDate("duedate", "Due Date", False)
        >>> date_field.date_format = "%d/%m/%Y"
        >>> date_field.data = "2023-12-25"
        >>> print(date_field.value)  # "25/12/2023"

    Note:
        Date fields do not have separate internal ID values, only formatted dates.
        All dates are expected to be in YYYY-MM-DD format from Jira's API.
    """
    DEFAULT_DATE_FORMAT = "%Y-%m-%d"

    def __init__(
        self,
        id: str,
        name: str,
        fetch_only: bool = False
    ):
        """
        Initialize a new IssueFieldTypeDate instance with field metadata.

        Args:
            id: Jira field identifier (e.g., 'duedate', 'customfield_10002').
            name: Human-readable field name for CSV export headers.
            fetch_only: If True, field is fetched but excluded from CSV export.
        """
        super().__init__(id, name, fetch_only)
        self.__date_format = IssueFieldTypeDate.DEFAULT_DATE_FORMAT


    @property
    def date_format(self) -> str:
        """
        Get the current date format pattern for this field.

        Returns the strftime-compatible date format string used to format
        date values for CSV export. Default is 'YYYY-MM-DD'.

        Returns:
            Current date format pattern string.
        """
        return self.__date_format

    @date_format.setter
    def date_format(self, value: str) -> None:
        """
        Set the date format pattern for this field.

        Updates the strftime-compatible date format string used to format
        date values for CSV export. Must be a valid format string.

        Args:
            value: New date format pattern string.
        """
        # Validate the new date format by attempting to format the current date
        try:
            datetime.now().strftime(value)
        except Exception as e:
            raise ValueError(f"Invalid date format string: {value}") from e

        self.__date_format = value


    @property
    def data(
        self
    ) -> str:
        """
        Get the raw date data from Jira API.

        Returns the stored date string as received from the Jira API
        response, typically in YYYY-MM-DD format, or empty string
        if no data has been set.

        Returns:
            Raw date string from Jira API, or empty string if unset.
        """
        return self._data

    @data.setter
    def data(
        self,
        value: str
    ) -> None:
        """
        Set date data from Jira API response and format for export.

        Validates that the input is a valid date string in YYYY-MM-DD format,
        parses it into a datetime object, and formats it according to the
        configured date_format pattern. Handles None values and invalid
        date formats with appropriate error reporting.

        The formatted date is stored in the value property with UTF-8 encoding
        to ensure safe CSV export with international date representations.

        Args:
            value: Date string from Jira API in YYYY-MM-DD format, or None for empty fields.

        Raises:
            ValueError: If value is not a valid date string in the expected format.
        """
        self._data = ""
        self._value = ""
        if isinstance(value, str) and value:
            try:
                self._data = str(value)
                dt = datetime.strptime(value, IssueFieldTypeDate.DEFAULT_DATE_FORMAT)
                self._value = IssueFieldType.string_to_utf8(dt.strftime(self.date_format))
            except ValueError:
                raise ValueError(f"Date field must be a string in '{IssueFieldTypeDate.DEFAULT_DATE_FORMAT}' format.")


    @property
    def has_value_id(
        self
    ) -> bool:
        """
        Check if this date field type supports internal ID values.

        Date fields contain only formatted date strings without separate internal
        identifiers. Unlike complex field types (users, options), date fields have
        no meaningful internal ID representation beyond their formatted value.

        Returns:
            Always False for date fields, indicating that value_id property
            is not available or meaningful for this field type.
        """
        return False