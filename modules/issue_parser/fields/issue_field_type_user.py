from .issue_field_type import IssueFieldType

class IssueFieldTypeUser(IssueFieldType):
    """
    Represents a short text issue field, escaping semicolons for semicolon-delimited CSV.
    """

    @property
    def data(
        self
    ) -> str:
        return self._data

    @data.setter
    def data(
        self,
        value: str
    ) -> None:
        if value is None or not isinstance(value, str) or len(value) == 0:
            self._data = ""
        else:
            self._data = str(value)


    def get_value_for_csv(self):
        """
        Returns the value as a string, with semicolons escaped.

        :param value: The value to be exported
        :return: String with semicolons escaped
        """
        # Ensure the value is a string and properly encoded
        return_string = self._ensure_utf8(self.data)

        ### The following code is commented out since this is handled by Pandas when writing the CSV file
        # Remove existing surrounding double quotes, if any
        #if return_string.startswith('"'):
        #    return_string = return_string[1:]
        #if return_string.endswith('"'):
        #    return_string = return_string[:-1]
        # Escape double quotes by doubling them
        #return_string = return_string.replace('"', '""')
        # Enclose the string in double quotes so semicolons are treated as part of the text
        #return_string = f'"{return_string}"'

        # Enclose the string in double quotes so semicolons are treated as part of the text
        return return_string


    def get_value_id_for_csv(self):
        """
        Returns the ID of the value as a string, with semicolons escaped.

        :return: Empty string since date fields do not have an ID
        """         
        return ""