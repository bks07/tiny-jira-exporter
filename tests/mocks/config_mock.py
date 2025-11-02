from tests.test_data.config_test_data import ConfigTestData

class ConfigMock:
    """
    Mock class that simulates configuration data for testing purposes.

    This class is used to mock configuration data, such as Jira API responses,
    by retrieving test data from the `ConfigTestData` class.
    """

    def __init__(
            self,
            yaml_file_location: str = "",
            logger: object = None,
            shall_pretty_print: bool = False
        ):
        """
        Initialize the ConfigMock instance.

        :param yaml_file_location: The path to the YAML configuration file (not used in the mock).
        :type yaml_file_location: str, optional
        :param logger: The logger instance for debugging (not used in the mock).
        :type logger: object, optional
        :param shall_pretty_print: Whether to enable pretty printing (not used in the mock).
        :type shall_pretty_print: bool, optional
        """
        self.__test_session: str = ""

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
        Simulate the retrieval of all fields from the configuration.

        :return: The fields test data for the current test session.
        :rtype: list
        """
        return ConfigTestData.get_fields_response(self.test_session)
