import pytest
from rsmetacheck.scripts.warnings.w009 import is_url, detect_development_status_url_pitfall


class TestIsUrl:
    """Test suite for is_url helper function"""

    @pytest.mark.parametrize("value,expected", [
        # Valid URLs with http/https
        ("http://example.com", True),
        ("https://example.com", True),
        ("HTTP://EXAMPLE.COM", True),
        ("https://www.example.org", True),

        # URLs starting with www
        ("www.example.com", True),
        ("www.github.com/user/repo", True),
        ("WWW.SITE.NET", True),

        # URLs with TLDs
        ("example.org", True),
        ("site.com", True),
        ("domain.net", True),
        ("mysite.org/path", True),
        ("test.com?query=value", True),

        # Mixed case
        ("HTTPS://EXAMPLE.ORG", True),
        ("Example.COM", True),

        # Non-URLs
        ("active", False),
        ("development", False),
        ("WIP", False),
        ("stable", False),
        ("beta", False),
        ("alpha", False),
        ("inactive", False),

        # Empty or invalid
        ("", False),
        ("   ", False),
        (None, False),

        # Edge cases with periods but not URLs
        ("file.txt", False),
        ("document.pdf", False),
        ("script.py", False),

        # Numbers and special chars
        ("12345", False),
        ("status-active", False),
        ("under_development", False),

        # Partial matches
        ("this is example.com in text", True),
        ("visit www.site.com for info", True),
        ("see https://example.org", True),
    ])
    def test_is_url_scenarios(self, value, expected):
        """Test various URL detection scenarios"""
        result = is_url(value)
        assert result == expected, f"Failed for value: {value}"

    def test_is_url_with_non_string(self):
        """Test is_url with non-string inputs"""
        assert is_url(123) is False
        assert is_url([]) is False
        assert is_url({}) is False
        assert is_url(None) is False

    def test_is_url_whitespace_handling(self):
        """Test that whitespace is properly handled"""
        assert is_url("  https://example.com  ") is True
        assert is_url("\twww.site.com\n") is True
        assert is_url("  example.org  ") is True


class TestDetectDevelopmentStatusUrlPitfall:
    """Test suite for detect_development_status_url_pitfall function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_warning,expected_status,expected_is_url", [
            # No development_status key
            (
                    {},
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # development_status not a list
            (
                    {"development_status": "active"},
                    "test_repo.json",
                    False,
                    None,
                    False
            ),
            (
                    {"development_status": {}},
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Empty development_status list
            (
                    {"development_status": []},
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Valid status string from codemeta.json
            (
                    {
                        "development_status": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "active"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # URL as development status from codemeta.json
            (
                    {
                        "development_status": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "https://www.repostatus.org/#active"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "https://www.repostatus.org/#active",
                    True
            ),

            # URL with www prefix
            (
                    {
                        "development_status": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "www.example.org/status"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "www.example.org/status",
                    True
            ),

            # URL with .com TLD
            (
                    {
                        "development_status": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "example.com/status"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "example.com/status",
                    True
            ),

            # Non-codemeta source with URL (should not trigger)
            (
                    {
                        "development_status": [{
                            "source": "README.md",
                            "technique": "header_analysis",
                            "result": {"value": "https://www.repostatus.org/#active"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # code_parser technique but not codemeta source (should not trigger)
            (
                    {
                        "development_status": [{
                            "source": "setup.py",
                            "technique": "code_parser",
                            "result": {"value": "https://www.repostatus.org/#active"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Case insensitive codemeta matching
            (
                    {
                        "development_status": [{
                            "source": "repository/CODEMETA.JSON",
                            "technique": "code_parser",
                            "result": {"value": "http://example.org"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "http://example.org",
                    True
            ),

            # code_parser with codemeta in source (lowercase check)
            (
                    {
                        "development_status": [{
                            "source": "CodeMeta file",
                            "technique": "code_parser",
                            "result": {"value": "https://example.com"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "https://example.com",
                    True
            ),

            # Multiple entries, first non-codemeta, second codemeta with URL
            (
                    {
                        "development_status": [
                            {
                                "source": "README.md",
                                "technique": "header_analysis",
                                "result": {"value": "active"}
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "www.status.org"}
                            }
                        ]
                    },
                    "test_repo.json",
                    True,
                    "www.status.org",
                    True
            ),

            # Missing result key
            (
                    {
                        "development_status": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser"
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Missing value in result
            (
                    {
                        "development_status": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Empty string value
            (
                    {
                        "development_status": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": ""}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # URL with .net TLD
            (
                    {
                        "development_status": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "status.net/active"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "status.net/active",
                    True
            ),

            # Valid status strings that are not URLs
            (
                    {
                        "development_status": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "wip"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),
        ])
    def test_detect_development_status_url_scenarios(self, somef_data, file_name,
                                                     expected_has_warning, expected_status,
                                                     expected_is_url):
        """Test various scenarios for development status URL detection"""
        result = detect_development_status_url_pitfall(somef_data, file_name)

        assert result["has_warning"] == expected_has_warning
        assert result["file_name"] == file_name
        assert result["development_status"] == expected_status
        assert result["is_url"] == expected_is_url

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_development_status_url_pitfall(somef_data, "test.json")

        assert "has_warning" in result
        assert "file_name" in result
        assert "development_status" in result
        assert "source" in result
        assert "is_url" in result

    def test_stops_at_first_match(self):
        """Test that function returns after finding first URL"""
        somef_data = {
            "development_status": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "https://example.com"}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "www.another.org"}
                }
            ]
        }

        result = detect_development_status_url_pitfall(somef_data, "test.json")

        assert result["has_warning"] is True
        assert result["development_status"] == "https://example.com"

    @pytest.mark.parametrize("url_value", [
        "https://www.repostatus.org/#active",
        "http://repostatus.org/#wip",
        "www.repostatus.org/#inactive",
        "repostatus.org/status",
        "status.com",
        "example.net/dev",
    ])
    def test_various_url_formats(self, url_value):
        """Test detection of various URL formats"""
        somef_data = {
            "development_status": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": url_value}
            }]
        }

        result = detect_development_status_url_pitfall(somef_data, "test.json")
        assert result["has_warning"] is True
        assert result["development_status"] == url_value

    @pytest.mark.parametrize("valid_status", [
        "active",
        "inactive",
        "wip",
        "concept",
        "suspended",
        "unsupported",
        "moved",
        "alpha",
        "beta",
        "stable",
    ])
    def test_valid_status_strings(self, valid_status):
        """Test that valid status strings don't trigger false positives"""
        somef_data = {
            "development_status": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": valid_status}
            }]
        }

        result = detect_development_status_url_pitfall(somef_data, "test.json")
        assert result["has_warning"] is False

    def test_source_variations(self):
        """Test various source path formats for codemeta.json"""
        test_sources = [
            ("codemeta.json", True),
            ("repository/codemeta.json", True),
            ("/path/to/codemeta.json", True),
            ("CODEMETA.json", True),
            ("CodeMeta.json", True),
            ("package.json", False),
            ("setup.py", False),
            ("README.md", False),
        ]

        for source, should_trigger in test_sources:
            somef_data = {
                "development_status": [{
                    "source": source,
                    "technique": "code_parser",
                    "result": {"value": "https://example.com"}
                }]
            }

            result = detect_development_status_url_pitfall(somef_data, "test.json")
            assert result["has_warning"] == should_trigger, f"Failed for source: {source}"

    def test_non_string_values(self):
        """Test that non-string values don't cause errors"""
        test_values = [
            123,
            None,
            [],
            {},
            True,
        ]

        for value in test_values:
            somef_data = {
                "development_status": [{
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": value}
                }]
            }

            result = detect_development_status_url_pitfall(somef_data, "test.json")
            assert result["has_warning"] is False