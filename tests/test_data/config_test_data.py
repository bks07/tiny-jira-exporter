import json
import os

class ConfigTestData:
    """
    Test data class that mimics Jira API responses loaded from JSON files.

    This class provides methods to load test data from JSON files stored in the `json` directory.
    """

    # Define the base path for test data
    BASE_PATH = os.path.join(os.path.dirname(__file__), 'json')

    @classmethod
    def load_json_file(cls, filename: str) -> dict:
        """
        Load a JSON file from the test data directory.

        :param filename: The name of the JSON file to load.
        :type filename: str
        :return: The contents of the JSON file as a dictionary.
        :rtype: dict
        :raises Exception: If the file cannot be loaded or parsed.
        """
        file_path = os.path.join(cls.BASE_PATH, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            raise Exception(f"Failed to load test data from {file_path}: {str(e)}")

    @classmethod
    def get_config(cls, test_session: str = "") -> list:
        """
        Get the configuration test data.

        :param test_session: An optional test session identifier to customize the data loading (default is an empty string).
        :type test_session: str
        :return: The configuration test data as a list.
        :rtype: list
        """
        return cls.load_json_file('config.json')