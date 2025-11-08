"""
Jira test data provider for unit testing.

This module provides access to pre-recorded Jira API responses stored as JSON files.
It enables unit tests to run with realistic data without requiring access to a live
Jira instance, ensuring consistent test execution and eliminating external dependencies.

The test data files are generated using the jira_test_data_fetcher script and contain
real Jira responses that have been sanitized for testing purposes.

Classes:
    JiraTestData: Static data provider for Jira API response simulation.

Typical usage example:
    fields = JiraTestData.get_fields_response()
    issues = JiraTestData.get_issues_response()
    changelog = JiraTestData.get_issue_status_changelogs()
"""

import json
import os

class JiraTestData:
    """
    Provider for pre-recorded Jira API response data used in unit testing.

    This class serves as a centralized access point for test data that simulates
    real Jira API responses. All data is loaded from JSON files that contain
    sanitized versions of actual Jira responses, ensuring tests work with
    realistic data structures and content.

    The class provides static methods for accessing different types of Jira data:
    - Field definitions and metadata
    - Issue data with various field types and values
    - Status change logs and workflow transitions

    Class Attributes:
        BASE_PATH (str): Absolute path to the directory containing JSON test files
        ISSUES_FILE (str): Filename for issue response data
        FIELDS_FILE (str): Filename for field definition data
        STATUS_CHANGELOGS_FILE (str): Filename for status changelog data

    Note:
        All methods are class methods and don't require instantiation. The JSON
        files are loaded fresh on each call to ensure test isolation.

    Example:
        >>> fields = JiraTestData.get_fields_response()
        >>> len(fields) > 0  # True if test data is available
        >>> issues = JiraTestData.get_issues_response()
        >>> 'issues' in issues  # True for standard Jira response format
    """

    # Define the base path for test data
    BASE_PATH = os.path.join(os.path.dirname(__file__), 'json')

    ISSUES_FILE = 'issues.json'
    FIELDS_FILE = 'fields.json'
    STATUS_CHANGELOGS_FILE = 'status_changelogs.json'

    @classmethod
    def load_json_file(cls, filename: str) -> dict:
        """
        Load and parse a JSON test data file from the test data directory.

        This method handles the low-level file loading and JSON parsing for all
        test data files. It provides consistent error handling and ensures proper
        UTF-8 encoding for files that may contain international characters.

        Args:
            filename: Name of the JSON file to load (without path). Must exist
                     in the test data directory defined by BASE_PATH.

        Returns:
            Parsed JSON content as a Python dictionary or list, depending on
            the file structure.

        Raises:
            Exception: If the file cannot be found, read, or parsed as valid JSON.
                      The exception message includes the full file path and the
                      underlying error for debugging.

        Note:
            This is a utility method used by other class methods. Direct usage
            is discouraged in favor of the specific data access methods.

        Example:
            >>> data = JiraTestData.load_json_file('fields.json')
            >>> isinstance(data, list)  # True for fields data
        """
        file_path = os.path.join(cls.BASE_PATH, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            raise Exception(f"Failed to load test data from {file_path}: {str(e)}")

    @classmethod
    def get_fields_response(cls, test_session: str = "") -> list:
        """
        Retrieve Jira field definition test data.

        Returns pre-recorded field metadata that matches the structure returned
        by Jira's /rest/api/2/field endpoint. This includes both system fields
        (like summary, status, priority) and custom fields with their complete
        configuration details.

        The field data is essential for testing field type detection, value
        parsing, and export formatting functionality.

        Args:
            test_session: Optional identifier for different test scenarios.
                         Currently not used but maintained for interface
                         compatibility with mock classes.

        Returns:
            List of field definition dictionaries, each containing:
            - id: Field identifier (e.g., 'summary', 'customfield_10001')
            - name: Human-readable field name
            - custom: Boolean indicating if it's a custom field
            - schema: Field type and configuration information

        Raises:
            Exception: If the fields test data file cannot be loaded.

        Example:
            >>> fields = JiraTestData.get_fields_response()
            >>> summary_field = next(f for f in fields if f['id'] == 'summary')
            >>> summary_field['name']  # 'Summary'
            >>> summary_field['custom']  # False
        """
        return cls.load_json_file(cls.FIELDS_FILE)

    @classmethod
    def get_issues_response(cls) -> dict:
        """
        Retrieve sample Jira issue data for testing.

        Returns pre-recorded issue data that matches the structure returned by
        Jira's search endpoint (/rest/api/2/search). This includes complete
        issue objects with various field types, values, and edge cases that
        are commonly encountered in real Jira instances.

        The issue data is crucial for testing issue parsing, field extraction,
        data transformation, and export functionality across different scenarios.

        Returns:
            Dictionary containing the standard Jira search response structure:
            - issues: List of issue objects with complete field data
            - total: Total number of issues in the response
            - startAt: Starting index for pagination
            - maxResults: Maximum results per page

        Raises:
            Exception: If the issues test data file cannot be loaded.

        Note:
            The issues contain realistic field values including various data types
            (strings, arrays, objects, dates) and represent different issue types,
            statuses, and configurations commonly found in Jira projects.

        Example:
            >>> response = JiraTestData.get_issues_response()
            >>> issues = response['issues']
            >>> len(issues) > 0  # True if test data contains issues
            >>> first_issue = issues[0]
            >>> 'fields' in first_issue  # True - contains field data
        """
        return cls.load_json_file(cls.ISSUES_FILE)

    @classmethod
    def get_issue_status_changelogs(cls) -> dict:
        """
        Retrieve issue status change history for workflow testing.

        Returns pre-recorded changelog data that matches the structure returned
        by Jira's issue changelog endpoint. This data contains the complete
        history of status transitions, assignee changes, and other field
        modifications for sample issues.

        The changelog data is essential for testing workflow analysis, time
        tracking, and status transition reporting functionality.

        Returns:
            Dictionary containing changelog data with the following structure:
            - values: List of changelog entries, each containing:
              - created: Timestamp when the change occurred
              - author: User who made the change
              - items: List of individual field changes within the entry
                - field: Name of the changed field
                - fromString/toString: Human-readable old and new values
                - from/to: Raw field values before and after change

        Raises:
            Exception: If the changelog test data file cannot be loaded.

        Note:
            The changelog data represents realistic workflow patterns and timing
            that would be found in active Jira projects, including status
            transitions, assignee changes, and field updates.

        Example:
            >>> changelog = JiraTestData.get_issue_status_changelogs()
            >>> entries = changelog['values']
            >>> status_changes = [item for entry in entries 
            ...                   for item in entry['items'] 
            ...                   if item['field'] == 'status']
            >>> len(status_changes) > 0  # True if status changes exist
        """
        return cls.load_json_file(cls.STATUS_CHANGELOGS_FILE)