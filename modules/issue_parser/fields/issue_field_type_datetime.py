from datetime import datetime
import pytz
from .issue_field_type import IssueFieldType

class IssueFieldTypeDatetime(IssueFieldType):
    """
    Represents a date issue field, formatting dates for CSV export.
    """
    DATE_PATTERN = "%Y-%m-%dT%H:%M:%S.%f%z"
    RETURN_DATE_ONLY = 0
    RETURN_DATE_TIME = 1
    RETURN_UNIX_TIMESTAMP = 2
    RETURN_UNIX_TIMESTAMP_MILLIS = 3
    RETURN_PATTERN_OPTIONS = [RETURN_DATE_ONLY, RETURN_DATE_TIME, RETURN_UNIX_TIMESTAMP, RETURN_UNIX_TIMESTAMP_MILLIS]
    DEFAULT_RETURN_PATTERN = RETURN_DATE_ONLY
    DEFAULT_TIME_ZONE = "UTC"

    def __init__(self, field_name: str, jira_field_name: str, fetch_only: bool = False) -> None:
        super().__init__(field_name, jira_field_name, fetch_only)
        self.__return_pattern = IssueFieldTypeDatetime.DEFAULT_RETURN_PATTERN
        self.__target_time_zone = pytz.timezone(IssueFieldTypeDatetime.DEFAULT_TIME_ZONE)
        self._data: datetime = None


    @property
    def data(self) -> str:
        if self._data is None:
            return ""
        try:
            dt_converted = self._data.astimezone(self.__target_time_zone)
            if self.__return_pattern == IssueFieldTypeDatetime.RETURN_DATE_TIME:
                return dt_converted.strftime("%Y-%m-%d %H:%M:%S %z")
            elif self.__return_pattern == IssueFieldTypeDatetime.RETURN_UNIX_TIMESTAMP:
                return str(int(dt_converted.timestamp()))
            elif self.__return_pattern == IssueFieldTypeDatetime.RETURN_UNIX_TIMESTAMP_MILLIS:
                return str(int(dt_converted.timestamp() * 1000))
            else:  # RETURN_DATE_ONLY or default
                return dt_converted.strftime("%Y-%m-%d")
        except Exception:
            return ""

    @data.setter
    def data(
        self,
        value: str
    ) -> None:
        self._data = None
        if value is None or not isinstance(value, str) or len(value) == 0:
            # Parse the string into a datetime object to check its validity
            try:
                self._data = datetime.strptime(value, IssueFieldTypeDatetime.DATE_PATTERN)
            except Exception:
                raise Exception(f"Failed to parse date value '{self._value}' with pattern '{IssueFieldTypeDatetime.DATE_PATTERN}'")
        else:
            raise Exception(f"Value '{self._value}' is not a string and cannot be parsed as a date")


    @property
    def return_pattern(self) -> int:
        return self.__return_pattern

    @return_pattern.setter
    def return_pattern(self, value: int) -> None:
        if value in IssueFieldTypeDatetime.RETURN_PATTERN_OPTIONS:
            self.__return_pattern = value
        else:
            self.__return_pattern = IssueFieldTypeDatetime.DEFAULT_RETURN_PATTERN
            raise ValueError(f"The given return pattern '{value}' is invalid. Valid options are: {IssueFieldTypeDatetime.RETURN_PATTERN_OPTIONS}. The return pattern has been set to the default value '{IssueFieldTypeDatetime.DEFAULT_RETURN_PATTERN}'.")


    @property
    def target_time_zone(self) -> str:
        return self.target_time_zone
    
    @target_time_zone.setter
    def target_time_zone(self, value: str) -> None:
        # Determine target timezone; fallback to UTC when no valid timezone is configured
        try:
            self.__target_time_zone = pytz.timezone(value)
        except Exception:
            self.__target_time_zone = pytz.timezone(IssueFieldTypeDatetime.DEFAULT_TIME_ZONE)
            raise ValueError(f"The configured time zone '{value}' is invalid. Please check the configuration. Falling back to '{IssueFieldTypeDatetime.DEFAULT_TIME_ZONE}'.")


    def get_value_for_csv(self) -> str:
        """
        Returns the value as a string, with semicolons escaped.

        :param value: The value to be exported
        :return: String with semicolons escaped
        """
        # Enclose the string in double quotes so semicolons are treated as part of the text
        return IssueFieldType.string_to_utf8(self.data)


    def get_value_id_for_csv(self):
        """
        Returns the ID of the value as a string, with semicolons escaped.

        :return: Empty string since date fields do not have an ID
        """         
        return ""