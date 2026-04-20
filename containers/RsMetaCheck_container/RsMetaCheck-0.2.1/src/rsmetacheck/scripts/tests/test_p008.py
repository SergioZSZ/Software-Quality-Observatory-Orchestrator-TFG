import pytest
from unittest.mock import Mock, patch
from rsmetacheck.scripts.pitfalls.p008 import (
    is_valid_url_format,
    check_url_status,
    extract_urls_from_requirements,
    detect_invalid_software_requirement_pitfall
)

class TestIsValidUrlFormat:
    """Test suite for is_valid_url_format function"""

    @pytest.mark.parametrize("url,expected", [
        # Valid URLs
        ("https://example.com", True),
        ("http://example.com", True),
        ("https://www.example.com/path", True),
        ("https://example.com:8080/path", True),

        # Invalid URLs
        ("example.com", False),
        ("www.example.com", False),
        ("/path/to/file", False),
        ("not a url", False),
        ("", False),
        ("   ", False),

        # Edge cases
        ("https://", False),
        ("http://", False),
        ("https://example", True),  # Valid but minimal
    ])
    def test_is_valid_url_format_scenarios(self, url, expected):
        """Test various URL format validation scenarios"""
        result = is_valid_url_format(url)
        assert result == expected, f"Failed for URL: {url}"

    def test_none_url_raises_error(self):
        """Test that None URL raises ValueError"""
        with pytest.raises(ValueError, match="URL cannot be None"):
            is_valid_url_format(None)

    def test_non_string_url(self):
        """Test that non-string URLs return False"""
        assert is_valid_url_format(123) is False
        assert is_valid_url_format([]) is False
        assert is_valid_url_format({}) is False


class TestCheckUrlStatus:
    """Test suite for check_url_status function"""

    @patch('metacheck.scripts.pitfalls.p008.requests.get')
    def test_successful_request(self, mock_get):
        """Test successful URL request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = check_url_status("https://example.com")

        assert result["is_accessible"] is True
        assert result["status_code"] == 200
        assert result["error"] is None

    @patch('metacheck.scripts.pitfalls.p008.requests.get')
    def test_redirect_status_code(self, mock_get):
        """Test that 301 redirects are considered accessible"""
        mock_response = Mock()
        mock_response.status_code = 301
        mock_get.return_value = mock_response

        result = check_url_status("https://example.com")

        assert result["is_accessible"] is True
        assert result["status_code"] == 301

    @patch('metacheck.scripts.pitfalls.p008.requests.get')
    def test_not_found_error(self, mock_get):
        """Test 404 Not Found status"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = check_url_status("https://example.com")

        assert result["is_accessible"] is False
        assert result["status_code"] == 404

    @patch('metacheck.scripts.pitfalls.p008.requests.get')
    def test_server_error(self, mock_get):
        """Test 500 server error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = check_url_status("https://example.com")

        assert result["is_accessible"] is False
        assert result["status_code"] == 500

    @patch('metacheck.scripts.pitfalls.p008.requests.get')
    def test_request_exception(self, mock_get):
        """Test handling of request exceptions"""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = check_url_status("https://example.com")

        assert result["is_accessible"] is False
        assert result["status_code"] is None
        assert "Connection error" in result["error"]

    def test_invalid_url_format(self):
        """Test with invalid URL format"""
        result = check_url_status("not a url")

        assert result["is_accessible"] is False
        assert result["error"] == "Invalid URL format"

    @patch('metacheck.scripts.pitfalls.p008.requests.get')
    def test_custom_timeout(self, mock_get):
        """Test that custom timeout is passed"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        check_url_status("https://example.com", timeout=5)

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs['timeout'] == 5

    @patch('metacheck.scripts.pitfalls.p008.requests.get')
    def test_user_agent_header(self, mock_get):
        """Test that User-Agent header is set"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        check_url_status("https://example.com")

        call_kwargs = mock_get.call_args[1]
        assert 'headers' in call_kwargs
        assert 'User-Agent' in call_kwargs['headers']


class TestExtractUrlsFromRequirements:
    """Test suite for extract_urls_from_requirements function"""

    @pytest.mark.parametrize("text,expected", [
        # HTTP/HTTPS URLs
        ("Install from https://example.com/package", ["https://example.com/package"]),
        ("See http://example.com for details", ["http://example.com"]),

        # Multiple URLs
        (
                "Visit https://example.com and http://test.org",
                ["https://example.com", "http://test.org"]
        ),

        # www URLs
        ("Download from www.example.com/file", ["www.example.com/file"]),

        # URLs with trailing punctuation
        ("Visit https://example.com.", ["https://example.com"]),
        ("See https://example.com!", ["https://example.com"]),
        ("Link: https://example.com,", ["https://example.com"]),

        # No URLs
        ("No URLs in this text", []),
        ("", []),

        # Mixed content
        (
                "Install package from https://pypi.org/project/name. See www.docs.com for help!",
                ["https://pypi.org/project/name", "www.docs.com"]
        ),
    ])
    def test_extract_urls_scenarios(self, text, expected):
        """Test various URL extraction scenarios"""
        result = extract_urls_from_requirements(text)
        assert sorted(result) == sorted(expected), f"Failed for text: {text}"

    def test_none_input(self):
        """Test with None input"""
        result = extract_urls_from_requirements(None)
        assert result == []

    def test_empty_input(self):
        """Test with empty input"""
        result = extract_urls_from_requirements("")
        assert result == []

    def test_url_with_query_parameters(self):
        """Test extraction of URLs with query parameters"""
        text = "Download from https://example.com/package?version=1.0&format=tar"
        result = extract_urls_from_requirements(text)
        assert "https://example.com/package?version=1.0&format=tar" in result

    def test_url_cleaning(self):
        """Test that trailing punctuation is removed"""
        test_cases = [
            ("https://example.com.", "https://example.com"),
            ("https://example.com,", "https://example.com"),
            ("https://example.com;", "https://example.com"),
            ("https://example.com!", "https://example.com"),
            ("https://example.com?", "https://example.com"),
            ("https://example.com)", "https://example.com"),
        ]

        for text, expected_url in test_cases:
            result = extract_urls_from_requirements(text)
            assert expected_url in result, f"Failed for: {text}"


class TestDetectInvalidSoftwareRequirementPitfall:
    """Test suite for detect_invalid_software_requirement_pitfall function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_pitfall", [
            # No requirements key
            ({}, "test_repo.json", False),

            # requirements not a list
            ({"requirements": "numpy"}, "test_repo.json", False),

            # Empty requirements list
            ({"requirements": []}, "test_repo.json", False),

            # Missing result key
            (
                    {
                        "requirements": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser"
                        }]
                    },
                    "test_repo.json",
                    False
            ),

            # Missing value in result
            (
                    {
                        "requirements": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {}
                        }]
                    },
                    "test_repo.json",
                    False
            ),

            # Non-metadata source
            (
                    {
                        "requirements": [{
                            "source": "README.md",
                            "technique": "header_analysis",
                            "result": {"value": "https://example.com"}
                        }]
                    },
                    "test_repo.json",
                    False
            ),
        ])
    @patch('metacheck.scripts.pitfalls.p008.check_url_status')
    def test_detect_invalid_requirement_basic_scenarios(self, mock_check, somef_data,
                                                        file_name, expected_has_pitfall):
        """Test basic scenarios without URL checking"""
        result = detect_invalid_software_requirement_pitfall(somef_data, file_name)
        assert result["has_pitfall"] == expected_has_pitfall

    @patch('metacheck.scripts.pitfalls.p008.check_url_status')
    def test_valid_url_requirement_accessible(self, mock_check):
        """Test requirement with accessible URL"""
        mock_check.return_value = {
            "is_accessible": True,
            "status_code": 200,
            "error": None
        }

        somef_data = {
            "requirements": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": "https://example.com"}
            }]
        }

        result = detect_invalid_software_requirement_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is False

    @patch('metacheck.scripts.pitfalls.p008.check_url_status')
    @patch('metacheck.scripts.pitfalls.p008.extract_metadata_source_filename')
    def test_valid_url_requirement_inaccessible(self, mock_extract, mock_check):
        """Test requirement with inaccessible URL"""
        mock_check.return_value = {
            "is_accessible": False,
            "status_code": 404,
            "error": None
        }
        mock_extract.return_value = "codemeta.json"

        somef_data = {
            "requirements": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": "https://broken.example.com"}
            }]
        }

        result = detect_invalid_software_requirement_pitfall(somef_data, "test.json")

        assert result["has_pitfall"] is True
        assert len(result["invalid_urls"]) == 1
        assert result["invalid_urls"][0]["url"] == "https://broken.example.com"
        assert result["invalid_urls"][0]["status_code"] == 404

    @patch('metacheck.scripts.pitfalls.p008.check_url_status')
    @patch('metacheck.scripts.pitfalls.p008.extract_metadata_source_filename')
    def test_requirement_text_with_embedded_urls(self, mock_extract, mock_check):
        """Test requirement text with embedded URLs"""
        mock_check.return_value = {
            "is_accessible": False,
            "status_code": 404,
            "error": None
        }
        mock_extract.return_value = "codemeta.json"

        somef_data = {
            "requirements": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": "Install from https://broken.example.com/package"}
            }]
        }

        result = detect_invalid_software_requirement_pitfall(somef_data, "test.json")

        assert result["has_pitfall"] is True
        assert len(result["invalid_urls"]) == 1
        assert result["invalid_urls"][0]["url"] == "https://broken.example.com/package"

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_invalid_software_requirement_pitfall(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "invalid_urls" in result
        assert "source" in result
        assert "metadata_source_file" in result
        assert "requirement_text" in result

    @pytest.mark.parametrize("metadata_file", [
        "codemeta.json", "description", "composer.json",
        "package.json", "pom.xml", "pyproject.toml",
        "requirements.txt", "setup.py"
    ])
    @patch('metacheck.scripts.pitfalls.p008.check_url_status')
    @patch('metacheck.scripts.pitfalls.p008.extract_metadata_source_filename')
    def test_all_metadata_sources(self, mock_extract, mock_check, metadata_file):
        """Test that all metadata file types are correctly processed"""
        mock_check.return_value = {
            "is_accessible": False,
            "status_code": 404,
            "error": None
        }
        mock_extract.return_value = metadata_file

        somef_data = {
            "requirements": [{
                "source": f"repository/{metadata_file}",
                "technique": "code_parser",
                "result": {"value": "https://broken.example.com"}
            }]
        }

        result = detect_invalid_software_requirement_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True
        assert result["metadata_source_file"] == metadata_file

    @patch('metacheck.scripts.pitfalls.p008.check_url_status')
    @patch('metacheck.scripts.pitfalls.p008.extract_metadata_source_filename')
    def test_multiple_urls_in_requirement(self, mock_extract, mock_check):
        """Test requirement with multiple URLs"""
        mock_check.side_effect = [
            {"is_accessible": True, "status_code": 200, "error": None},
            {"is_accessible": False, "status_code": 404, "error": None}
        ]
        mock_extract.return_value = "codemeta.json"

        somef_data = {
            "requirements": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": "Visit https://good.com and https://broken.com"}
            }]
        }

        result = detect_invalid_software_requirement_pitfall(somef_data, "test.json")

        assert result["has_pitfall"] is True
        assert len(result["invalid_urls"]) == 1
        assert result["invalid_urls"][0]["url"] == "https://broken.com"

    @patch('metacheck.scripts.pitfalls.p008.check_url_status')
    @patch('metacheck.scripts.pitfalls.p008.extract_metadata_source_filename')
    def test_requirement_as_list(self, mock_extract, mock_check):
        """Test requirement value as a list"""
        mock_check.return_value = {
            "is_accessible": False,
            "status_code": 404,
            "error": None
        }
        mock_extract.return_value = "codemeta.json"

        somef_data = {
            "requirements": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": ["package1", "from https://broken.com"]}
            }]
        }

        result = detect_invalid_software_requirement_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True

    @patch('metacheck.scripts.pitfalls.p008.check_url_status')
    @patch('metacheck.scripts.pitfalls.p008.extract_metadata_source_filename')
    def test_requirement_as_dict(self, mock_extract, mock_check):
        """Test requirement value as a dictionary"""
        mock_check.return_value = {
            "is_accessible": False,
            "status_code": 404,
            "error": None
        }
        mock_extract.return_value = "codemeta.json"

        somef_data = {
            "requirements": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {
                    "value": {
                        "name": "package",
                        "description": "Install from https://broken.com"
                    }
                }
            }]
        }

        result = detect_invalid_software_requirement_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True

    @patch('metacheck.scripts.pitfalls.p008.check_url_status')
    @patch('metacheck.scripts.pitfalls.p008.extract_metadata_source_filename')
    def test_stops_at_first_invalid_url(self, mock_extract, mock_check):
        """Test that function stops after finding first invalid URL"""
        mock_check.return_value = {
            "is_accessible": False,
            "status_code": 404,
            "error": None
        }
        mock_extract.side_effect = ["codemeta.json", "package.json"]

        somef_data = {
            "requirements": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "https://broken1.com"}
                },
                {
                    "source": "repository/package.json",
                    "technique": "code_parser",
                    "result": {"value": "https://broken2.com"}
                }
            ]
        }

        result = detect_invalid_software_requirement_pitfall(somef_data, "test.json")

        assert result["has_pitfall"] is True
        # Should only process first entry
        assert len(result["invalid_urls"]) == 1
        assert result["invalid_urls"][0]["url"] == "https://broken1.com"

    @patch('metacheck.scripts.pitfalls.p008.check_url_status')
    def test_wrong_technique_no_check(self, mock_check):
        """Test that wrong technique doesn't process"""
        somef_data = {
            "requirements": [{
                "source": "repository/codemeta.json",
                "technique": "github_api",
                "result": {"value": "https://example.com"}
            }]
        }

        result = detect_invalid_software_requirement_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is False
        # URL check should not be called
        mock_check.assert_not_called()