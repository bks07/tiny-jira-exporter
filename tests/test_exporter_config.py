"""
Unit tests for the ExporterConfig class.

Tests configuration file parsing, validation, and data access methods
using both valid and invalid configuration scenarios.
"""

import unittest
import tempfile
import os
import yaml
import logging
from unittest.mock import patch, MagicMock

from modules.exporter_config.exporter_config import ExporterConfig


class TestExporterConfig(unittest.TestCase):
    """Test suite for ExporterConfig class functionality."""

    def setUp(self):
        """Set up test fixtures and common test data."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.CRITICAL)  # Suppress log output during tests
        
        # Sample valid configuration data
        self.valid_config = {
            'Connection': {
                'Domain': 'https://test.atlassian.net',
                'Username': 'test@example.com',
                'API Token': 'test_token_123'
            },
            'Search Criteria': {
                'Projects': ['TEST'],
                'Issue Types': ['Story', 'Bug'],
                'Max Results': 100
            },
            'Export': {
                'Field Separator': ',',
                'Decimal Separator': '.',
                'Time Zone': 'UTC'
            }
        }
        
        # Path to existing test config for integration tests
        self.test_config_path = os.path.join(
            os.path.dirname(__file__), 
            'test_data', 'yaml', 'test_config.yaml'
        )

    def _create_temp_config_file(self, config_data):
        """Create a temporary YAML file with the given configuration data."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(config_data, temp_file, default_flow_style=False)
        temp_file.close()
        return temp_file.name

    def _cleanup_temp_file(self, filepath):
        """Remove temporary file if it exists."""
        if filepath and os.path.exists(filepath):
            os.unlink(filepath)

    def test_init(self):
        """Test ExporterConfig initialization with a valid configuration file."""
        try:
            config = ExporterConfig(
                logger=self.logger,
                shall_pretty_print=False
            )
            self.assertIsNotNone(config)
        finally:
            self._cleanup_temp_file(config_file)

    def test_load_yaml_file_with_nonexistent_file(self):
        """Test that ExporterConfig raises appropriate error for missing file."""
        with self.assertRaises((FileNotFoundError, ValueError)):
            config = ExporterConfig(
                logger=self.logger,
                shall_pretty_print=False
            )
            config.load_yaml_file(file_location='/nonexistent/path/config.yaml')

    def test_load_yaml_file_with_invalid_yaml(self):
        """Test that ExporterConfig handles invalid YAML gracefully."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        temp_file.write("invalid: yaml: content: [unclosed")
        temp_file.close()
        
        try:
            with self.assertRaises((yaml.YAMLError, ValueError)):
                config = ExporterConfig(
                    logger=self.logger,
                    shall_pretty_print=False
                )
                config.load_yaml_file(file_location=temp_file.name)
        finally:
            self._cleanup_temp_file(temp_file.name)

    def test_get_connection_details(self):
        """Test retrieval of connection configuration."""
        config_file = self._create_temp_config_file(self.valid_config)
        try:
            config = ExporterConfig(
                logger=self.logger,
                shall_pretty_print=False
            )
            config.load_yaml_file(file_location=config_file)
            
            # Test connection properties
            self.assertEqual(config.domain, 'https://test.atlassian.net')
            self.assertEqual(config.username, 'test@example.com')
            self.assertEqual(config.api_token, 'test_token_123')
            
        finally:
            self._cleanup_temp_file(config_file)

    def test_get_search_criteria(self):
        """Test retrieval of search criteria configuration."""
        config_file = self._create_temp_config_file(self.valid_config)
        try:
            config = ExporterConfig(
                logger=self.logger,
                shall_pretty_print=False
            )
            config.load_yaml_file(file_location=config_file)
            
            # Test JQL query (may be constructed from projects/issue types)
            jql = config.jql_query
            self.assertIsInstance(jql, str)
            
        finally:
            self._cleanup_temp_file(config_file)

    def test_get_export_settings(self):
        """Test retrieval of export configuration."""
        config_file = self._create_temp_config_file(self.valid_config)
        try:
            config = ExporterConfig(
                logger=self.logger,
                shall_pretty_print=False
            )
            config.load_yaml_file(file_location=config_file)

            # Test field prefix properties
            standard_prefix = config.standard_field_prefix
            custom_prefix = config.custom_field_prefix
            postfix = config.issue_field_id_postfix
            
            self.assertIsInstance(standard_prefix, str)
            self.assertIsInstance(custom_prefix, str)
            self.assertIsInstance(postfix, str)
            
        finally:
            self._cleanup_temp_file(config_file)

    def test_integration_with_real_test_config(self):
        """Test ExporterConfig with the actual test configuration file."""
        if not os.path.exists(self.test_config_path):
            self.skipTest("Test config file not found")
            
        config = ExporterConfig(
            logger=self.logger,
            shall_pretty_print=False
        )
        config.load_yaml_file(file_location=self.test_config_path)

        self.assertIsNotNone(config)
        # Add specific assertions based on the content of kswd_test_config.yaml

    def test_missing_required_sections(self):
        """Test handling of configuration files missing required sections."""
        incomplete_configs = [
            {},  # Empty config
            {'Connection': {}},  # Missing Search Criteria
            {'Search Criteria': {}},  # Missing Connection
        ]
        
        for incomplete_config in incomplete_configs:
            config_file = self._create_temp_config_file(incomplete_config)
            try:
                with self.assertRaises(ValueError):
                    config = ExporterConfig(
                        logger=self.logger,
                        shall_pretty_print=False
                    )
                    config.load_yaml_file(file_location=config_file)
            finally:
                self._cleanup_temp_file(config_file)

    @patch('modules.exporter_config.exporter_config.yaml.safe_load')
    def test_yaml_parsing_error_handling(self, mock_yaml_load):
        """Test error handling when YAML parsing fails."""
        mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")
        
        config_file = self._create_temp_config_file(self.valid_config)
        try:
            with self.assertRaises((yaml.YAMLError, ValueError)):
                config = ExporterConfig(
                    logger=self.logger,
                    shall_pretty_print=False
                )
                config.load_yaml_file(file_location=config_file)
        finally:
            self._cleanup_temp_file(config_file)

    def test_pretty_print_functionality(self):
        """Test that pretty print option works without errors."""
        config_file = self._create_temp_config_file(self.valid_config)
        try:
            # This should not raise an exception
            config = ExporterConfig(
                logger=self.logger,
                shall_pretty_print=True
            )
            config.load_yaml_file(file_location=config_file)
            self.assertIsNotNone(config)
        finally:
            self._cleanup_temp_file(config_file)

    def test_field_configuration_parsing(self):
        """Test parsing of field configuration sections."""
        config_with_fields = {
            **self.valid_config,
            'Fields': {
                'Standard Fields': ['summary', 'status', 'assignee'],
                'Custom Fields': ['customfield_10001', 'customfield_10002']
            }
        }
        
        config_file = self._create_temp_config_file(config_with_fields)
        try:
            config = ExporterConfig(
                logger=self.logger,
                shall_pretty_print=False
            )
            config.load_yaml_file(file_location=config_file)

            # Test field configuration properties
            standard_fields = config.standard_issue_fields
            custom_fields = config.custom_issue_fields
            
            self.assertIsInstance(standard_fields, dict)
            self.assertIsInstance(custom_fields, dict)
            
            # Test field prefixes and postfixes
            standard_prefix = config.standard_field_prefix
            custom_prefix = config.custom_field_prefix
            postfix = config.issue_field_id_postfix
            
            self.assertIsInstance(standard_prefix, str)
            self.assertIsInstance(custom_prefix, str)
            self.assertIsInstance(postfix, str)
                
        finally:
            self._cleanup_temp_file(config_file)


class TestExporterConfigEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for ExporterConfig."""

    def setUp(self):
        """Set up test fixtures for edge case testing."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.CRITICAL)

    def test_empty_string_values(self):
        """Test handling of empty string values in configuration."""
        config_with_empty_values = {
            'Connection': {
                'Domain': '',
                'Username': '',
                'API Token': ''
            },
            'Search Criteria': {
                'Projects': [],
                'Max Results': 0
            }
        }
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(config_with_empty_values, temp_file, default_flow_style=False)
        temp_file.close()
        
        try:
            # Should handle empty values gracefully or raise appropriate error
            with self.assertRaises(ValueError):
                config = ExporterConfig(
                    logger=self.logger,
                    shall_pretty_print=False
                )
                config.load_yaml_file(file_location=temp_file.name)
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def test_very_large_config_file(self):
        """Test performance with a large configuration file."""
        large_config = {
            'Connection': {
                'Domain': 'https://test.atlassian.net',
                'Username': 'test@example.com',
                'API Token': 'test_token_123'
            },
            'Search Criteria': {
                'Projects': [f'PROJ{i}' for i in range(1000)],  # Large project list
                'Issue Types': ['Story', 'Bug', 'Task'],
                'Max Results': 10000
            }
        }
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(large_config, temp_file, default_flow_style=False)
        temp_file.close()
        
        try:
            # Should handle large configs without issues
            config = ExporterConfig(
                logger=self.logger,
                shall_pretty_print=False
            )
            config.load_yaml_file(file_location=temp_file.name)
            self.assertIsNotNone(config)
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


if __name__ == '__main__':
    unittest.main()