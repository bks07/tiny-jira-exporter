from typing import Dict, Type, Any
import logging

# Assuming your base and derived classes are defined as in the previous answer
from .issue_field_type import IssueFieldType
from .issue_field_type_short_text import IssueFieldTypeShortText
from .issue_field_type_date import IssueFieldTypeDate
from .issue_field_type_datetime import IssueFieldTypeDatetime
from .issue_field_type_id_name import IssueFieldTypeIdName
from .issue_field_type_user import IssueFieldTypeUser
from .issue_field_type_array import IssueFieldTypeArray
from .issue_field_type_number import IssueFieldTypeNumber

# A dictionary to map API-returned type strings to your Python classes


class IssueFieldTypeFactory:
    """
    A factory class for creating the correct IssueField subclass
    based on the field's metadata.
    """

    # Mapping of the primary schema types (schema.type) to IssueField subclasses
    FIELD_TYPE_MAPPING: Dict[str, Type[IssueFieldType]] = {
        # Plain text (e.g., Summary, Description, single-line text custom fields).
        # A simple JSON string ("Hello World")
        "string": IssueFieldTypeShortText,
        # A numerical value (e.g., Story Points, Time Tracking estimates, number custom fields).
        # A JSON number (5.0 or 1200)
        "number": IssueFieldTypeNumber,
        # A list of values (e.g., Components, Fix Versions, Labels, Multi-select custom fields).
        # A JSON array ([{"name": "v1"}, {"name": "v2"}] or ["labelA", "labelB"])
        "array": IssueFieldTypeArray,
        # A date only, without time (e.g., Due Date, Date Picker custom fields).
        # A date string ("YYYY-MM-DD")
        "date": IssueFieldTypeDate,
        # A date and time, typically with a timezone offset (e.g., Created, Updated, Date Time Picker custom fields).
        # An ISO 8601 string ("YYYY-MM-DDT HH:MM:SS.sss+HH:MM")
        "datetime": IssueFieldTypeDatetime,
        # A reference to a Jira user (e.g., Reporter, Assignee, User Picker custom fields).
        # A JSON object with user details ({"accountId": "...", "displayName": "..."})
        "user": IssueFieldTypeUser,
        # A reference to a Jira Project.
        # A JSON object with project details ({"id": "...", "key": "..."})
        #"project": IssueFieldTypeProject,
        # A reference to the issue's resolution.
        # A JSON object with resolution details ({"id": "...", "name": "..."})
        "resolution": IssueFieldTypeIdName,
        # A reference to the issue's priority.
        # A JSON object with priority details ({"id": "...", "name": "..."})
        "priority": IssueFieldTypeIdName,
        # A reference to the issue's type.
        # A JSON object with issue type details ({"id": "...", "name": "..."})
        "issuetype": IssueFieldTypeIdName
        # The combined time tracking fields (Original Estimate, Remaining Estimate).
        # A JSON object with seconds ({"originalEstimateSeconds": 7200})	
        #"timetracking": IssueFieldTypeTimeTracking
    }

    @staticmethod
    def create_field_type(
        schema_type: str,
        name: str,
        id: str,
        logger: logging.Logger
    ) -> IssueFieldType:
        """
        Instantiates the appropriate IssueField subclass.
        
        Args:
            schema_type: The schema type identifier.
            name: The display name of the field.
            id: The API ID of the field (e.g., 'customfield_10000').
            logger: Logger instance for error handling.
            
        Returns:
            An instance of an IssueFieldType subclass.
            
        Raises:
            ValueError: If the scheme type key is unknown.
        """
        
        # 1. Look up the corresponding Python class from the map
        if schema_type in IssueFieldTypeFactory.FIELD_TYPE_MAPPING:
            field_class = IssueFieldTypeFactory.FIELD_TYPE_MAPPING[schema_type]
        else:
            # Handle unknown or unmapped fields (e.g., an app field you don't care about)
            logger.warning(f"Unknown scheme type '{schema_type}'. Falling back to short text field type.")
            # You might define a generic IssueField subclass here for unhandled types
            return IssueFieldTypeShortText(name, id) # Assuming IssueField is not abstract or has a concrete implementation

        # 2. Instantiate the correct class and set its value
        # The specific constructor arguments will depend on your subclass design.
        try:
            # Create instance with initial name/id
            return field_class(name, id)
            
        except Exception as e:
            # Handle instantiation or validation errors (e.g., wrong value type)
            logger.error(f"Error instantiating field {name} ({field_class.__name__}): {e}")
            raise
