import json
import os

class JiraTestData:
    """Test data that mimics Jira API responses loaded from JSON files"""
    
    # Define the base path for test data
    BASE_PATH = os.path.join(os.path.dirname(__file__), 'json')
    
    @classmethod
    def load_json_file(cls, filename: str) -> dict:
        """Load a JSON file from the test data directory"""
        file_path = os.path.join(cls.BASE_PATH, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            raise Exception(f"Failed to load test data from {file_path}: {str(e)}")
    
    @classmethod
    def get_fields_response(cls, test_session:str = "") -> list:
        """Get the fields test data"""
        return cls.load_json_file('fields_response.json')
    
    @classmethod
    def get_issues_response(cls) -> dict:
        """Get the issues test data"""
        return cls.load_json_file('issues_response.json')
    
    @classmethod
    def get_status_changelog(cls) -> list:
        """Get the changelog test data"""
        return cls.load_json_file('status_changelog.json')