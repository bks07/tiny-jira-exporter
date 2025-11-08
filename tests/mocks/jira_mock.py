from tests.test_data.jira_test_data import JiraTestData

class JiraMock:
    """
    Mock class that simulates Jira API responses.

    This class is used to mock Jira API calls for testing purposes. It retrieves test data
    from the `JiraTestData` class, which loads data from JSON files.
    """

    def __init__(self, url=None, username=None, password=None, cloud=True):
        """
        Initialize the JiraMock instance.

        :param url: The Jira instance URL (not used in the mock).
        :type url: str, optional
        :param username: The Jira username (not used in the mock).
        :type username: str, optional
        :param password: The Jira password or API token (not used in the mock).
        :type password: str, optional
        :param cloud: Whether the Jira instance is cloud-based (not used in the mock).
        :type cloud: bool, optional
        """
        self.__test_session: str = ""
        self.__status_changelogs: dict = None

    @property
    def test_session(self) -> str:
        """
        Get the current test session identifier.

        :return: The test session identifier.
        :rtype: str
        """
        return self.__test_session

    @test_session.setter
    def test_session(self, value: str) -> None:
        """
        Set the test session identifier.

        :param value: The test session identifier to set.
        :type value: str
        """
        self.__test_session = value

    def get_all_fields(self):
        """
        Simulate the Jira API call to retrieve all fields.

        :return: The fields test data for the current test session.
        :rtype: list
        """
        return JiraTestData.get_fields_response(self.test_session)

    def enhanced_jql(self, jql_query, fields=None):
        """
        Simulate the Jira API call to execute a JQL query.

        :param jql_query: The JQL query string (not used in the mock).
        :type jql_query: str
        :param fields: The fields to include in the response (not used in the mock).
        :type fields: list, optional
        :return: The issues test data for the current test session.
        :rtype: dict
        """
        return JiraTestData.get_issues_response(self.test_session)

    def get_issue_status_changelog(self, issue_id):
        """
        Simulate the Jira API call to retrieve the status changelog for an issue.

        :param issue_id: The ID of the issue (not used in the mock).
        :type issue_id: str
        :return: The status changelog test data for the current test session.
        :rtype: list
        """
        if self.__status_changelogs is None:
            self.__status_changelogs = JiraTestData.get_issue_status_changelogs()
        return self.__status_changelogs.get(issue_id, [])