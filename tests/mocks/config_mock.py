"""
Mock implementation for configuration handling in unit tests.

This module provides a mock version of the ExporterConfig class that returns
predefined test data instead of parsing YAML files or making API calls. This
enables unit tests to run consistently and in isolation without external dependencies.

Classes:
    ConfigMock: Test double for ExporterConfig that provides static test data.

Typical usage example:
    config_mock = ConfigMock()
    config_mock.test_session = "basic_fields"
    fields = config_mock.get_all_fields()
"""

from tests.test_data.config_test_data import ConfigTestData

class ConfigMock:
    """
    Test mock for the ExporterConfig class used in unit testing.

    This mock class simulates the behavior of the ExporterConfig class by providing
    test data instead of parsing actual YAML configuration files or making real API calls.
    It allows tests to run in isolation with predictable data sets without requiring
    external dependencies like configuration files or network connections.

    The mock supports different test scenarios through the test_session property,
    which determines which set of test data is returned by the mock methods.

    Attributes:
        test_session (str): Identifier for the current test scenario, used to
                           select appropriate test data from ConfigTestData.

    Note:
        This class mimics the interface of ExporterConfig but returns static test data
        instead of performing actual configuration parsing or API interactions.
    """

    def __init__(
            self,
            yaml_file_location: str = "",
            logger: object = None,
            shall_pretty_print: bool = False
        ):
        """
        Initialize the configuration mock with the same signature as ExporterConfig.

        All parameters are accepted for interface compatibility but are ignored since
        this mock doesn't perform actual configuration parsing or logging operations.
        The mock starts with an empty test session that should be set before use.

        Args:
            yaml_file_location: Path to YAML config file (ignored in mock).
            logger: Logger instance for debugging (ignored in mock).
            shall_pretty_print: Enable pretty printing (ignored in mock).

        Note:
            Unlike the real ExporterConfig, this mock doesn't validate parameters
            or raise exceptions for missing configuration files.
        """
        self.__test_session: str = ""

    @property
    def test_session(self) -> str:
        """
        Get the current test session identifier.

        The test session determines which set of test data will be returned
        by mock methods. Different sessions can simulate various API responses
        or configuration scenarios for comprehensive testing.

        Returns:
            The active test session identifier. Empty string if not set.

        Example:
            >>> mock = ConfigMock()
            >>> mock.test_session = "complex_fields"
            >>> session = mock.test_session
            >>> print(session)
            'complex_fields'
        """
        return self.__test_session
    
    @test_session.setter
    def test_session(self, value: str) -> None:
        """
        Set the test session identifier to control which test data is returned.

        This property allows tests to switch between different data scenarios
        without creating new mock instances. The session identifier should
        correspond to available test data sets in ConfigTestData.

        Args:
            value: Test session identifier that determines the data set to use.
                  Should match available sessions in ConfigTestData.

        Raises:
            No validation is performed - invalid session IDs will result in
            empty or default data being returned by mock methods.

        Example:
            >>> mock = ConfigMock()
            >>> mock.test_session = "basic_fields"  # Switch to basic field set
            >>> mock.test_session = "custom_fields"  # Switch to custom field set
        """
        self.__test_session = value
    
    def get_all_fields(self):
        """
        Retrieve mock field configuration data for the current test session.

        This method simulates the ExporterConfig.get_all_fields() behavior by
        returning predefined test data instead of parsing actual configuration
        or making API calls. The returned data structure matches what the real
        method would provide.

        Returns:
            List of field configuration dictionaries corresponding to the current
            test session. The structure and content depend on the active test_session.
            Returns empty list or default data for unrecognized sessions.

        Note:
            Unlike the real implementation, this method never raises exceptions
            and doesn't validate the test session identifier.

        Example:
            >>> mock = ConfigMock()
            >>> mock.test_session = "basic_fields"
            >>> fields = mock.get_all_fields()
            >>> len(fields) > 0  # True if test data exists for "basic_fields"
        """
        return ConfigTestData.get_fields_response(self.test_session)
