# coding: UTF-8

from abc import abstractmethod
from typing import Any
import re
import chardet

class IssueFieldType:
    """
    Abstract base class for handling different types of Jira issue fields.

    Provides a common interface for parsing, storing, and formatting various
    Jira field types (text, date, user, array, etc.). Each field type handles
    its specific data structure and formatting requirements while maintaining
    a consistent API for the export process.

    This class manages field metadata (ID, name, fetch behavior) and provides
    utility methods for field identification and string processing. Concrete
    subclasses implement the actual data parsing and value extraction logic.

    Example:
        # Typically instantiated through IssueFieldTypeFactory
        field = IssueFieldTypeFactory.create_field_type(
            field_id="status",
            field_name="Status",
            schema_type="string"
        )
        field.data = raw_jira_field_data
        formatted_value = field.value

    Attributes:
        CUSTOM_FIELD_ID_PATTERN: Regex pattern for identifying custom fields.
        __id: Jira field identifier (e.g., 'status', 'customfield_10001').
        __name: Human-readable field name for export headers.
        __fetch_only: Whether field is fetched but excluded from CSV export.
        _data: Raw field data from Jira API (managed by subclasses).
    """
    CUSTOM_FIELD_ID_PATTERN = r"^customfield_\d+$"

    def __init__(
        self,
        id: str,
        name: str,
        fetch_only: bool = False
    ):
        """
        Initialize a new IssueFieldType instance with field metadata.

        Sets up the basic field properties that control how the field is
        identified, displayed, and handled during the export process.

        Args:
            id: Jira field identifier (e.g., 'status', 'customfield_10001').
            name: Human-readable field name for CSV export headers.
            fetch_only: If True, field is fetched but excluded from CSV export.
        """
        # Properties for Jira connection
        self.__id: str = id
        self.__name: str = name
        self.__fetch_only: bool = fetch_only

        # The actual data storage attribute can be private to hide complexity
        self._data: Any = None
        self._value: str = ""
        self._value_id: str = ""

    @property
    def id(
        self
    ) -> str:
        """
        Get the Jira field identifier.

        Returns the unique identifier used by Jira to reference this field
        in API requests and responses. Standard fields have names like 'status'
        or 'assignee', while custom fields follow the pattern 'customfield_XXXXX'.

        Returns:
            Jira field identifier string.
        """
        return self.__id


    @property
    def name(
        self
    ) -> str:
        """
        Get the human-readable field name.

        Returns the display name used in CSV export headers and user-facing
        output. This provides a more readable alternative to the technical
        field ID for end-user consumption.

        Returns:
            Human-readable field name string.
        """
        return self.__name


    @property
    def is_custom_field(
        self
    ) -> bool:
        """
        Check if this field is a custom field.

        Determines whether this field is a Jira custom field by examining
        the field ID pattern. Custom fields follow the format 'customfield_XXXXX'
        where XXXXX is a numeric identifier.

        Returns:
            True if this is a custom field, False for standard Jira fields.
        """
        return IssueFieldType.check_custom_field_id(self.id)
    

    @property
    def fetch_only(
        self
    ) -> bool:
        """
        Check if this field is fetch-only (excluded from CSV export).

        Indicates whether this field should be retrieved from Jira but
        excluded from the final CSV export. Useful for fields needed for
        processing (like workflow analysis) but not for end-user output.

        Returns:
            True if field should be fetched but not exported, False otherwise.
        """
        return self.__fetch_only
    
    @fetch_only.setter
    def fetch_only(
        self,
        value: bool
    ):
        """
        Set the fetch-only status for this field.

        Controls whether this field should be included in CSV export after
        being fetched from Jira. This can be changed dynamically based on
        configuration requirements or processing needs.

        Args:
            value: True to exclude from export, False to include in export.
        """
        self.__fetch_only = value

    @property
    @abstractmethod
    def data(
        self
    ) -> Any:
        """
        Get the raw field data from Jira API.

        Abstract property that must be implemented by subclasses to return
        the stored raw field data as received from the Jira API. The data
        structure varies by field type (dict, list, string, etc.).

        Returns:
            Raw field data in its original format from Jira API.
        """
        pass
    
    @data.setter
    @abstractmethod
    def data(
        self,
        value: dict
    ):
        """
        Set the raw field data from Jira API.

        Abstract setter that must be implemented by subclasses to store
        and process raw field data from Jira API responses. Subclasses
        should validate and transform the data as needed for their type.

        Args:
            value: Raw field data from Jira API response.
        """
        pass

    @property
    @abstractmethod
    def has_value_id(
        self
    ) -> bool:
        """
        Check if this field type supports internal ID values.

        Abstract property that must be implemented by subclasses to indicate
        whether the field has separate display and ID representations.
        Used to determine if value_id property should be accessed.

        Returns:
            True if field has internal ID values, False otherwise.
        """
        pass

    @property
    def value_id(
        self
    ) -> Any:
        """
        Get the internal ID representation of the field value.

        Abstract property that must be implemented by subclasses to return
        the internal identifier for fields that have both display names
        and internal IDs (e.g., status ID vs status name, user ID vs display name).

        Returns:
            Internal ID value for the field, or None if not applicable.
        """
        return self._value_id


    @property
    def value(
        self
    ) -> Any:
        """
        Get the formatted field value for CSV export.

        Abstract property that must be implemented by subclasses to return
        a human-readable, CSV-compatible representation of the field data.
        This is typically a string or simple value suitable for export.

        Returns:
            Formatted field value ready for CSV export.
        """
        return self._value


    @staticmethod
    def check_custom_field_id(
        field_id: str
    ) -> bool:
        """
        Check if a field ID matches the Jira custom field pattern.

        Validates whether the provided field ID follows the standard Jira
        custom field naming convention 'customfield_XXXXX' where XXXXX is
        a numeric identifier assigned by Jira.

        Args:
            field_id: Field identifier to validate.

        Returns:
            True if the ID matches custom field pattern, False otherwise.
        """
        return re.match(IssueFieldType.CUSTOM_FIELD_ID_PATTERN, field_id) is not None


    @staticmethod
    def string_to_utf8(
        value: str
    ) -> str:
        """
        Convert input string to UTF-8 with encoding detection and error handling.

        Ensures string data is properly UTF-8 encoded for safe CSV export.
        Handles various input encodings by detecting the source encoding
        and converting to UTF-8. Provides fallback handling for problematic
        characters or encoding errors.

        Args:
            value: Input string value, potentially in unknown encoding.

        Returns:
            UTF-8 encoded string, or empty string if input is None/invalid.

        Note:
            Uses chardet library for encoding detection and 'replace' error
            handling to ensure robust processing of international characters.
        """
        if not value or not isinstance(value, str):
            return ""

        # If already str, try to encode/decode as utf-8 directly

        try:
            # If it can be encoded as utf-8, it's fine
            value.encode("utf-8")
            return value
        except UnicodeEncodeError:
            # Try to detect encoding and decode
            raw_bytes = value.encode(errors="replace")

        detected = chardet.detect(raw_bytes)
        encoding = detected.get("encoding") or "utf-8"
        try:
            return raw_bytes.decode(encoding, errors="replace")
        except Exception:
            # Return a safe fallback string if decoding fails
            return ""