import enum
from .issue_field_type import IssueFieldType

class IssueFieldTypeArray(IssueFieldType):
    """
    Handle array-type Jira fields containing multiple structured values.

    Processes array fields from Jira API responses including components, versions,
    users, labels, and other multi-value fields. Supports different item types
    (string, component, version, user, option) and formats them appropriately
    for CSV export using semicolon delimiters.

    This field type handles complex array structures by extracting both display
    names and internal IDs when available. It flattens array data into
    delimiter-separated strings suitable for CSV export while preserving
    the ability to access individual item properties.

    Example:
        >>> array_field = IssueFieldTypeArray("components", "Components", "component", False)
        >>> array_field.data = [{"id": "10001", "name": "Backend"}, {"id": "10002", "name": "Frontend"}]
        >>> print(array_field.value)  # "Backend;Frontend"
        >>> print(array_field.value_id)  # "10001;10002"

    Note:
        Array items are joined with semicolon delimiters. Some item types
        provide both display names and internal IDs for enhanced export options.
    """
    class ItemType(enum.Enum):
        STRING = "string"
        COMPONENT = "component"
        VERSION = "version"
        USER = "user"
        OPTION = "option"

    DELIMITER = ";"

    def __init__(self, id, name, item_type, fetch_only = False):
        """
        Initialize a new array field type handler.

        Args:
            id: Jira field identifier (e.g., 'components', 'customfield_10001').
            name: Human-readable field name for export headers.
            item_type: Type of items in the array (string, component, version, user, option).
            fetch_only: If True, field is fetched but excluded from export.

        Raises:
            ValueError: If item_type is not a valid ItemType enum value.
        """
        super().__init__(id, name, fetch_only)
        self.__item_type = IssueFieldTypeArray.ItemType(item_type)
        self.__has_value_id = False

    @property
    def data(
        self
    ) -> list:
        """
        Get the raw array data from Jira API.

        Returns the stored list value as received from the Jira API
        response, or empty list if no data has been set.

        Returns:
            Raw list data containing array items, or empty list if unset.
        """
        return self._data

    @data.setter
    def data(
        self,
        value: list
    ) -> None:
        """
        Set array data from Jira API response and process for export.

        Validates that the input is a list value and processes each item according
        to the configured item type. Extracts display names and internal IDs where
        available, joining them with semicolon delimiters for CSV export.

        Processing varies by item type:
        - USER: Extracts displayName and accountId from user objects
        - STRING: Uses string values directly (no IDs available)
        - Others: Extracts name and id properties from structured objects

        Args:
            value: List of items from Jira API, or None for empty fields.

        Raises:
            ValueError: If value is not None and not a list type.
        """
        # Initialize default values
        self._data = []
        self._value = ""
        self._value_id = ""
        self.__has_value_id = False
        if value is None:
            pass
        elif not isinstance(value, list):
            raise ValueError("Array field must be a list.")
        else:
            self._data = value
            if len(self._data) > 0:
                if self.__item_type == IssueFieldTypeArray.ItemType.USER:
                    # For user type arrays, we do not support value_id
                    self.__has_value_id = True
                    self._value_id = IssueFieldType.string_to_utf8(self.DELIMITER.join([str(item.get("accountId", "")) for item in self._data]))
                    self._value = IssueFieldType.string_to_utf8(self.DELIMITER.join([str(item.get("displayName", "")) for item in self._data]))
                elif self.__item_type == IssueFieldTypeArray.ItemType.STRING:
                    self.__has_value_id = False
                    self._value = IssueFieldType.string_to_utf8(self.DELIMITER.join([str(item).replace(";", "\\;") for item in self._data]))
                else:
                    self.__has_value_id = True
                    self._value_id = IssueFieldType.string_to_utf8(self.DELIMITER.join([str(item.get("id", "")) for item in self._data]))
                    self._value = IssueFieldType.string_to_utf8(self.DELIMITER.join([str(item.get("name", "")) for item in self._data]))

    @property
    def has_value_id(
        self
    ) -> bool:
        """
        Check if this array field type supports internal ID values.

        Array fields may or may not have internal IDs depending on their item type.
        String arrays only contain text values, while structured arrays (components,
        versions, users, options) typically provide both display names and IDs.

        Returns:
            True if the current array items have internal IDs available,
            False for string-only arrays or empty arrays.
        """
        return self.__has_value_id
