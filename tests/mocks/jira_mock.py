from tests.test_data.jira_test_data import JiraTestData

class JiraMock:
    """Mock class that simulates Jira API responses"""
    
    def __init__(self, url=None, username=None, password=None, cloud=True):
        self.__test_session:str = ""
        pass


    @property
    def test_session(self) -> str:
        return self.__test_session
    
    @test_session.setter
    def test_session(self, value: str) -> None:
        self.__test_session = value
    

    def get_all_fields(self):
        return JiraTestData.get_fields_response(self.test_session)

    def enhanced_jql(self, jql_query, fields=None):
        return JiraTestData.get_issues_response(self.test_session)

    def get_issue_status_changelog(self, issue_id):
        return JiraTestData.get_status_changelog(self.test_session)