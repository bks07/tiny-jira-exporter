from tests.test_data.jira_test_data import JiraTestData

class JiraMock:
    """
    Mock implementation of Jira API client for testing purposes.

    Simulates the behavior of the atlassian-python-api Jira client by returning
    predefined test data instead of making actual HTTP requests. This enables
    reliable, fast unit testing without external dependencies or network calls.

    The mock supports different test scenarios through configurable test sessions,
    allowing tests to verify behavior with various data sets and edge cases.

    Example:
        jira_mock = JiraMock()
        jira_mock.test_session = "basic_test"
        fields = jira_mock.get_all_fields()
        issues = jira_mock.enhanced_jql("project = TEST")

    Attributes:
        __test_session: Current test session identifier for data selection.
        __status_changelogs: Cached status changelog data for performance.
    """

    def __init__(self, url=None, username=None, password=None, cloud=True):
        """
        Initialize a new JiraMock instance with connection parameters.

        Accepts the same parameters as the real Jira client for compatibility,
        but these parameters are ignored since no actual connection is made.
        The mock starts with an empty test session and lazy-loaded changelog data.

        Args:
            url: Jira instance URL (ignored in mock, for API compatibility).
            username: Jira username (ignored in mock, for API compatibility).
            password: Jira password or API token (ignored in mock, for API compatibility).
            cloud: Whether Jira instance is cloud-based (ignored in mock, for API compatibility).
        """
        self.__test_session: str = ""
        self.__status_changelogs: dict = None

    @property
    def test_session(self) -> str:
        """
        Get the current test session identifier.

        The test session determines which set of test data will be returned
        by the mock's API methods. Different sessions can simulate various
        Jira configurations, data sets, and edge cases for comprehensive testing.

        Returns:
            Current test session identifier string.
        """
        return self.__test_session

    @test_session.setter
    def test_session(self, value: str) -> None:
        """
        Set the test session identifier for data selection.

        Changes the active test session, which determines what test data
        will be returned by subsequent API calls. This allows tests to
        easily switch between different data scenarios and configurations.

        Args:
            value: Test session identifier to activate.
        """
        self.__test_session = value

    def get_all_fields(self):
        """
        Mock Jira's get_all_fields API to return field metadata.

        Simulates the Jira REST API endpoint that retrieves all available
        fields for the instance, including both standard and custom fields.
        Returns predefined test data based on the current test session.

        Returns:
            List of field dictionaries containing field metadata such as
            id, name, schema type, and other field properties.
        """
        return JiraTestData.get_fields_response(self.test_session)

    def enhanced_jql(self, jql_query, fields=None):
        """
        Mock Jira's enhanced JQL search API to return issue data.

        Simulates the atlassian-python-api's enhanced_jql method that executes
        JQL queries and returns matching issues. The mock ignores the actual
        query parameters and returns predefined test data based on the current
        test session, enabling consistent test results.

        Args:
            jql_query: JQL query string (ignored in mock, for API compatibility).
            fields: List of field IDs to include (ignored in mock, for API compatibility).

        Returns:
            Dictionary containing 'issues' key with list of issue data matching
            the expected Jira API response format.
        """
        return JiraTestData.get_issues_response(self.test_session)

    def get_issue_status_changelog(self, issue_id):
        """
        Mock Jira's issue changelog API for status transition history.

        Simulates retrieving an issue's status change history, which is used
        for workflow analysis and time-in-status calculations. Uses cached
        changelog data for performance and returns issue-specific transition
        records based on the provided issue ID.

        Args:
            issue_id: Jira issue ID to get changelog for (used for data lookup).

        Returns:
            List of changelog entries containing status transition data,
            or empty list if no changelog exists for the given issue ID.
        """
        if self.__status_changelogs is None:
            self.__status_changelogs = JiraTestData.get_issue_status_changelogs()
        return self.__status_changelogs.get(issue_id, [])