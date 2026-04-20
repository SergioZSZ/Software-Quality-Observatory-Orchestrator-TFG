import pytest
from rsmetacheck.scripts.warnings.w006 import (
    is_valid_identifier,
    has_doi_in_other_sources,  # Added this import
    detect_identifier_name_warning
)


class TestIsValidIdentifier:
    """Test suite for is_valid_identifier function"""

    @pytest.mark.parametrize("identifier,expected", [
        # Empty or None
        ("", False),
        (None, False),

        # Valid DOI patterns
        ("doi:10.1234/example", True),
        ("DOI:10.5678/test", True),
        ("10.1000/journal.12345", True),
        ("10.5281/zenodo.67890", True),

        # Valid URLs
        ("https://example.com", True),
        ("http://example.org/resource", True),
        ("https://doi.org/10.1234/example", True),

        # Invalid identifiers (names, not IDs)
        ("Project Name", False),
        ("My Software", False),
        ("John Doe", False),
        ("Software Title", False),

        # Edge cases
        ("doi:", False),  # doi: without actual DOI
        ("10.", False),  # Incomplete DOI
        ("ftp://example.com", False),  # Not http/https

        # Case insensitive
        ("DOI:10.1234/test", True),
        ("HTTPS://EXAMPLE.COM", True),
    ])
    def test_identifier_validation(self, identifier, expected):
        """Test identifier validation scenarios"""
        result = is_valid_identifier(identifier)
        assert result == expected


class TestHasDoiInOtherSources:
    """Test suite for has_doi_in_other_sources function"""

    def test_doi_in_non_codemeta_source(self):
        """Test detection of DOI in non-codemeta sources"""
        identifier_entries = [
            {
                "source": "README.md",
                "result": {"value": "10.1234/example"}
            }
        ]

        result = has_doi_in_other_sources(identifier_entries)
        assert result == True

    def test_no_doi_in_other_sources(self):
        """Test when no DOI exists in other sources"""
        identifier_entries = [
            {
                "source": "README.md",
                "result": {"value": "Project Name"}
            }
        ]

        result = has_doi_in_other_sources(identifier_entries)
        assert result == False

    def test_doi_only_in_codemeta(self):
        """Test when DOI only exists in codemeta.json"""
        identifier_entries = [
            {
                "source": "repository/codemeta.json",
                "result": {"value": "10.1234/example"}
            }
        ]

        result = has_doi_in_other_sources(identifier_entries)
        assert result == False

    def test_doi_keyword_detection(self):
        """Test detection using 'doi' keyword"""
        identifier_entries = [
            {
                "source": "README.md",
                "result": {"value": "doi:10.1234/example"}
            }
        ]

        result = has_doi_in_other_sources(identifier_entries)
        assert result == True

    def test_doi_pattern_detection(self):
        """Test detection using DOI pattern"""
        identifier_entries = [
            {
                "source": "CITATION.cff",
                "result": {"value": "10.5281/zenodo.12345"}
            }
        ]

        result = has_doi_in_other_sources(identifier_entries)
        assert result == True


class TestDetectIdentifierNameWarning:
    """Test suite for detect_identifier_name_warning function"""

    @pytest.mark.parametrize("somef_data,file_name,expected_has_warning", [
        # No identifier key
        (
                {},
                "test_repo.json",
                False
        ),

        # identifier not a list
        (
                {"identifier": "Project Name"},
                "test_repo.json",
                False
        ),

        # Empty identifier list
        (
                {"identifier": []},
                "test_repo.json",
                False
        ),

        # Valid identifier in codemeta (no warning)
        (
                {
                    "identifier": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {"value": "10.1234/example"}
                    }]
                },
                "test_repo.json",
                False
        ),

        # Name in codemeta, but no valid identifier elsewhere (no warning)
        (
                {
                    "identifier": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {"value": "Project Name"}
                    }]
                },
                "test_repo.json",
                False
        ),

        # Name in codemeta, valid DOI elsewhere (warning)
        (
                {
                    "identifier": [
                        {
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "Project Name"}
                        },
                        {
                            "source": "README.md",
                            "result": {"value": "10.1234/example"}
                        }
                    ]
                },
                "test_repo.json",
                True
        ),

        # Name in codemeta, valid URL elsewhere (warning)
        (
                {
                    "identifier": [
                        {
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "My Software"}
                        },
                        {
                            "source": "CITATION.cff",
                            "result": {"value": "https://doi.org/10.1234/test"}
                        }
                    ]
                },
                "test_repo.json",
                True
        ),

        # Name in codemeta with lowercase source match (warning)
        (
                {
                    "identifier": [
                        {
                            "source": "repository/CODEMETA.json",
                            "technique": "code_parser",
                            "result": {"value": "Project"}
                        },
                        {
                            "source": "README.md",
                            "result": {"value": "doi:10.1234/test"}
                        }
                    ]
                },
                "test_repo.json",
                True
        ),
    ])
    def test_detect_warning_scenarios(self, somef_data, file_name, expected_has_warning):
        """Test various identifier name warning scenarios"""
        result = detect_identifier_name_warning(somef_data, file_name)

        assert result["has_warning"] == expected_has_warning
        assert result["file_name"] == file_name

        if expected_has_warning:
            assert result["codemeta_identifier"] is not None
            assert result["codemeta_source"] is not None
            assert result["has_valid_identifier_elsewhere"] == True

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_identifier_name_warning(somef_data, "test.json")

        assert "has_warning" in result
        assert "file_name" in result
        assert "codemeta_identifier" in result
        assert "codemeta_source" in result
        assert "has_valid_identifier_elsewhere" in result
        assert "other_identifiers" in result

    def test_codemeta_identifier_captured(self):
        """Test that codemeta identifier is properly captured"""
        somef_data = {
            "identifier": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "Software Title"}
                },
                {
                    "source": "README.md",
                    "result": {"value": "10.1234/example"}
                }
            ]
        }

        result = detect_identifier_name_warning(somef_data, "test.json")
        assert result["codemeta_identifier"] == "Software Title"
        assert result["codemeta_source"] == "repository/codemeta.json"

    def test_other_identifiers_collected(self):
        """Test that other identifiers are collected"""
        somef_data = {
            "identifier": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "Project Name"}
                },
                {
                    "source": "README.md",
                    "technique": "header_analysis",
                    "result": {"value": "10.1234/example"}
                },
                {
                    "source": "CITATION.cff",
                    "technique": "code_parser",
                    "result": {"value": "https://example.com"}
                }
            ]
        }

        result = detect_identifier_name_warning(somef_data, "test.json")
        assert result["has_warning"] == True
        assert len(result["other_identifiers"]) == 2

    def test_multiple_codemeta_identifiers_uses_first(self):
        """Test that first codemeta identifier is used"""
        somef_data = {
            "identifier": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "First Name"}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "Second Name"}
                },
                {
                    "source": "README.md",
                    "result": {"value": "10.1234/example"}
                }
            ]
        }

        result = detect_identifier_name_warning(somef_data, "test.json")
        assert result["codemeta_identifier"] == "First Name"

    def test_technique_code_parser_matching(self):
        """Test matching using technique=code_parser"""
        somef_data = {
            "identifier": [
                {
                    "source": "some/path/codemeta.file",
                    "technique": "code_parser",
                    "result": {"value": "Project"}
                },
                {
                    "source": "README.md",
                    "result": {"value": "10.1234/example"}
                }
            ]
        }

        result = detect_identifier_name_warning(somef_data, "test.json")
        assert result["has_warning"] == True

    def test_doi_pattern_in_other_sources(self):
        """Test that DOI pattern is detected in other sources"""
        somef_data = {
            "identifier": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "My Project"}
                },
                {
                    "source": "README.md",
                    "result": {"value": "Check our DOI: 10.5281/zenodo.12345"}
                }
            ]
        }

        result = detect_identifier_name_warning(somef_data, "test.json")
        assert result["has_warning"] == True

    @pytest.mark.parametrize("valid_id", [
        "10.1234/example",
        "doi:10.5678/test",
        "https://doi.org/10.1234/test",
        "http://example.org/resource"
    ])
    def test_various_valid_identifier_formats(self, valid_id):
        """Test that various valid identifier formats trigger warning"""
        somef_data = {
            "identifier": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "Project Name"}
                },
                {
                    "source": "README.md",
                    "result": {"value": valid_id}
                }
            ]
        }

        result = detect_identifier_name_warning(somef_data, "test.json")
        assert result["has_warning"] == True

    def test_no_warning_when_all_names(self):
        """Test no warning when all identifiers are names"""
        somef_data = {
            "identifier": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "Project Name"}
                },
                {
                    "source": "README.md",
                    "result": {"value": "Another Name"}
                }
            ]
        }

        result = detect_identifier_name_warning(somef_data, "test.json")
        assert result["has_warning"] == False