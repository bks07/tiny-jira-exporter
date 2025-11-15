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
        # A reference to the issue's resolution.
        # A JSON object with resolution details ({"id": "...", "name": "..."})
        "resolution": IssueFieldTypeIdName,
        "status": IssueFieldTypeIdName,
        "priority": IssueFieldTypeIdName,
        "issuetype": IssueFieldTypeIdName
        # INFO: Not implemented so far
        # group	An Atlassian group reference.	(Not a common default field)	Group Picker
        # issuelink	A reference to an issue link object.	issuelinks	Issue Link Field
        # attachment	A list of file attachments.	attachment	Attachment Field
        # comment	A list of comments.	comment	Comment Field
        # any	Used for fields that can hold various types of data or are highly customized (less common).
    }

    @staticmethod
    def create_field_type(
        schema_type: str,
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
        
        # 1. Look up the corresponding Python class from the map
        if schema_type in IssueFieldTypeFactory.FIELD_TYPE_MAPPING:
            field_class = IssueFieldTypeFactory.FIELD_TYPE_MAPPING[schema_type]
            try:
            # Create instance with initial name/id
              return field_class(name, id, fetch_only)
            except Exception as e:
                # Handle instantiation or validation errors (e.g., wrong value type)
                logger.error(f"Error instantiating field {name} ({field_class.__name__}): {e}")
                raise            
        else:
            # Handle unknown or unmapped fields (e.g., an app field you don't care about)
            logger.warning(f"Unknown scheme type '{schema_type}'. No field type created.")
            # You might define a generic IssueField subclass here for unhandled types
            return None

        # 2. Instantiate the correct class and set its value
        # The specific constructor arguments will depend on your subclass design.
        
