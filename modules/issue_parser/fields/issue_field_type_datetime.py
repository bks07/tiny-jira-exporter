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
        
        self.__value: str = ""

        self._data: datetime = None


    @property
    def data(self) -> str:
        return str(self._data)

    @data.setter
    def data(
        self,
        value: str
    ) -> None:
        self._data = None
        if value is None or not isinstance(value, str):
            raise Exception(f"Value '{value}' is not a string and cannot be parsed as a date")
        elif len(value) == 0:
            self._data = None
            self.__value = ""
        else:
            # Parse the string into a datetime object to check its validity
            try:
                self._data = datetime.strptime(value, IssueFieldTypeDatetime.DATE_PATTERN)

                dt_converted = self._data.astimezone(self.__target_time_zone)
                if self.__return_pattern == IssueFieldTypeDatetime.RETURN_DATE_TIME:
                    self.__value = IssueFieldType.string_to_utf8(self._data.strftime("%Y-%m-%d %H:%M:%S %z"))
                elif self.__return_pattern == IssueFieldTypeDatetime.RETURN_UNIX_TIMESTAMP:
                    self.__value = IssueFieldType.string_to_utf8(str(int(dt_converted.timestamp())))
                elif self.__return_pattern == IssueFieldTypeDatetime.RETURN_UNIX_TIMESTAMP_MILLIS:
                    self.__value = IssueFieldType.string_to_utf8(str(int(dt_converted.timestamp() * 1000)))
                else:  # RETURN_DATE_ONLY or default
                    self.__value = IssueFieldType.string_to_utf8(dt_converted.strftime("%Y-%m-%d"))
            except Exception:
                raise Exception(f"Failed to parse date value '{value}' with pattern '{IssueFieldTypeDatetime.DATE_PATTERN}'")


    @property
    def value(
        self
    ) -> str:
        return self.__value

    @property
    def has_value_id(
        self
    ) -> bool:
        return False # Date fields do not have an associated ID as they are string values only

    @property
    def value_id(
        self
    ) -> str:
        return "" # Date fields do not have an associated ID as they are string values only

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