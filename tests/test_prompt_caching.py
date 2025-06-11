#!/usr/bin/env python3
"""
Tests for prompt caching optimization.

This test verifies that the large prompt template is cached as a class constant
instead of being reconstructed on every AI call.
"""

import unittest
import time
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import screenshot_monitor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from screenshot_monitor import ScreenshotMonitor


class TestPromptCaching(unittest.TestCase):
    """Test prompt template caching optimization"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the AWS client to avoid needing credentials
        with patch('boto3.client') as mock_boto:
            mock_boto.return_value = MagicMock()
            self.monitor = ScreenshotMonitor(storage_dir="test_screenshots", model_name="claude-4-sonnet")
    
    def test_prompt_template_exists(self):
        """Test that the prompt template constant exists and is properly formatted"""
        # Check that the class constant exists
        self.assertTrue(hasattr(ScreenshotMonitor, '_ANALYSIS_PROMPT_TEMPLATE'))
        
        # Check that it's a string and not empty
        template = ScreenshotMonitor._ANALYSIS_PROMPT_TEMPLATE
        self.assertIsInstance(template, str)
        self.assertGreater(len(template), 500)  # Should be 500+ characters as mentioned in OPTIMIZATIONS.md
        
        # Check that it contains the URL placeholder
        self.assertIn('{url}', template)
        
        # Check that it contains key components of the prompt
        self.assertIn('website monitoring expert', template)
        self.assertIn('JSON format', template)
        self.assertIn('has_changes', template)
        self.assertIn('deployment monitoring', template)
    
    def test_prompt_formatting(self):
        """Test that prompt formatting works correctly with URLs"""
        template = ScreenshotMonitor._ANALYSIS_PROMPT_TEMPLATE
        test_url = "https://example.com"
        
        # Format the template
        formatted_prompt = template.format(url=test_url)
        
        # Check that URL was properly inserted
        self.assertIn(test_url, formatted_prompt)
        self.assertNotIn('{url}', formatted_prompt)  # Placeholder should be replaced
        
        # Check that the rest of the prompt is intact
        self.assertIn('website monitoring expert', formatted_prompt)
        self.assertIn('JSON format', formatted_prompt)
    
    def test_multiple_url_formatting(self):
        """Test that template can be reused with different URLs"""
        template = ScreenshotMonitor._ANALYSIS_PROMPT_TEMPLATE
        
        urls = [
            "https://example.com",
            "https://google.com",
            "https://github.com/user/repo",
            "https://api.service.com/v1/endpoint"
        ]
        
        for url in urls:
            formatted_prompt = template.format(url=url)
            self.assertIn(url, formatted_prompt)
            self.assertNotIn('{url}', formatted_prompt)
            # Should still contain the same length approximately
            self.assertGreater(len(formatted_prompt), 500)
    
    @patch('screenshot_monitor.ScreenshotMonitor.encode_image_to_base64')
    def test_prompt_used_in_comparison(self, mock_encode):
        """Test that the cached prompt is used in actual comparison method"""
        # Mock the bedrock response
        mock_response = {
            'output': {
                'message': {
                    'content': [
                        {
                            'text': '{"has_changes": false, "severity": "none", "summary": "No changes detected"}'
                        }
                    ]
                }
            }
        }
        
        # Mock image encoding
        mock_encode.return_value = "fake_base64_data"
        
        # Mock the bedrock client's converse method
        self.monitor.bedrock.converse.return_value = mock_response
        
        # Call the comparison method
        test_url = "https://test-site.com"
        result = self.monitor.compare_with_claude("baseline.png", "current.png", test_url)
        
        # Verify bedrock was called
        self.assertTrue(self.monitor.bedrock.converse.called)
        
        # Get the actual prompt that was sent
        call_args = self.monitor.bedrock.converse.call_args
        messages = call_args[1]['messages']
        actual_prompt = messages[0]['content'][0]['text']
        
        # Verify the URL was inserted correctly
        self.assertIn(test_url, actual_prompt)
        self.assertIn('website monitoring expert', actual_prompt)
    
    def test_prompt_consistency_and_reuse(self):
        """Test that cached template produces consistent results and demonstrates reusability"""
        test_url = "https://example.com"
        template = ScreenshotMonitor._ANALYSIS_PROMPT_TEMPLATE
        
        # The main benefit is avoiding string reconstruction in memory and maintaining consistency
        # Test that the template can be reused efficiently for multiple calls
        results = []
        for i in range(100):
            prompt = template.format(url=test_url)
            results.append(prompt)
        
        # All results should be identical
        self.assertTrue(all(prompt == results[0] for prompt in results))
        
        # Each prompt should contain the URL
        for prompt in results:
            self.assertIn(test_url, prompt)
            self.assertGreater(len(prompt), 500)
        
        # Compare with old f-string approach for content equivalence
        old_style_prompt = f"""You are a website monitoring expert analyzing screenshots for changes. I will provide you with two screenshots of the same website URL: {test_url}

The first image is the BASELINE (reference) screenshot.
The second image is the CURRENT screenshot taken more recently.

Please analyze these screenshots and provide a detailed comparison report in the following JSON format:

{{
    "has_changes": true/false,
    "severity": "none|minor|moderate|major|critical",
    "summary": "Brief summary of changes found",
    "changes_detected": [
        {{
            "type": "layout|content|styling|functionality|error|availability",
            "description": "Detailed description of the change",
            "location": "Where on the page this change occurs",
            "impact": "Potential impact of this change"
        }}
    ],
    "availability_status": "available|partially_available|unavailable|error",
    "recommendations": ["List of recommended actions if any issues found"]
}}

Focus on:
- Layout changes (elements moved, resized, disappeared)
- Content changes (text differences, images changed)
- Error messages or broken elements
- Overall site availability and functionality
- Visual styling changes
- Any elements that appear broken or missing

Be thorough but practical - highlight changes that would matter for deployment monitoring."""
        
        new_style_prompt = template.format(url=test_url)
        
        # Both approaches should produce identical content
        self.assertEqual(old_style_prompt, new_style_prompt)
        
        print(f"\n✅ Prompt Caching Optimization Validated:")
        print(f"   - Template length: {len(template)} characters")
        print(f"   - Generated prompt length: {len(new_style_prompt)} characters")
        print(f"   - Content consistency: ✅ Identical to f-string approach")
        print(f"   - Reusability: ✅ Template can be reused for multiple URLs")


if __name__ == "__main__":
    unittest.main() 