import pytest
from unittest.mock import patch
from rsmetacheck.scripts.pitfalls.p003 import (
    has_multiple_authors_in_single_field,
    detect_multiple_authors_single_field_pitfall
)


class TestHasMultipleAuthorsInSingleField:
    """Test suite for has_multiple_authors_in_single_field function"""

    @pytest.mark.parametrize("author_value,expected", [
        # Empty or None values
        ("", False),
        (None, False),

        # Not a string
        (123, False),
        ([], False),
        ({}, False),

        # Single author
        ("John Smith", False),
        ("Jane Doe", False),
        ("Dr. Robert Johnson", False),

        # Multiple authors with 'and'
        ("John Smith and Jane Doe", True),
        ("Alice and Bob and Charlie", True),
        ("John AND Jane", True),

        # Multiple authors with '&'
        ("John Smith & Jane Doe", True),
        ("Alice & Bob", True),

        # Multiple authors with comma
        ("John Smith, Jane Doe", True),
        ("Alice, Bob, Charlie", True),

        # Comma with Jr. (should not trigger)
        ("John Smith, Jr.", False),
        ("Robert Johnson, Jr.", False),

        # Multiple authors with semicolon
        ("John Smith; Jane Doe", True),
        ("Alice; Bob; Charlie", True),

        # Multiple authors on separate lines
        ("John Smith\nJane Doe", True),
        ("Alice\nBob\nCharlie", True),

        # Mixed patterns
        ("John Smith, Jane Doe and Alice Brown", True),
        ("John & Jane, Alice", True),

        # Whitespace handling
        ("  John Smith and Jane Doe  ", True),
        ("John,Jane", True),

        # Edge cases
        ("Smith, John", True),  # Could be multiple or last, first
        ("Dr. Smith and Dr. Jones", True),
    ])
    def test_multiple_authors_detection(self, author_value, expected):
        """Test various scenarios for detecting multiple authors"""
        result = has_multiple_authors_in_single_field(author_value)
        assert result == expected


class TestDetectMultipleAuthorsSingleFieldPitfall:
    """Test suite for detect_multiple_authors_single_field_pitfall function"""

    @pytest.mark.parametrize("somef_data,file_name,expected_has_pitfall,expected_author_value", [
        # No authors key
        (
                {},
                "test_repo.json",
                False,
                None
        ),

        # Authors not a list
        (
                {"authors": "John Doe"},
                "test_repo.json",
                False,
                None
        ),

        # Empty authors list
        (
                {"authors": []},
                "test_repo.json",
                False,
                None
        ),

        # Single author in metadata
        (
                {
                    "authors": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {"value": "John Smith"}
                    }]
                },
                "test_repo.json",
                False,
                None
        ),

        # Multiple authors with 'and'
        (
                {
                    "authors": [{
                        "source": "repository/package.json",
                        "technique": "code_parser",
                        "result": {"value": "John Smith and Jane Doe"}
                    }]
                },
                "test_repo.json",
                True,
                "John Smith and Jane Doe"
        ),

        # Multiple authors with comma
        (
                {
                    "authors": [{
                        "source": "repository/setup.py",
                        "technique": "code_parser",
                        "result": {"value": "Alice, Bob, Charlie"}
                    }]
                },
                "test_repo.json",
                True,
                "Alice, Bob, Charlie"
        ),

        # Structured author data with multiple authors
        (
                {
                    "authors": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {
                            "value": {
                                "name": "John Smith and Jane Doe",
                                "email": "test@example.com"
                            }
                        }
                    }]
                },
                "test_repo.json",
                True,
                "John Smith and Jane Doe"
        ),

        # Non-metadata source (should not detect)
        (
                {
                    "authors": [{
                        "source": "README.md",
                        "technique": "header_analysis",
                        "result": {"value": "John and Jane"}
                    }]
                },
                "test_repo.json",
                False,
                None
        ),

        # Different technique (should not detect)
        (
                {
                    "authors": [{
                        "source": "repository/codemeta.json",
                        "technique": "header_analysis",
                        "result": {"value": "John and Jane"}
                    }]
                },
                "test_repo.json",
                False,
                None
        ),

        # Multiple entries, first non-metadata, second metadata with issue
        (
                {
                    "authors": [
                        {
                            "source": "README.md",
                            "technique": "header_analysis",
                            "result": {"value": "Single Author"}
                        },
                        {
                            "source": "repository/pyproject.toml",
                            "technique": "code_parser",
                            "result": {"value": "Alice & Bob"}
                        }
                    ]
                },
                "test_repo.json",
                True,
                "Alice & Bob"
        ),
    ])
    def test_detect_pitfall_scenarios(self, somef_data, file_name,
                                      expected_has_pitfall, expected_author_value):
        """Test various multiple authors detection scenarios"""
        with patch('metacheck.scripts.pitfalls.p003.extract_metadata_source_filename', return_value="test_file.json"):
            result = detect_multiple_authors_single_field_pitfall(somef_data, file_name)

            assert result["has_pitfall"] == expected_has_pitfall
            assert result["file_name"] == file_name
            assert result["author_value"] == expected_author_value

            if expected_has_pitfall:
                assert result["source"] is not None
                assert result["metadata_source_file"] is not None
                assert result["multiple_authors_detected"] == True

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_multiple_authors_single_field_pitfall(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "author_value" in result
        assert "source" in result
        assert "metadata_source_file" in result
        assert "multiple_authors_detected" in result

    @pytest.mark.parametrize("metadata_file", [
        "codemeta.json", "DESCRIPTION", "composer.json",
        "package.json", "pom.xml", "pyproject.toml",
        "requirements.txt", "setup.py"
    ])
    def test_all_metadata_sources(self, metadata_file):
        """Test that all metadata file types are correctly detected"""
        somef_data = {
            "authors": [{
                "source": f"repository/{metadata_file}",
                "technique": "code_parser",
                "result": {"value": "John and Jane"}
            }]
        }

        with patch('metacheck.scripts.pitfalls.p003.extract_metadata_source_filename', return_value=metadata_file):
            result = detect_multiple_authors_single_field_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] == True

    @pytest.mark.parametrize("separator", [" and ", " & ", ", ", "; ", "\n"])
    def test_all_separator_patterns(self, separator):
        """Test that all separator patterns are detected"""
        author_value = f"Author1{separator}Author2"
        result = has_multiple_authors_in_single_field(author_value)
        assert result == True, f"Failed to detect separator: '{separator}'"