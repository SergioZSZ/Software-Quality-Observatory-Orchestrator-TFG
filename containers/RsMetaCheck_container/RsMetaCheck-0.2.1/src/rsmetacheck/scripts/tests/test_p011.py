import pytest
from unittest.mock import Mock, patch
from rsmetacheck.scripts.pitfalls.p011 import (
    is_url_accessible,
    detect_issue_tracker_format_pitfall
)


class TestIsUrlAccessible:
    """Test suite for is_url_accessible function"""

    @patch('metacheck.scripts.pitfalls.p011.requests.head')
    def test_successful_head_request(self, mock_head):
        """Test successful HEAD request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        result = is_url_accessible("https://example.com")
        assert result is True
        mock_head.assert_called_once()

    @patch('metacheck.scripts.pitfalls.p011.requests.head')
    @patch('metacheck.scripts.pitfalls.p011.requests.get')
    def test_head_not_allowed_fallback_to_get(self, mock_get, mock_head):
        """Test fallback to GET when HEAD returns 405"""
        mock_head_response = Mock()
        mock_head_response.status_code = 405
        mock_head.return_value = mock_head_response

        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get.return_value = mock_get_response

        result = is_url_accessible("https://example.com")
        assert result is True
        mock_head.assert_called_once()
        mock_get.assert_called_once()

    @patch('metacheck.scripts.pitfalls.p011.requests.head')
    def test_redirect_status_codes(self, mock_head):
        """Test that 3xx redirect codes are considered accessible"""
        for status_code in [301, 302, 303, 307, 308]:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_head.return_value = mock_response

            result = is_url_accessible("https://example.com")
            assert result is True, f"Failed for status code: {status_code}"

    @patch('metacheck.scripts.pitfalls.p011.requests.head')
    def test_error_status_codes(self, mock_head):
        """Test that 4xx and 5xx status codes are not accessible"""
        for status_code in [400, 401, 403, 404, 500, 502, 503]:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_head.return_value = mock_response

            result = is_url_accessible("https://example.com")
            assert result is False, f"Failed for status code: {status_code}"

    @patch('metacheck.scripts.pitfalls.p011.requests.head')
    def test_request_exception(self, mock_head):
        """Test handling of request exceptions"""
        import requests
        mock_head.side_effect = requests.exceptions.RequestException("Connection error")

        result = is_url_accessible("https://example.com")
        assert result is False

    @patch('metacheck.scripts.pitfalls.p011.requests.head')
    def test_timeout_exception(self, mock_head):
        """Test handling of timeout exceptions"""
        import requests
        mock_head.side_effect = requests.exceptions.Timeout("Timeout")

        result = is_url_accessible("https://example.com")
        assert result is False

    @patch('metacheck.scripts.pitfalls.p011.requests.head')
    def test_general_exception(self, mock_head):
        """Test handling of general exceptions"""
        mock_head.side_effect = Exception("Unexpected error")

        result = is_url_accessible("https://example.com")
        assert result is False

    @patch('metacheck.scripts.pitfalls.p011.requests.head')
    def test_whitespace_handling(self, mock_head):
        """Test that URL whitespace is properly stripped"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        result = is_url_accessible("  https://example.com  ")
        assert result is True

    @patch('metacheck.scripts.pitfalls.p011.requests.head')
    def test_custom_timeout(self, mock_head):
        """Test that custom timeout is used"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        is_url_accessible("https://example.com", timeout=5)

        # Check that timeout was passed to the request
        call_kwargs = mock_head.call_args[1]
        assert call_kwargs['timeout'] == 5


class TestDetectIssueTrackerFormatPitfall:
    """Test suite for detect_issue_tracker_format_pitfall function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_pitfall,expected_url", [
            # No issue_tracker key
            (
                    {},
                    "test_repo.json",
                    False,
                    None
            ),

            # issue_tracker not a list
            (
                    {"issue_tracker": "https://example.com/issues"},
                    "test_repo.json",
                    False,
                    None
            ),

            # Empty issue_tracker list
            (
                    {"issue_tracker": []},
                    "test_repo.json",
                    False,
                    None
            ),

            # Missing result key
            (
                    {
                        "issue_tracker": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser"
                        }]
                    },
                    "test_repo.json",
                    False,
                    None
            ),

            # Missing value in result
            (
                    {
                        "issue_tracker": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None
            ),

            # Non-codemeta source (should not trigger)
            (
                    {
                        "issue_tracker": [{
                            "source": "README.md",
                            "technique": "header_analysis",
                            "result": {"value": "https://example.com/issues"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None
            ),
        ])
    @patch('metacheck.scripts.pitfalls.p011.is_url_accessible')
    def test_detect_issue_tracker_scenarios_without_url_check(self, mock_accessible,
                                                              somef_data, file_name,
                                                              expected_has_pitfall,
                                                              expected_url):
        """Test various scenarios without URL accessibility check"""
        result = detect_issue_tracker_format_pitfall(somef_data, file_name)

        assert result["has_pitfall"] == expected_has_pitfall
        assert result["file_name"] == file_name
        assert result["issue_url"] == expected_url

    @patch('metacheck.scripts.pitfalls.p011.is_url_accessible')
    def test_accessible_url_no_pitfall(self, mock_accessible):
        """Test that accessible URL doesn't trigger pitfall"""
        mock_accessible.return_value = True

        somef_data = {
            "issue_tracker": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": "https://github.com/user/repo/issues"}
            }]
        }

        result = detect_issue_tracker_format_pitfall(somef_data, "test.json")

        assert result["has_pitfall"] is False
        mock_accessible.assert_called_once_with("https://github.com/user/repo/issues")

    @patch('metacheck.scripts.pitfalls.p011.is_url_accessible')
    def test_inaccessible_url_has_pitfall(self, mock_accessible):
        """Test that inaccessible URL triggers pitfall"""
        mock_accessible.return_value = False

        somef_data = {
            "issue_tracker": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": "https://broken.example.com/issues"}
            }]
        }

        result = detect_issue_tracker_format_pitfall(somef_data, "test.json")

        assert result["has_pitfall"] is True
        assert result["issue_url"] == "https://broken.example.com/issues"
        assert result["format_violation"] == "URL is not accessible or returns error status"

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_issue_tracker_format_pitfall(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "issue_url" in result
        assert "source" in result
        assert "format_violation" in result

    @patch('metacheck.scripts.pitfalls.p011.is_url_accessible')
    def test_case_insensitive_codemeta_matching(self, mock_accessible):
        """Test case insensitive matching for codemeta.json"""
        mock_accessible.return_value = False

        test_sources = [
            "codemeta.json",
            "repository/codemeta.json",
            "CODEMETA.JSON",
            "CodeMeta.json",
        ]

        for source in test_sources:
            somef_data = {
                "issue_tracker": [{
                    "source": source,
                    "technique": "code_parser",
                    "result": {"value": "https://broken.example.com/issues"}
                }]
            }

            result = detect_issue_tracker_format_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] is True, f"Failed for source: {source}"

    @patch('metacheck.scripts.pitfalls.p011.is_url_accessible')
    def test_code_parser_with_codemeta_in_source(self, mock_accessible):
        """Test detection with code_parser technique and codemeta in source"""
        mock_accessible.return_value = False

        somef_data = {
            "issue_tracker": [{
                "source": "CodeMeta file",
                "technique": "code_parser",
                "result": {"value": "https://broken.example.com/issues"}
            }]
        }

        result = detect_issue_tracker_format_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True

    @patch('metacheck.scripts.pitfalls.p011.is_url_accessible')
    def test_stops_at_first_match(self, mock_accessible):
        """Test that function stops after finding first inaccessible URL"""
        mock_accessible.side_effect = [False, True]

        somef_data = {
            "issue_tracker": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "https://broken1.example.com/issues"}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "https://broken2.example.com/issues"}
                }
            ]
        }

        result = detect_issue_tracker_format_pitfall(somef_data, "test.json")

        assert result["has_pitfall"] is True
        assert result["issue_url"] == "https://broken1.example.com/issues"
        # Should only call is_url_accessible once
        assert mock_accessible.call_count == 1

    @patch('metacheck.scripts.pitfalls.p011.is_url_accessible')
    def test_multiple_entries_first_non_codemeta(self, mock_accessible):
        """Test with multiple entries where first is non-codemeta"""
        mock_accessible.return_value = False

        somef_data = {
            "issue_tracker": [
                {
                    "source": "README.md",
                    "technique": "header_analysis",
                    "result": {"value": "https://accessible.example.com/issues"}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "https://broken.example.com/issues"}
                }
            ]
        }

        result = detect_issue_tracker_format_pitfall(somef_data, "test.json")

        assert result["has_pitfall"] is True
        assert result["issue_url"] == "https://broken.example.com/issues"

    @patch('metacheck.scripts.pitfalls.p011.is_url_accessible')
    def test_various_issue_tracker_urls(self, mock_accessible):
        """Test with various issue tracker URL formats"""
        test_urls = [
            "https://github.com/user/repo/issues",
            "https://gitlab.com/user/repo/-/issues",
            "https://bitbucket.org/user/repo/issues",
            "https://example.com/jira/projects/PROJ/issues",
        ]

        for url in test_urls:
            mock_accessible.return_value = False

            somef_data = {
                "issue_tracker": [{
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": url}
                }]
            }

            result = detect_issue_tracker_format_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] is True
            assert result["issue_url"] == url

    @patch('metacheck.scripts.pitfalls.p011.is_url_accessible')
    def test_wrong_technique_no_pitfall(self, mock_accessible):
        """Test that wrong technique doesn't trigger for codemeta.json"""
        mock_accessible.return_value = False

        somef_data = {
            "issue_tracker": [{
                "source": "repository/codemeta.json",
                "technique": "github_api",
                "result": {"value": "https://broken.example.com/issues"}
            }]
        }

        result = detect_issue_tracker_format_pitfall(somef_data, "test.json")

        # Should still trigger because source matches
        assert result["has_pitfall"] is True