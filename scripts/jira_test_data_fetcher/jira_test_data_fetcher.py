#!/usr/bin/env python3
# coding: utf8

"""
Jira test data fetcher for generating mock data for unit tests.

This script connects to a live Jira instance and downloads real data to create
comprehensive test fixtures. It fetches field definitions, issue data, and
status change logs, then saves them as JSON files in the test data directory.

The generated test data enables unit tests to run without requiring access to
a live Jira instance, ensuring consistent and reliable test execution.

Classes:
    JiraTestDataFetcher: Main class for fetching and saving Jira test data.

Environment Variables:
    JIRA_DOMAIN: Base URL of the Jira instance (e.g., https://company.atlassian.net)
    JIRA_USERNAME: Jira username or email address
    JIRA_API_TOKEN: Jira API token for authentication
    JIRA_QUERY: JQL query to select which issues to fetch (optional)
    JIRA_ISSUE_FIELDS: Comma-separated list of fields to include (optional)

Typical usage example:
    # Using environment variables
    export JIRA_DOMAIN="https://company.atlassian.net"
    export JIRA_USERNAME="user@company.com"
    export JIRA_API_TOKEN="your_api_token"
    python jira_test_data_fetcher.py

    # Using command line arguments
    python jira_test_data_fetcher.py -d "https://company.atlassian.net" \
        -u "user@company.com" -t "api_token" -q "project = TEST"
"""

import sys
import os
# Add the project root directory to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(PROJECT_ROOT)

import json
import logging
from atlassian import Jira
from argparse import ArgumentParser
from dotenv import load_dotenv

import importlib.util

spec = importlib.util.spec_from_file_location(
    "jira_test_data", 
    os.path.join(PROJECT_ROOT, "tests", "test_data", "jira_test_data.py")
)
jira_test_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jira_test_data)
JiraTestData = jira_test_data.JiraTestData

# Load environment variables from .env file
load_dotenv()

class JiraTestDataFetcher:
    """
    Fetches live Jira data and converts it to JSON test fixtures.

    This class connects to a Jira Cloud instance and downloads various types of
    data required for comprehensive unit testing. It handles authentication,
    data retrieval, and file output management automatically.

    The fetcher creates three types of test data files:
    - Field definitions (fields.json): Complete field metadata from Jira
    - Issue data (issues.json): Sample issues matching specified criteria
    - Status changelog (status_changelog.json): Change history for workflow testing

    Attributes:
        ISSUES_FILE (str): Filename for saved issue data
        FIELDS_FILE (str): Filename for saved field definitions  
        STATUS_CHANGELOG_FILE (str): Filename for saved status change data
        jira (Jira): Atlassian API client instance
        logger (Logger): Logging instance for debug output
        output_dir (str): Absolute path to test data output directory

    Example:
        >>> fetcher = JiraTestDataFetcher(
        ...     domain="https://company.atlassian.net",
        ...     username="user@company.com", 
        ...     api_token="your_token"
        ... )
        >>> fetcher.fetch_and_save_all("project = TEST", "summary,status")
    """

    def __init__(self, domain: str, username: str, api_token: str, project_root: str):
        """
        Initialize the Jira test data fetcher with connection parameters.

        Sets up the Jira API client, configures logging for debug output, and
        ensures the output directory exists for saving test data files. The
        output directory is automatically determined relative to the script location.

        Args:
            domain: Base URL of the Jira instance (e.g., 'https://company.atlassian.net')
            username: Jira username or email address for authentication
            api_token: Jira API token (not password) for secure authentication

        Raises:
            ConnectionError: If unable to connect to the specified Jira domain
            AuthenticationError: If credentials are invalid

        Note:
            This class assumes Jira Cloud and uses API token authentication.
            Server/Data Center instances may require different authentication.
        """
        self.jira = Jira(
            url=domain,
            username=username,
            password=api_token,
            cloud=True
        )
        # Set up logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)

        # Define output directory for test data
        self.output_dir = os.path.join(
            project_root,
            'tests', 'test_data', 'json'
        )
        self.logger.info(f"Output directory: {self.output_dir}")
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_and_save_all(self, jql_query: str, fields: str) -> None:
        """
        Orchestrate the complete test data fetching process.

        This method executes the full workflow to generate all required test data:
        1. Fetches field definitions from Jira
        2. Retrieves sample issues based on the provided JQL query
        3. Downloads status changelog for one of the fetched issues

        The order matters because status changelog fetching depends on having
        issue data available to select a sample issue ID.

        Args:
            jql_query: JQL (Jira Query Language) string to filter which issues to fetch.
                      Can be None to use default query or system configuration.
            fields: Comma-separated string of field names to include in issue data.
                   Can be None to fetch all available fields.

        Raises:
            JiraError: If any of the Jira API calls fail
            FileNotFoundError: If unable to create output directory
            PermissionError: If insufficient permissions to write output files

        Example:
            >>> fetcher.fetch_and_save_all(
            ...     jql_query="project = TEST AND status != Done",
            ...     fields="summary,status,assignee,created"
            ... )
        """
        self.fetch_fields()
        self.fetch_issues(jql_query, fields)
        self.fetch_status_changelog()

    def fetch_fields(self):
        """
        Retrieve complete field definitions from Jira and save as JSON.

        Downloads metadata for all available fields in the Jira instance, including
        both system fields (like summary, status) and custom fields. This data is
        essential for understanding field types, allowed values, and configuration
        options when parsing issues.

        The saved data includes field IDs, names, types, schemas, and configuration
        details that are used by the issue parser to correctly handle different
        field types during export operations.

        Raises:
            JiraError: If the field metadata request fails
            JSONDecodeError: If the response cannot be parsed
            IOError: If unable to write the output file

        Note:
            Field definitions are relatively stable but may change when custom
            fields are added, removed, or reconfigured in Jira.
        """
        fields = self.jira.get_all_fields()
        self._save_json(JiraTestData.FIELDS_FILE, fields)

    def fetch_issues(self, jql_query: str, fields: str):
        """
        Retrieve sample issues from Jira based on specified criteria.

        Executes a JQL query to fetch issues that match the given criteria and
        returns only the specified fields. This creates realistic test data that
        reflects the actual structure and content of issues in the Jira instance.

        The fetched issues serve as test fixtures for validating issue parsing,
        field extraction, and export functionality without requiring live API
        access during unit tests.

        Args:
            jql_query: JQL query string to filter issues. If None or empty,
                      may fetch recent issues or use a default query.
            fields: Comma-separated field names to include in the response.
                   If None or empty, all available fields are returned.

        Raises:
            JiraError: If the JQL query is invalid or the request fails
            ValueError: If the fields parameter contains invalid field names
            IOError: If unable to save the response data

        Example:
            >>> fetcher.fetch_issues(
            ...     jql_query="project = TEST ORDER BY created DESC",
            ...     fields="summary,status,assignee,priority,created"
            ... )

        Note:
            Large result sets may be paginated by the Jira API. The enhanced_jql
            method handles pagination automatically.
        """
        issues = self.jira.enhanced_jql(jql_query, fields=fields)
        self._save_json(JiraTestData.ISSUES_FILE, issues)

    def fetch_status_changelog(self):
        """
        Download status change history for a sample issue to test workflow parsing.

        Retrieves the complete changelog for the first issue from the previously
        fetched issues data. This provides realistic workflow transition data
        for testing status tracking, time-in-status calculations, and workflow
        analysis features.

        The changelog includes details about who made changes, when they occurred,
        and what the previous and new values were for each status transition.

        Raises:
            FileNotFoundError: If the issues file hasn't been created yet
            JSONDecodeError: If the issues file is corrupted
            JiraError: If the changelog request fails
            IndexError: If no issues were found in the issues data

        Dependencies:
            This method requires that fetch_issues() has been called first and
            successfully created the issues.json file with at least one issue.

        Note:
            Only fetches changelog for the first issue to minimize API calls
            while still providing comprehensive test data for workflow features.
        """
        # Get first issue from issues response to fetch its changelog
        issues_file = os.path.join(self.output_dir, JiraTestData.ISSUES_FILE)
        with open(issues_file, 'r') as f:
            issues_data = json.load(f)
        
        status_changelogs = {}
        if issues_data.get('issues'):
            for issue in issues_data['issues']:
                issue_id = issue['id']
                status_changelogs[issue_id] = self.jira.get_issue_status_changelog(issue_id)
            self._save_json(JiraTestData.STATUS_CHANGELOGS_FILE, status_changelogs)

    def _save_json(self, filename: str, data: dict):
        """
        Save data to a formatted JSON file in the test data directory.

        Writes the provided data structure to a JSON file with consistent formatting
        (2-space indentation, UTF-8 encoding, non-ASCII characters preserved).
        This ensures test data files are human-readable and can be easily inspected
        or modified for testing edge cases.

        Args:
            filename: Name of the file to create (without path)
            data: Python data structure to serialize as JSON

        Raises:
            IOError: If unable to write to the output directory
            TypeError: If the data contains non-serializable objects
            UnicodeEncodeError: If encoding issues occur (rare with UTF-8)

        Note:
            Files are saved to the predetermined output directory and will
            overwrite existing files with the same name.
        """
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {filename}")


def main():
    """
    Command-line entry point for the Jira test data fetcher.

    Handles argument parsing, environment variable loading, parameter validation,
    and orchestrates the complete test data fetching workflow. Supports both
    command-line arguments and environment variables for configuration.

    Command-line arguments take precedence over environment variables, allowing
    for flexible usage in different contexts (development, CI/CD, manual execution).

    Environment Variables (with command-line equivalents):
        JIRA_DOMAIN (-d/--domain): Jira instance URL
        JIRA_USERNAME (-u/--username): Authentication username  
        JIRA_API_TOKEN (-t/--api-token): API token for authentication
        JIRA_QUERY (-q/--jql): JQL query for issue selection (optional)
        JIRA_ISSUE_FIELDS (-f/--fields): Comma-separated field list (optional)

    Exit Codes:
        0: Successful completion
        2: Missing required parameters or argument parsing error

    Examples:
        # Using environment variables
        $ export JIRA_DOMAIN="https://company.atlassian.net"
        $ export JIRA_USERNAME="user@company.com"  
        $ export JIRA_API_TOKEN="your_token"
        $ python jira_test_data_fetcher.py

        # Using command-line arguments
        $ python jira_test_data_fetcher.py \\
            --domain "https://company.atlassian.net" \\
            --username "user@company.com" \\
            --api-token "your_token" \\
            --jql "project = TEST AND status != Done" \\
            --fields "summary,status,assignee"

    Raises:
        SystemExit: If required parameters are missing or invalid
    """
    parser = ArgumentParser(description='Fetch Jira test data')
    parser.add_argument('-d', '--domain', help='Jira domain URL')
    parser.add_argument('-u', '--username', help='Jira username')
    parser.add_argument('-t', '--api-token', help='Jira API token')
    parser.add_argument('-q', '--jql', help='JQL query to fetch issues')
    parser.add_argument('-f', '--fields', help='Comma-separated list of issue fields to fetch')
    
    args = parser.parse_args()
    
    # Use environment variables with fallback to command line arguments
    domain = args.domain or os.getenv('JIRA_DOMAIN')
    username = args.username or os.getenv('JIRA_USERNAME')
    api_token = args.api_token or os.getenv('JIRA_API_TOKEN')
    jql_query = args.jql or os.getenv('JIRA_QUERY')
    fields = args.fields or os.getenv('JIRA_ISSUE_FIELDS')

    # Validate that we have all required values
    if not all([domain, username, api_token]):
        parser.error("Missing required parameters. Provide either command line arguments or environment variables "
                    "(JIRA_DOMAIN, JIRA_USERNAME, JIRA_API_TOKEN)")

    fetcher = JiraTestDataFetcher(domain, username, api_token, PROJECT_ROOT)
    fetcher.fetch_and_save_all(jql_query, fields)


if __name__ == '__main__':
    main()