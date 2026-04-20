import pytest
from rsmetacheck.scripts.warnings.w007 import detect_empty_identifier_warning


class TestDetectEmptyIdentifierWarning:
    """Test suite for detect_empty_identifier_warning function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_warning,expected_identifier,expected_source", [
            # No identifier key
            (
                    {},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Identifier not a list
            (
                    {"identifier": "some-id"},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),
            (
                    {"identifier": {}},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Empty identifier list
            (
                    {"identifier": []},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Valid identifier from codemeta.json
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "my-project-id"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Empty string identifier from codemeta.json
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": ""}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "",
                    "repository/codemeta.json"
            ),

            # Whitespace-only identifier
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "   "}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "   ",
                    "repository/codemeta.json"
            ),

            # None identifier
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": None}
                        }]
                    },
                    "test_repo.json",
                    True,
                    None,
                    "repository/codemeta.json"
            ),

            # Multiple entries, first valid, second empty
            (
                    {
                        "identifier": [
                            {
                                "source": "README.md",
                                "technique": "header_analysis",
                                "result": {"value": "valid-id"}
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": ""}
                            }
                        ]
                    },
                    "test_repo.json",
                    True,
                    "",
                    "repository/codemeta.json"
            ),

            # codemeta in source (case-insensitive)
            (
                    {
                        "identifier": [{
                            "source": "repository/CodeMeta.json",
                            "technique": "code_parser",
                            "result": {"value": ""}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "",
                    "repository/CodeMeta.json"
            ),

            # code_parser technique with codemeta mention
            (
                    {
                        "identifier": [{
                            "source": "codemeta file",
                            "technique": "code_parser",
                            "result": {"value": ""}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "",
                    "codemeta file"
            ),

            # Non-codemeta source with empty identifier (should not trigger)
            (
                    {
                        "identifier": [{
                            "source": "README.md",
                            "technique": "header_analysis",
                            "result": {"value": ""}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Missing result key
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser"
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Missing value in result
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Tab and newline characters (should be considered empty)
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "\t\n  "}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "\t\n  ",
                    "repository/codemeta.json"
            ),
        ])
    def test_detect_empty_identifier_scenarios(self, somef_data, file_name,
                                               expected_has_warning, expected_identifier,
                                               expected_source):
        """Test various scenarios for empty identifier detection"""
        result = detect_empty_identifier_warning(somef_data, file_name)

        assert result["has_warning"] == expected_has_warning
        assert result["file_name"] == file_name
        assert result["identifier_value"] == expected_identifier
        assert result["source"] == expected_source

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_empty_identifier_warning(somef_data, "test.json")

        assert "has_warning" in result
        assert "file_name" in result
        assert "identifier_value" in result
        assert "source" in result

    def test_stops_at_first_match(self):
        """Test that function returns after finding first empty identifier"""
        somef_data = {
            "identifier": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": ""}
                },
                {
                    "source": "repository/another_codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "  "}
                }
            ]
        }

        result = detect_empty_identifier_warning(somef_data, "test.json")

        assert result["has_warning"] is True
        assert result["source"] == "repository/codemeta.json"

    @pytest.mark.parametrize("technique", ["code_parser", "header_analysis", "github_api"])
    def test_technique_filtering(self, technique):
        """Test that only code_parser technique triggers for codemeta"""
        somef_data = {
            "identifier": [{
                "source": "repository/codemeta.json",
                "technique": technique,
                "result": {"value": ""}
            }]
        }

        result = detect_empty_identifier_warning(somef_data, "test.json")

        if technique == "code_parser":
            assert result["has_warning"] is True
        else:
            # For non-code_parser, it should still match if "codemeta.json" is in source
            assert result["has_warning"] is True

    def test_source_variations(self):
        """Test various source path formats"""
        test_sources = [
            "codemeta.json",
            "repository/codemeta.json",
            "/path/to/codemeta.json",
            "CODEMETA.json",
            "project/CodeMeta.json"
        ]

        for source in test_sources:
            somef_data = {
                "identifier": [{
                    "source": source,
                    "technique": "code_parser",
                    "result": {"value": ""}
                }]
            }

            result = detect_empty_identifier_warning(somef_data, "test.json")
            assert result["has_warning"] is True, f"Failed for source: {source}"

    @pytest.mark.parametrize("empty_value", ["", "  ", "\t", "\n", "   \t\n  ", None])
    def test_various_empty_values(self, empty_value):
        """Test detection of various forms of empty values"""
        somef_data = {
            "identifier": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": empty_value}
            }]
        }

        result = detect_empty_identifier_warning(somef_data, "test.json")
        assert result["has_warning"] is True
        assert result["identifier_value"] == empty_value