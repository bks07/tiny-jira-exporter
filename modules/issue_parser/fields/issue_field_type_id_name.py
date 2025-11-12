from .issue_field_type import IssueFieldType

class IssueFieldTypeIdName(IssueFieldType):
    """
    Represents a short text issue field, escaping semicolons for semicolon-delimited CSV.
    """

    def get_value_for_csv(self):
        """
        Returns the value as a string, with semicolons escaped.

        :param value: The value to be exported
        :return: String with semicolons escaped
        """
        if self.data['name'] is None:
            return ""
        
        # Ensure the value is a string and properly encoded
        return IssueFieldType.string_to_utf8(self.data['value'])


    def get_value_id_for_csv(self):
        """
        Returns the ID of the value as a string, with semicolons escaped.

        :param value: The value to be exported
        :return: String with semicolons escaped
        """
        if self.data['id'] is None:
            return ""
        
        # Ensure the id is a string and properly encoded
        return IssueFieldType.string_to_utf8(self.data['id'])