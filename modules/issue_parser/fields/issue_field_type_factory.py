from typing import Dict, Type, Any
import logging

# Assuming your base and derived classes are defined as in the previous answer
from modules.exporter_config.exporter_config import ExporterConfig
from modules.issue_parser.fields.issue_field_type_option import IssueFieldTypeOption
from .issue_field_type import IssueFieldType
from .issue_field_type_short_text import IssueFieldTypeShortText
from .issue_field_type_date import IssueFieldTypeDate
from .issue_field_type_datetime import IssueFieldTypeDatetime
from .issue_field_type_id_name import IssueFieldTypeIdName
from .issue_field_type_user import IssueFieldTypeUser
from .issue_field_type_array import IssueFieldTypeArray
from .issue_field_type_number import IssueFieldTypeNumber
from .issue_field_type_flagged import IssueFieldTypeFlagged
from .issue_field_type_parent import IssueFieldTypeParent

class IssueFieldTypeFactory:
    """
    Factory class for creating appropriate IssueFieldType instances based on Jira field schemas.

    Implements the factory pattern to instantiate the correct field type handler
    based on Jira's schema type information. This enables polymorphic handling
    of different field types (string, date, user, array, etc.) without requiring
    the caller to know the specific implementation details.

    The factory uses a mapping table to associate Jira schema types with their
    corresponding Python classes, providing extensibility and maintainability
    for supporting new field types. Falls back to text handling for unknown types.

    Example:
        field = IssueFieldTypeFactory.create_field_type(
            schema_type="datetime",
            id="created",
            name="Created Date",
            fetch_only=False,
            logger=logger
        )

    Attributes:
        FIELD_TYPE_MAPPING: Dictionary mapping Jira schema types to Python classes.
    """
    SCHEMA_TYPE_PARENT = "parent"
    SCHEMA_TYPE_STRING = "string"
    SCHEMA_TYPE_NUMBER = "number"
    SCHEMA_TYPE_ARRAY = "array"
    SCHEMA_TYPE_DATE = "date"
    SCHEMA_TYPE_DATETIME = "datetime"
    SCHEMA_TYPE_USER = "user"
    SCHEMA_TYPE_RESOLUTION = "resolution"
    SCHEMA_TYPE_STATUS = "status"
    SCHEMA_TYPE_PRIORITY = "priority"
    SCHEMA_TYPE_ISSUETYPE = "issuetype"
    SCHEMA_TYPE_OPTION = "option"


    # Mapping of the primary schema types (schema.type) to IssueField subclasses
    FIELD_TYPE_MAPPING: Dict[str, Type[IssueFieldType]] = {
        # Plain text (e.g., Summary, Description, single-line text custom fields).
        # A simple JSON string ("Hello World")
        SCHEMA_TYPE_STRING: IssueFieldTypeShortText,
        # A numerical value (e.g., Story Points, Time Tracking estimates, number custom fields).
        # A JSON number (5.0 or 1200)
        SCHEMA_TYPE_NUMBER: IssueFieldTypeNumber,
        # A list of values (e.g., Components, Fix Versions, Labels, Multi-select custom fields).
        # A JSON array ([{"name": "v1"}, {"name": "v2"}] or ["labelA", "labelB"])
        SCHEMA_TYPE_ARRAY: IssueFieldTypeArray,
        # A date only, without time (e.g., Due Date, Date Picker custom fields).
        # A date string ("YYYY-MM-DD")
        SCHEMA_TYPE_DATE: IssueFieldTypeDate,
        # A date and time, typically with a timezone offset (e.g., Created, Updated, Date Time Picker custom fields).
        # An ISO 8601 string ("YYYY-MM-DDT HH:MM:SS.sss+HH:MM")
        SCHEMA_TYPE_DATETIME: IssueFieldTypeDatetime,
        # A reference to a Jira user (e.g., Reporter, Assignee, User Picker custom fields).
        # A JSON object with user details ({"accountId": "...", "displayName": "..."})
        SCHEMA_TYPE_USER: IssueFieldTypeUser,
        # A reference to the issue's resolution.
        # A JSON object with resolution details ({"id": "...", "name": "..."})
        SCHEMA_TYPE_RESOLUTION: IssueFieldTypeIdName,
        SCHEMA_TYPE_STATUS: IssueFieldTypeIdName,
        SCHEMA_TYPE_PRIORITY: IssueFieldTypeIdName,
        SCHEMA_TYPE_ISSUETYPE: IssueFieldTypeIdName,
        # A reference to an option value from a select list (e.g., Single Select, Multi Select custom fields).
        # A JSON object with option details ({"id": "...", "value": "..."})
        SCHEMA_TYPE_OPTION: IssueFieldTypeOption,
        # INFO: Not implemented so far
        # group	An Atlassian group reference.	(Not a common default field)	Group Picker
        # issuelink	A reference to an issue link object.	issuelinks	Issue Link Field
        # attachment	A list of file attachments.	attachment	Attachment Field
        # comment	A list of comments.	comment	Comment Field
        # any	Used for fields that can hold various types of data or are highly customized (less common).
    }

    def __init__(self):
        """
        Initialize a new IssueFieldTypeFactory with default configuration settings.

        Sets up the factory with default values for date formatting, timezone handling,
        and decimal separation. These settings are applied to field instances when they
        are created through the create_field_type method.

        The factory maintains internal mapping tables for converting ExporterConfig
        constants to field-type-specific constants, enabling consistent configuration
        across different field type implementations.
        """
        self.__date_format: str = ""
        self.__datetime_option: str = ""
        self.__datetime_format: str = ""
        self.__time_zone: str = ""
        self.__decimal_separator: str = ExporterConfig.DEFAULT_DECIMAL_SEPARATOR

        self._decimal_separator_map = {
            ExporterConfig.DECIMAL_SEPARATOR_POINT: IssueFieldTypeNumber.DECIMAL_SEPARATOR_POINT,
            ExporterConfig.DECIMAL_SEPARATOR_COMMA: IssueFieldTypeNumber.DECIMAL_SEPARATOR_COMMA
        }

        self._datetime_options_map = {
            ExporterConfig.DATETIME_OPTION_DATE: IssueFieldTypeDatetime.OPTION_DATE_FORMAT,
            ExporterConfig.DATETIME_OPTION_SECONDS: IssueFieldTypeDatetime.OPTION_UNIX_TIMESTAMP,
            ExporterConfig.DATETIME_OPTION_MILLISECONDS: IssueFieldTypeDatetime.OPTION_UNIX_TIMESTAMP_MILLISECONDS
        }



    @property
    def date_format(self) -> str:
        """
        Get the current date format pattern used for date field formatting.

        Returns the strftime-compatible format string that will be applied to
        date field instances created by this factory. This format determines
        how date values appear in CSV exports.

        Returns:
            String containing the date format pattern (e.g., "%Y-%m-%d").
        """
        return self.__date_format
    
    @date_format.setter
    def date_format(self, value: str) -> None:
        """
        Set the date format pattern for date field formatting.

        Configures the strftime-compatible format string that will be applied
        to IssueFieldTypeDate instances created by this factory. This setting
        affects all subsequently created date fields.

        Args:
            value: Date format pattern string (e.g., "%Y-%m-%d", "%d/%m/%Y").
        """
        self.__date_format = value


    @property
    def datetime_option(self) -> str:
        """
        Get the current datetime output option for datetime field formatting.

        Returns the configured output format type for datetime fields, which
        determines whether datetime values are exported as formatted strings,
        Unix timestamps, or Unix timestamps with milliseconds.

        Returns:
            String constant representing the datetime output option:
            - DATETIME_OPTION_DATE: Formatted date string
            - DATETIME_OPTION_SECONDS: Unix timestamp in seconds
            - DATETIME_OPTION_MILLISECONDS: Unix timestamp in milliseconds
        """
        return self.__datetime_option

    @datetime_option.setter
    def datetime_option(self, value: str) -> None:
        """
        Set the datetime output option for datetime field formatting.

        Configures how datetime values are formatted in CSV exports for
        IssueFieldTypeDatetime instances created by this factory. The setting
        is automatically converted to the appropriate field-type constant.

        Args:
            value: Datetime output option constant from ExporterConfig:
                   - DATETIME_OPTION_DATE: Formatted date string
                   - DATETIME_OPTION_SECONDS: Unix timestamp in seconds
                   - DATETIME_OPTION_MILLISECONDS: Unix timestamp in milliseconds
        """
        self.__datetime_option = value


    @property
    def datetime_format(self) -> str:
        """
        Get the current datetime format pattern used for datetime field formatting.

        Returns the strftime-compatible format string that will be applied to
        datetime field instances when the datetime_option is set to formatted
        string output. This format determines how datetime values appear in CSV exports.

        Returns:
            String containing the datetime format pattern (e.g., "%Y-%m-%d %H:%M:%S").
        """
        return self.__datetime_format

    @datetime_format.setter
    def datetime_format(self, value: str) -> None:
        """
        Set the datetime format pattern for datetime field formatting.

        Configures the strftime-compatible format string that will be applied
        to IssueFieldTypeDatetime instances created by this factory when using
        formatted string output. This setting affects all subsequently created datetime fields.

        Args:
            value: Datetime format pattern string (e.g., "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M").
        """
        self.__datetime_format = value


    @property
    def time_zone(self) -> str:
        """
        Get the current timezone setting for datetime field conversion.

        Returns the timezone identifier used for converting datetime values
        from UTC (Jira's default) to the desired local timezone for reporting.
        This affects how datetime fields display time values in CSV exports.

        Returns:
            Timezone identifier string (e.g., "UTC", "America/New_York", "Europe/London").
        """
        return self.__time_zone

    @time_zone.setter
    def time_zone(self, value: str) -> None:
        """
        Set the timezone for datetime field conversion.

        Configures the timezone identifier that will be applied to
        IssueFieldTypeDatetime instances created by this factory. Datetime
        values are converted from UTC to this timezone for display in CSV exports.

        Args:
            value: Valid pytz timezone identifier string (e.g., "UTC", 
                   "America/New_York", "Europe/London", "Asia/Tokyo").
        """
        self.__time_zone = value


    @property
    def decimal_separator(self) -> str:
        """
        Get the current decimal separator setting for number field formatting.

        Returns the decimal separator character used for formatting numerical
        values in CSV exports. This setting affects how decimal numbers are
        displayed in different locales (period for US format, comma for EU format).

        Returns:
            Decimal separator constant from ExporterConfig:
            - DECIMAL_SEPARATOR_POINT: Period (.) separator
            - DECIMAL_SEPARATOR_COMMA: Comma (,) separator
        """
        return self.__decimal_separator
    
    @decimal_separator.setter
    def decimal_separator(self, value: str) -> None:
        """
        Set the decimal separator for number field formatting.

        Configures the decimal separator character that will be applied to
        IssueFieldTypeNumber instances created by this factory. The setting
        is automatically converted to the appropriate field-type constant.

        Args:
            value: Decimal separator constant from ExporterConfig:
                   - DECIMAL_SEPARATOR_POINT: Period (.) separator for US format
                   - DECIMAL_SEPARATOR_COMMA: Comma (,) separator for EU format
        """
        self.__decimal_separator = value

    def create_field_type(
        self,
        schema_type: str,
        item_type: str,
        id: str,
        name: str,
        fetch_only: bool,
        logger: logging.Logger
    ) -> IssueFieldType:
        """
        Create the appropriate IssueFieldType instance based on Jira schema type.

        Determines the correct field type handler class from the schema type
        and instantiates it with the provided field metadata. Handles unknown
        schema types by falling back to text field handling with appropriate
        logging for troubleshooting.

        Supported schema types include: string, number, array, date, datetime,
        user, status, priority, issuetype, and resolution.

        Args:
            schema_type: Jira schema type identifier (e.g., 'string', 'datetime', 'user').
            id: Jira field identifier (e.g., 'status', 'customfield_10001').
            name: Human-readable field name for export headers.
            fetch_only: If True, field is fetched but excluded from CSV export.
            logger: Logger instance for warning/error reporting.

        Returns:
            Configured IssueFieldType instance ready for data processing.

        Raises:
            Exception: Re-raises any instantiation errors after logging for debugging.

        Note:
            Unknown schema types automatically fall back to IssueFieldTypeShortText
            with a warning logged for investigation.
        """
        # Special case for Parent field
        if name == "Parent":
            return IssueFieldTypeParent(id, name, fetch_only)

        # Look up the corresponding Python class from the map
        if schema_type in IssueFieldTypeFactory.FIELD_TYPE_MAPPING:
            if schema_type == "array":
                if name == "Flagged":
                    # Special case for the Flagged field
                    # Keep in mind that the "Flagged" field in Jira is represented as an array type
                    field_instance = IssueFieldTypeFlagged(id, name, fetch_only)
                else:
                    field_instance = IssueFieldTypeArray(id, name, item_type, fetch_only)
            else:
                field_class = IssueFieldTypeFactory.FIELD_TYPE_MAPPING[schema_type]
                field_instance = field_class(id, name, fetch_only)
                if schema_type == IssueFieldTypeFactory.SCHEMA_TYPE_DATE:
                    field_instance.date_format = self.date_format
                elif schema_type == IssueFieldTypeFactory.SCHEMA_TYPE_DATETIME:
                    field_instance.datetime_format = self.datetime_format
                    field_instance.time_zone = self.time_zone
                    field_instance.return_value_option = self._datetime_options_map[self.datetime_option]
                elif schema_type == IssueFieldTypeFactory.SCHEMA_TYPE_NUMBER:
                    field_instance.decimal_separator = self._decimal_separator_map[self.decimal_separator]
            return field_instance

        else:
            # Handle unknown or unmapped fields (e.g., an app field you don't care about)
            logger.warning(f"Unknown scheme type '{schema_type}'. No field type created.")
            # You might define a generic IssueField subclass here for unhandled types
            return None        
