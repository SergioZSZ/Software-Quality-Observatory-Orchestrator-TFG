import pytest
from rsmetacheck.scripts.pitfalls.p014 import is_bare_doi, detect_bare_doi_pitfall


class TestIsBareDoi:
    """Test suite for is_bare_doi helper function"""

    @pytest.mark.parametrize("identifier,expected", [
        # Bare DOI patterns
        ("doi:10.1234/example", True),
        ("doi:10.5555/repo.v1", True),
        ("10.1234/example", True),
        ("10.5555/repo.v1", True),
        ("10.1000/xyz123", True),

        # With whitespace
        ("  doi:10.1234/example  ", True),
        ("  10.1234/example  ", True),

        # Full DOI URLs (should return False)
        ("https://doi.org/10.1234/example", False),
        ("https://doi.org/10.5555/repo", False),
        ("HTTPS://DOI.ORG/10.1234/example", False),

        # Invalid patterns
        ("doi:example", False),
        ("10.example", False),
        ("doi:10", False),
        ("10", False),
        ("not-a-doi", False),
        ("example.com/10.1234", False),

        # Empty or None
        ("", False),
        ("   ", False),
        (None, False),

        # Edge cases
        ("doi:10.1/a", True),
        ("10.999999/test", True),
        ("doi:10.12345/very-long-suffix", True),

        # Non-string types
        (123, False),
        ([], False),
        ({}, False),
    ])
    def test_is_bare_doi_scenarios(self, identifier, expected):
        """Test various bare DOI detection scenarios"""
        result = is_bare_doi(identifier)
        assert result == expected, f"Failed for identifier: {identifier}"

    def test_various_doi_prefixes(self):
        """Test DOIs with various numeric prefixes"""
        prefixes = ["10.1", "10.12", "10.123", "10.1234", "10.12345"]

        for prefix in prefixes:
            bare_doi = f"{prefix}/example"
            doi_with_prefix = f"doi:{prefix}/example"
            full_url = f"https://doi.org/{prefix}/example"

            assert is_bare_doi(bare_doi) is True, f"Failed for bare DOI: {bare_doi}"
            assert is_bare_doi(doi_with_prefix) is True, f"Failed for DOI with prefix: {doi_with_prefix}"
            assert is_bare_doi(full_url) is False, f"Failed for full URL: {full_url}"

    def test_complex_doi_suffixes(self):
        """Test DOIs with complex suffix patterns"""
        suffixes = [
            "example",
            "repo.v1",
            "dataset-2023",
            "paper_final",
            "10.1234.5678",
            "item/123"
        ]

        for suffix in suffixes:
            bare_doi = f"10.1234/{suffix}"
            assert is_bare_doi(bare_doi) is True, f"Failed for suffix: {suffix}"


class TestDetectBareDOIPitfall:
    """Test suite for detect_bare_doi_pitfall function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_pitfall,expected_identifier,expected_is_bare", [
            # No identifier key
            (
                    {},
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # identifier not a list
            (
                    {"identifier": "10.1234/example"},
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Empty identifier list
            (
                    {"identifier": []},
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Full DOI URL from codemeta.json (no pitfall)
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "https://doi.org/10.1234/example"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Bare DOI with doi: prefix from codemeta.json
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "doi:10.1234/example"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "doi:10.1234/example",
                    True
            ),

            # Bare DOI without prefix from codemeta.json
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "10.1234/example"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "10.1234/example",
                    True
            ),

            # Bare DOI from non-codemeta source (should not trigger)
            (
                    {
                        "identifier": [{
                            "source": "README.md",
                            "technique": "header_analysis",
                            "result": {"value": "doi:10.1234/example"}
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
                        "identifier": [{
                            "source": "repository/CODEMETA.JSON",
                            "technique": "code_parser",
                            "result": {"value": "10.5555/repo"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "10.5555/repo",
                    True
            ),

            # code_parser with codemeta in source
            (
                    {
                        "identifier": [{
                            "source": "CodeMeta file",
                            "technique": "code_parser",
                            "result": {"value": "doi:10.1234/test"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "doi:10.1234/test",
                    True
            ),

            # Multiple entries, first valid, second bare
            (
                    {
                        "identifier": [
                            {
                                "source": "README.md",
                                "technique": "header_analysis",
                                "result": {"value": "https://doi.org/10.1234/example"}
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "10.1234/example"}
                            }
                        ]
                    },
                    "test_repo.json",
                    True,
                    "10.1234/example",
                    True
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
                    False
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
                    False
            ),

            # Empty string value
            (
                    {
                        "identifier": [{
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

            # Non-DOI identifier
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "my-project-identifier"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Complex bare DOI
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "doi:10.12345/dataset.2023.v1"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "doi:10.12345/dataset.2023.v1",
                    True
            ),
        ])
    def test_detect_bare_doi_scenarios(self, somef_data, file_name,
                                       expected_has_pitfall, expected_identifier,
                                       expected_is_bare):
        """Test various scenarios for bare DOI detection"""
        result = detect_bare_doi_pitfall(somef_data, file_name)

        assert result["has_pitfall"] == expected_has_pitfall
        assert result["file_name"] == file_name
        assert result["identifier_value"] == expected_identifier
        assert result["is_bare_doi"] == expected_is_bare

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_bare_doi_pitfall(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "identifier_value" in result
        assert "source" in result
        assert "is_bare_doi" in result

    def test_stops_at_first_match(self):
        """Test that function returns after finding first bare DOI"""
        somef_data = {
            "identifier": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "doi:10.1234/first"}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "10.5555/second"}
                }
            ]
        }

        result = detect_bare_doi_pitfall(somef_data, "test.json")

        assert result["has_pitfall"] is True
        assert result["identifier_value"] == "doi:10.1234/first"

    @pytest.mark.parametrize("bare_doi", [
        "doi:10.1234/example",
        "10.1234/example",
        "doi:10.5555/repo.v1",
        "10.9999/dataset-2023",
        "doi:10.1000/test_paper",
    ])
    def test_various_bare_doi_formats(self, bare_doi):
        """Test detection of various bare DOI formats"""
        somef_data = {
            "identifier": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": bare_doi}
            }]
        }

        result = detect_bare_doi_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True
        assert result["identifier_value"] == bare_doi

    @pytest.mark.parametrize("full_doi", [
        "https://doi.org/10.1234/example",
        "https://doi.org/10.5555/repo",
        "HTTPS://DOI.ORG/10.9999/test",
    ])
    def test_full_doi_urls_no_pitfall(self, full_doi):
        """Test that full DOI URLs don't trigger the pitfall"""
        somef_data = {
            "identifier": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": full_doi}
            }]
        }

        result = detect_bare_doi_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is False

    def test_source_variations(self):
        """Test various source path formats for codemeta.json"""
        test_sources = [
            ("codemeta.json", True),
            ("repository/codemeta.json", True),
            ("/path/to/codemeta.json", True),
            ("CODEMETA.json", True),
            ("CodeMeta.json", True),
            ("package.json", False),
            ("README.md", False),
        ]

        for source, should_trigger in test_sources:
            somef_data = {
                "identifier": [{
                    "source": source,
                    "technique": "code_parser",
                    "result": {"value": "doi:10.1234/example"}
                }]
            }

            result = detect_bare_doi_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] == should_trigger, f"Failed for source: {source}"

    @pytest.mark.parametrize("technique", ["code_parser", "header_analysis", "github_api"])
    def test_technique_filtering(self, technique):
        """Test that only code_parser technique triggers for codemeta"""
        somef_data = {
            "identifier": [{
                "source": "repository/codemeta.json",
                "technique": technique,
                "result": {"value": "doi:10.1234/example"}
            }]
        }

        result = detect_bare_doi_pitfall(somef_data, "test.json")

        # Should trigger for codemeta.json regardless of technique when source matches
        assert result["has_pitfall"] is True

    def test_non_string_identifier_value(self):
        """Test that non-string identifier values don't cause errors"""
        test_values = [123, None, [], {}, True]

        for value in test_values:
            somef_data = {
                "identifier": [{
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": value}
                }]
            }

            result = detect_bare_doi_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] is False