import pytest
from unittest.mock import patch
from rsmetacheck.scripts.warnings.w008 import detect_author_name_list_warning


class TestDetectAuthorNameListWarning:
    """Test suite for detect_author_name_list_warning function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_warning,expected_author,expected_source_file", [
            # No authors key
            (
                    {},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Authors not a list
            (
                    {"authors": "John Doe"},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),
            (
                    {"authors": {}},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Empty authors list
            (
                    {"authors": []},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Valid author string without list pattern
            (
                    {
                        "authors": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "John Doe"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Author with list pattern containing comma
            (
                    {
                        "authors": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "['William', 'Michael'] Landau"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "['William', 'Michael'] Landau",
                    "codemeta.json"
            ),

            # List pattern with single item (no comma, should not trigger)
            (
                    {
                        "authors": [{
                            "source": "repository/package.json",
                            "technique": "code_parser",
                            "result": {"value": "['John'] Doe"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # List pattern with multiple items and commas
            (
                    {
                        "authors": [{
                            "source": "repository/setup.py",
                            "technique": "code_parser",
                            "result": {"value": "['Alice', 'Bob', 'Charlie'] Team"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "['Alice', 'Bob', 'Charlie'] Team",
                    "setup.py"
            ),

            # Non-string author value (should not trigger)
            (
                    {
                        "authors": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": {"name": "John Doe"}}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Author value as list (should not trigger since we check for string)
            (
                    {
                        "authors": [{
                            "source": "repository/package.json",
                            "technique": "code_parser",
                            "result": {"value": ["John Doe", "Jane Smith"]}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Non-metadata source (should not trigger)
            (
                    {
                        "authors": [{
                            "source": "README.md",
                            "technique": "header_analysis",
                            "result": {"value": "['William', 'Michael'] Landau"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Wrong technique (should not trigger)
            (
                    {
                        "authors": [{
                            "source": "repository/codemeta.json",
                            "technique": "github_api",
                            "result": {"value": "['William', 'Michael'] Landau"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Multiple list patterns in string
            (
                    {
                        "authors": [{
                            "source": "repository/pyproject.toml",
                            "technique": "code_parser",
                            "result": {"value": "['First', 'Second'] ['Third', 'Fourth'] Name"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "['First', 'Second'] ['Third', 'Fourth'] Name",
                    "pyproject.toml"
            ),

            # Missing result key
            (
                    {
                        "authors": [{
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
                        "authors": [{
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

            # Empty brackets (no comma, should not trigger)
            (
                    {
                        "authors": [{
                            "source": "repository/composer.json",
                            "technique": "code_parser",
                            "result": {"value": "[] Author Name"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # List with spaces around comma
            (
                    {
                        "authors": [{
                            "source": "repository/pom.xml",
                            "technique": "code_parser",
                            "result": {"value": "['First' , 'Second'] LastName"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "['First' , 'Second'] LastName",
                    "pom.xml"
            ),
        ])
    def test_detect_author_name_list_scenarios(self, somef_data, file_name,
                                               expected_has_warning, expected_author,
                                               expected_source_file):
        """Test various scenarios for author name list detection"""
        with patch('metacheck.scripts.warnings.w008.extract_metadata_source_filename',
                   return_value=expected_source_file):
            result = detect_author_name_list_warning(somef_data, file_name)

            assert result["has_warning"] == expected_has_warning
            assert result["file_name"] == file_name
            assert result["author_value"] == expected_author

            if expected_has_warning:
                assert result["metadata_source_file"] == expected_source_file

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_author_name_list_warning(somef_data, "test.json")

        assert "has_warning" in result
        assert "file_name" in result
        assert "author_value" in result
        assert "source" in result
        assert "metadata_source_file" in result

    @pytest.mark.parametrize("metadata_file", [
        "codemeta.json", "DESCRIPTION", "composer.json",
        "package.json", "pom.xml", "pyproject.toml",
        "requirements.txt", "setup.py"
    ])
    def test_all_metadata_sources(self, metadata_file):
        """Test that all metadata file types are correctly processed"""
        somef_data = {
            "authors": [{
                "source": f"repository/{metadata_file}",
                "technique": "code_parser",
                "result": {"value": "['First', 'Second'] LastName"}
            }]
        }

        with patch('metacheck.scripts.warnings.w008.extract_metadata_source_filename',
                   return_value=metadata_file):
            result = detect_author_name_list_warning(somef_data, "test.json")
            assert result["has_warning"] is True
            assert result["metadata_source_file"] == metadata_file

    @pytest.mark.parametrize("list_pattern", [
        "['A', 'B']",
        "['First', 'Middle', 'Last']",
        "['One','Two','Three']",  # No spaces after commas
        "['X' , 'Y' , 'Z']",  # Spaces around commas
        "[\"A\", \"B\"]",  # Double quotes
    ])
    def test_various_list_patterns(self, list_pattern):
        """Test detection of various list pattern formats"""
        somef_data = {
            "authors": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": f"{list_pattern} Surname"}
            }]
        }

        with patch('metacheck.scripts.warnings.w008.extract_metadata_source_filename',
                   return_value="codemeta.json"):
            result = detect_author_name_list_warning(somef_data, "test.json")
            assert result["has_warning"] is True, f"Failed to detect pattern: {list_pattern}"

    def test_no_comma_in_brackets(self):
        """Test that brackets without commas don't trigger warning"""
        test_cases = [
            "[SingleItem] Name",
            "[] Name",
            "[NoCommaHere] Name",
            "['Single'] Name"
        ]

        for test_value in test_cases:
            somef_data = {
                "authors": [{
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": test_value}
                }]
            }

            result = detect_author_name_list_warning(somef_data, "test.json")
            assert result["has_warning"] is False, f"False positive for: {test_value}"

    def test_multiple_authors_first_has_warning(self):
        """Test processing multiple author entries where first has warning"""
        somef_data = {
            "authors": [
                {
                    "source": "README.md",
                    "technique": "header_analysis",
                    "result": {"value": "Normal Author"}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "['A', 'B'] Problem"}
                }
            ]
        }

        with patch('metacheck.scripts.warnings.w008.extract_metadata_source_filename',
                   return_value="codemeta.json"):
            result = detect_author_name_list_warning(somef_data, "test.json")
            assert result["has_warning"] is True

    def test_source_field_variations(self):
        """Test various source field formats"""
        test_sources = [
            "codemeta.json",
            "repository/codemeta.json",
            "/full/path/to/package.json",
            "setup.py",
            "DESCRIPTION"
        ]

        for source in test_sources:
            expected_file = source.split('/')[-1]
            somef_data = {
                "authors": [{
                    "source": source,
                    "technique": "code_parser",
                    "result": {"value": "['A', 'B'] Name"}
                }]
            }

            with patch('metacheck.scripts.warnings.w008.extract_metadata_source_filename',
                       return_value=expected_file):
                result = detect_author_name_list_warning(somef_data, "test.json")

                # Check if it's a metadata source
                is_metadata = any(meta in source for meta in [
                    "codemeta.json", "DESCRIPTION", "composer.json",
                    "package.json", "pom.xml", "pyproject.toml",
                    "requirements.txt", "setup.py"
                ])

                assert result["has_warning"] == is_metadata