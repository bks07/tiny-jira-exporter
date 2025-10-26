import unittest
from modules.issue_parser.issue_parser import IssueParser
from modules.exporter_config.exporter_config import ExporterConfig
from tests.mocks.jira_mock import JiraMock
import logging

class TestIssueParser(unittest.TestCase):
    def setUp(self):
        config = ExporterConfig()
        logger = logging.getLogger(__name__)
        self.jira_mock = JiraMock()
        self.parser = IssueParser(config, logger, jira_instance=self.jira_mock)

    def test_fetch_issues(self):
        self.parser.fetch_issues()
        # Add assertions here