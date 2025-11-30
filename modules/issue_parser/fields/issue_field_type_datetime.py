from datetime import datetime
import pytz
from .issue_field_type import IssueFieldType

class IssueFieldTypeDatetime(IssueFieldType):
    """
    Handle Jira datetime fields with timezone conversion and flexible formatting.

    Processes datetime fields from Jira API responses including created, updated,
    resolved dates, and datetime picker custom fields. Supports multiple output
    formats (date-only, full datetime, Unix timestamps) and timezone conversion
    for consistent reporting across different time zones.

    The class parses ISO 8601 datetime strings from Jira, converts them to a
    target timezone, and formats them according to configured output preferences.
    Provides robust error handling for invalid dates and timezone configurations.

    Example:
        datetime_field = IssueFieldTypeDatetime("created", "Created", False)
        datetime_field.target_time_zone = "America/New_York"
        datetime_field.return_pattern = IssueFieldTypeDatetime.RETURN_DATE_TIME
        datetime_field.data = "2023-12-01T10:30:00.000+0000"
        print(datetime_field.value)  # "2023-12-01 05:30:00 -0500"

    Attributes:
        DATE_PATTERN: ISO 8601 datetime format for parsing Jira timestamps.
        RETURN_DATE_ONLY: Output format constant for date-only format (YYYY-MM-DD).
        RETURN_DATE_TIME: Output format constant for full datetime with timezone.
        RETURN_UNIX_TIMESTAMP: Output format constant for Unix timestamp seconds.
        RETURN_UNIX_TIMESTAMP_MILLIS: Output format constant for Unix timestamp milliseconds.
    """
    INPUT_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"
    OPTION_DATE_FORMAT = 0
    OPTION_UNIX_TIMESTAMP = 1
    OPTION_UNIX_TIMESTAMP_MILLISECONDS = 2
    RETURN_VALUE_OPTIONS = [OPTION_DATE_FORMAT, OPTION_UNIX_TIMESTAMP, OPTION_UNIX_TIMESTAMP_MILLISECONDS]
    DEFAULT_VALUE_OPTION = OPTION_DATE_FORMAT
    DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_TIME_ZONE = "UTC"

    def __init__(self, field_name: str, jira_field_name: str, fetch_only: bool = False) -> None:
        """
        Initialize a new IssueFieldTypeDatetime instance with formatting configuration.

        Sets up the datetime field with default output format (date-only) and
        timezone (UTC). The field is ready to parse ISO 8601 datetime strings
        from Jira and convert them according to the configured preferences.

        Args:
            field_name: Jira field identifier (e.g., 'created', 'customfield_10020').
            jira_field_name: Human-readable field name for export headers.
            fetch_only: If True, field is fetched but excluded from CSV export.
        """
        super().__init__(field_name, jira_field_name, fetch_only)
        self.__return_value_option: int = IssueFieldTypeDatetime.DEFAULT_VALUE_OPTION
        self.__datetime_format: str = IssueFieldTypeDatetime.DEFAULT_DATETIME_FORMAT
        self.__target_time_zone: str = pytz.timezone(IssueFieldTypeDatetime.DEFAULT_TIME_ZONE)

        self._data: datetime = None


    @property
    def data(self) -> str:
        """
        Get the raw datetime data as a string representation.

        Returns the stored datetime object converted to string format,
        or "None" if no valid datetime has been parsed and stored.

        Returns:
            String representation of the stored datetime object.
        """
        return self._data

    @data.setter
    def data(
        self,
        value: str
    ) -> None:
        """
        Set datetime data from Jira API response and format for export.

        Parses ISO 8601 datetime strings from Jira API, converts them to the
        configured target timezone, and formats them according to the specified
        return pattern. Handles None values and invalid data with appropriate
        error reporting and fallback behavior.

        Args:
            value: ISO 8601 datetime string from Jira API, or None for empty fields.

        Raises:
            Exception: If value is not a string or cannot be parsed as datetime.
        """
        self._data = None
        if value is None:
            self._data = ""
            self._value = ""
        elif not isinstance(value, str):
            raise Exception(f"Value '{value}' is not a string and cannot be parsed as a date")
        elif len(value) == 0:
            self._data = ""
            self._value = ""
        else:
            # Parse the string into a datetime object to check its validity
            try:
                self._data = value
                self._value = IssueFieldTypeDatetime.convert_datetime(
                    value,
                    self.datetime_format,
                    str(self.target_time_zone),
                    self.return_value_option
                )


            except Exception as e:
                raise Exception(f"Failed to parse date value '{self._data}' with format '{IssueFieldTypeDatetime.INPUT_DATETIME_FORMAT}'. Original error: {e}")


    @property
    def has_value_id(
        self
    ) -> bool:
        """
        Check if this field type supports internal ID values.

        Datetime fields only contain timestamp values without separate internal
        identifiers, so this property always returns False to indicate that
        value_id property is not meaningful for this field type.

        Returns:
            Always False for datetime fields (no internal ID available).
        """
        return False # Date fields do not have an associated ID as they are string values only


    @property
    def datetime_format(self) -> str:
        """
        Get the current datetime format string pattern.

        Returns the strftime-compatible format string used for datetime formatting
        when the return_value_option is set to OPTION_DATE_FORMAT. This pattern
        determines how datetime values appear in CSV exports.

        Returns:
            String containing the current strftime format pattern
            (e.g., "%Y-%m-%d %H:%M:%S" for "2023-12-01 14:30:00").
        """
        return self.__datetime_format
    
    @datetime_format.setter
    def datetime_format(self, value: str) -> None:
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

        self.__datetime_format = value


    @property
    def return_value_option(self) -> int:
        """
        Get the current datetime return value format option.

        Returns the configured output format for datetime values in CSV exports.
        Available options include formatted dates, Unix timestamps in seconds,
        and Unix timestamps in milliseconds.

        Returns:
            Integer constant representing the current output format:
            - OPTION_DATE_FORMAT (0): Formatted date string
            - OPTION_UNIX_TIMESTAMP (1): Unix timestamp in seconds
            - OPTION_UNIX_TIMESTAMP_MILLISECONDS (2): Unix timestamp in milliseconds
        """
        return self.__return_value_option

    @return_value_option.setter
    def return_value_option(self, value: int) -> None:
        """
        Set the datetime return value format option.

        Configures how datetime values are formatted for CSV export. Valid options
        include formatted date strings, Unix timestamps in seconds, or Unix timestamps
        in milliseconds. Falls back to default format for invalid values.

        Args:
            value: Integer constant for output format:
                   - OPTION_DATE_FORMAT (0): Formatted date string
                   - OPTION_UNIX_TIMESTAMP (1): Unix timestamp in seconds  
                   - OPTION_UNIX_TIMESTAMP_MILLISECONDS (2): Unix timestamp in milliseconds

        Raises:
            ValueError: If value is not a valid option constant, with fallback to default.
        """
        if value in IssueFieldTypeDatetime.RETURN_VALUE_OPTIONS:
            self.__return_value_option = value
        else:
            self.__return_value_option = IssueFieldTypeDatetime.DEFAULT_VALUE_OPTION
            raise ValueError(f"The given return pattern '{value}' is invalid. Valid options are: {IssueFieldTypeDatetime.RETURN_VALUE_OPTIONS}. The return pattern has been set to the default value '{IssueFieldTypeDatetime.DEFAULT_VALUE_OPTION}'.")


    @property
    def target_time_zone(self) -> str:
        """
        Get the current target timezone for datetime conversion.

        Returns the timezone identifier used for converting Jira's UTC timestamps
        to the desired local time for reporting purposes.

        Returns:
            Timezone identifier string (e.g., 'UTC', 'America/New_York').
        """
        return str(self.__target_time_zone)
    
    @target_time_zone.setter
    def target_time_zone(self, value: str) -> None:
        """
        Set the target timezone for datetime conversion.

        Configures the timezone for converting Jira's UTC timestamps to local
        time for reporting. Validates the timezone identifier and falls back
        to UTC if the provided timezone is invalid. Existing data will be
        converted to the new timezone when this changes.

        Args:
            value: Timezone identifier string (e.g., 'UTC', 'America/New_York',
                   'Europe/London'). Must be a valid pytz timezone name.

        Raises:
            ValueError: If the timezone identifier is not valid, with fallback to UTC.
        """
        # Determine target timezone; fallback to UTC when no valid timezone is configured
        try:
            self.__target_time_zone = pytz.timezone(value)
        except Exception:
            self.__target_time_zone = pytz.timezone(IssueFieldTypeDatetime.DEFAULT_TIME_ZONE)
            raise ValueError(f"The configured time zone '{value}' is invalid. Please check the configuration. Falling back to '{IssueFieldTypeDatetime.DEFAULT_TIME_ZONE}'.")


    #############################
    ### Public static methods ###
    #############################


    @staticmethod
    def convert_datetime(
        datetime_str: str,
        return_date_format: str,
        return_time_zone: str,
        return_value_option: int = 0  # OPTION_DATE_FORMAT
    ) -> str:
        """
        Convert ISO datetime string to formatted output in specified timezone.

        Handles timezone conversion from ISO format timestamps (with or without 'Z'
        suffix) to a target timezone, then formats the result according to the
        specified return value option. Supports multiple output formats including
        formatted date strings, Unix timestamps, and millisecond timestamps.

        Special handling for Jira's millisecond format by padding 3-digit milliseconds
        to 6-digit microseconds required by Python's datetime parsing. Provides robust
        timezone parsing for both positive and negative UTC offsets.

        Args:
            datetime_str: Input datetime in ISO format (e.g., "2023-01-15T10:30:00Z",
                         "2023-01-15T10:30:00.123+00:00", or "2023-01-15T10:30:00.123-05:00").
            return_date_format: Python strftime pattern for formatted output 
                               (e.g., "%Y-%m-%d %H:%M:%S" for "2023-01-15 10:30:00").
            return_time_zone: Target timezone identifier string for conversion
                             (e.g., "UTC", "America/New_York", "Europe/London").
            return_value_option: Output format option (default: OPTION_DATE_FORMAT):
                                - OPTION_DATE_FORMAT (0): Formatted date string
                                - OPTION_UNIX_TIMESTAMP (1): Unix timestamp seconds
                                - OPTION_UNIX_TIMESTAMP_MILLISECONDS (2): Unix timestamp milliseconds

        Returns:
            Formatted datetime string in the target timezone according to the
            specified return value option, with UTF-8 encoding for safe CSV export.

        Example:
            >>> IssueFieldTypeDatetime.convert_datetime(
            ...     "2023-01-15T10:30:00.123Z", "%Y-%m-%d %H:%M:%S", "America/New_York", 0
            ... )
            '2023-01-15 05:30:00'
            >>> IssueFieldTypeDatetime.convert_datetime(
            ...     "2023-01-15T10:30:00Z", "%Y-%m-%d", "UTC", 1
            ... )
            '1673776200'
        """
        # Parse the input date string (handle both 'Z' suffix and timezone info)
        if datetime_str.endswith('Z'):
            datetime_str = datetime_str.replace("Z", "+00:00")
        
        # Handle Jira's milliseconds format by padding to microseconds
        # Jira uses 3-digit milliseconds (e.g., .112) but Python's %f expects 6-digit microseconds
        if '.' in datetime_str and '+' in datetime_str:
            # Split on timezone separator
            datetime_part, time_zone_part = datetime_str.rsplit('+', 1)
            if '.' in datetime_part:
                base_part, fraction_part = datetime_part.rsplit('.', 1)
                # Pad milliseconds (3 digits) to microseconds (6 digits)
                if len(fraction_part) < 6:
                    fraction_part = fraction_part.ljust(6, '0')
                    datetime_str = f"{base_part}.{fraction_part}+{time_zone_part}"
        elif '.' in datetime_str and '-' in datetime_str.split('T')[-1]:
            # Handle negative timezone offset
            datetime_part, time_zone_part = datetime_str.rsplit('-', 1)
            if '.' in datetime_part and ':' in time_zone_part:  # Ensure we split on timezone, not date
                base_part, fraction_part = datetime_part.rsplit('.', 1)
                # Pad milliseconds (3 digits) to microseconds (6 digits)
                if len(fraction_part) < 6:
                    fraction_part = fraction_part.ljust(6, '0')
                    datetime_str = f"{base_part}.{fraction_part}-{time_zone_part}"

        dt = datetime.fromisoformat(datetime_str)

        # Convert to the configured timezone
        if dt.tzinfo is None:
            utc = pytz.timezone("UTC")
            dt = utc.localize(dt)

        target_time_zone = pytz.timezone(str(return_time_zone))
        dt_converted = dt.astimezone(target_time_zone)
        
        return_value = ""
        if return_value_option == IssueFieldTypeDatetime.OPTION_DATE_FORMAT:
            return_value = dt_converted.strftime(return_date_format)
        elif return_value_option == IssueFieldTypeDatetime.OPTION_UNIX_TIMESTAMP:
            return_value = str(int(dt_converted.timestamp()))
        elif return_value_option == IssueFieldTypeDatetime.OPTION_UNIX_TIMESTAMP_MILLISECONDS:
            return_value = str(int(dt_converted.timestamp() * 1000))

        # Format according to the provided date pattern
        return IssueFieldType.string_to_utf8(return_value)
