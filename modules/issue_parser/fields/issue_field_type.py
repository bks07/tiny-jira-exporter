# coding: UTF-8

from abc import abstractmethod
from typing import Any
import re
import chardet

class IssueFieldType:
    """
    The general class for issue fields.
    It is a helper for the exporter config class.

    :param name: The name of the issue field like "Key"
    :type name: str
    :param id: The id of the issue field like "issuekey" or "customfield_10018"
    :type id: str
    :param shall_fetch: If true, the exporter will fetch this field from Jira
    :type shall_fetch: bool
    :param shall_export_to_csv: If true, the exporter will include this field in the export CSV file
    :param shall_export_to_csv: bool
    """
    CUSTOM_FIELD_ID_PATTERN = r"^customfield_\d+$"

    def __init__(
        self,
        name: str,
        id: str,
        shall_fetch: bool = False,
        shall_export_to_csv: bool = False
    ):
        # Porperties for Jira connection
        self.__name: str = name
        self.__id: str = id
        self.__shall_fetch: bool = shall_fetch
        self.__shall_export_to_csv = shall_export_to_csv
        # The actual data storage attribute can be private to hide complexity
        self._data: Any = None
        

    @property
    def name(
        self
    ) -> str:
        return self.__name
    
    @name.setter
    def name(
        self,
        value: str
    ):
        self.__name = value


    @property
    def id(
        self
    ) -> str:
        return self.__id


    @property
    def is_custom_field(
        self
    ) -> bool:
        return IssueFieldType.check_custom_field_id(id)


    @property
    def shall_fetch(
        self
    ) -> bool:
        # Must also be true if it should be exported
        return self.__shall_fetch or self.__shall_export_to_csv
    
    @shall_fetch.setter
    def shall_fetch(
        self,
        value: bool
    ):
        self.__shall_fetch = value


    @property
    def shall_export_to_csv(
        self
    ) -> bool:
        return self.__shall_export_to_csv
    
    @shall_export_to_csv.setter
    def shall_export_to_csv(
        self,
        value: bool
    ):
        self.__shall_export_to_csv = value


    @property
    @abstractmethod
    def data(
        self
    ) -> Any:
        pass
    
    @data.setter
    @abstractmethod
    def data(
        self,
        value: Any
    ):
        pass


    def _ensure_utf8(
        self,
        value: str
    ) -> str:
        """
        Ensures the input string is UTF-8 encoded and decodable.
        If the input is None or empty, returns an empty string.
        Tries to detect encoding and decode to UTF-8 if necessary.

        :param value: The value of the issue field
        :type value: str or any

        :return: The parsed field value as UTF-8 string
        :rtype: str
        """
        if not value or isinstance(value, str):
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


    @abstractmethod
    def get_value_for_csv(
        self
    ) -> str:
        """
        Returns the value as a string, with semicolons escaped.

        :param value: The value to be exported
        :return: String with semicolons escaped
        """
        pass


    @abstractmethod
    def get_value_id_for_csv(
        self
    ) -> str:
        """
        Returns the ID of the value as a string, with semicolons escaped.

        :param value: The value to be exported
        :return: String with semicolons escaped
        """
        pass


    @staticmethod
    def check_custom_field_id(
        field_id: str
    ) -> bool:
        """
        Checks if the given field ID matches the custom field pattern.

        :param field_id: The field ID to check
        :type field_id: str

        :return: True if it is a custom field ID, False otherwise
        :rtype: bool
        """
        return re.match(IssueFieldType.CUSTOM_FIELD_ID_PATTERN, field_id) is not None