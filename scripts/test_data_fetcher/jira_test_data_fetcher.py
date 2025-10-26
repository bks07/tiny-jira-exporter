import json
import os
import sys
from atlassian import Jira
from argparse import ArgumentParser

class JiraTestDataFetcher:
    """Fetches test data from Jira and saves it as JSON files"""

    def __init__(self, domain: str, username: str, api_token: str):
        self.jira = Jira(
            url=domain,
            username=username,
            password=api_token,
            cloud=True
        )
        self.output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'tests', 'test_data', 'json'
        )
        print(f"Output directory: {self.output_dir}")
        sys.exit(0)
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_and_save_all(self):
        """Fetch all required test data and save to JSON files"""
        self.fetch_fields()
        self.fetch_issues()
        self.fetch_changelog()

    def fetch_fields(self):
        """Fetch field definitions from Jira"""
        fields = self.jira.get_all_fields()
        self._save_json('fields_response.json', fields)

    def fetch_issues(self):
        """Fetch sample issues from Jira"""
        # Modify JQL to fetch relevant test issues
        jql = 'project = "TEST" ORDER BY created DESC'
        issues = self.jira.jql(jql, limit=5)
        self._save_json('issues_response.json', issues)

    def fetch_changelog(self):
        """Fetch status changelog for a sample issue"""
        # Get first issue from issues response to fetch its changelog
        issues_file = os.path.join(self.output_dir, 'issues_response.json')
        with open(issues_file, 'r') as f:
            issues_data = json.load(f)
        
        if issues_data.get('issues'):
            issue_id = issues_data['issues'][0]['id']
            changelog = self.jira.get_issue_changelog(issue_id)
            self._save_json('status_changelog.json', changelog)

    def _save_json(self, filename: str, data: dict):
        """Save data to a JSON file"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {filename}")

def main():
    parser = ArgumentParser(description='Fetch Jira test data')
    parser.add_argument('-d', '--domain', help='Jira domain URL')
    parser.add_argument('-u', '--username', help='Jira username')
    parser.add_argument('-t', '--api-token', help='Jira API token')
    
    args = parser.parse_args()
    
    # Use environment variables with fallback to command line arguments
    domain = args.domain or os.getenv('JIRA_DOMAIN')
    username = args.username or os.getenv('JIRA_USERNAME')
    api_token = args.api_token or os.getenv('JIRA_API_TOKEN')
    
    # Validate that we have all required values
    if not all([domain, username, api_token]):
        parser.error("Missing required parameters. Provide either command line arguments or environment variables "
                    "(JIRA_DOMAIN, JIRA_USERNAME, JIRA_API_TOKEN)")
    
    fetcher = JiraTestDataFetcher(domain, username, api_token)
    fetcher.fetch_and_save_all()

if __name__ == '__main__':
    main()