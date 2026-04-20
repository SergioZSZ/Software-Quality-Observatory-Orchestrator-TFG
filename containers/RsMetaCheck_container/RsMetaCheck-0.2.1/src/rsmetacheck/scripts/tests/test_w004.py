import pytest
from rsmetacheck.scripts.warnings.w004 import detect_programming_language_no_version_pitfall


class TestDetectProgrammingLanguageNoVersionPitfall:
    """Test suite for detect_programming_language_no_version_pitfall function"""

    @pytest.mark.parametrize("somef_data,file_name,expected_has_warning,expected_languages", [
        # No programming_languages key
        (
                {},
                "test_repo.json",
                False,
                []
        ),

        # programming_languages not a list
        (
                {"programming_languages": "Python"},
                "test_repo.json",
                False,
                []
        ),

        # Empty programming_languages list
        (
                {"programming_languages": []},
                "test_repo.json",
                False,
                []
        ),

        # Language with version (no warning)
        (
                {
                    "programming_languages": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {
                            "name": "Python",
                            "version": "3.9"
                        }
                    }]
                },
                "test_repo.json",
                False,
                []
        ),

        # Language without version (warning)
        (
                {
                    "programming_languages": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {
                            "name": "Python",
                            "version": None
                        }
                    }]
                },
                "test_repo.json",
                True,
                ["Python"]
        ),

        # Multiple languages, all with versions (no warning)
        (
                {
                    "programming_languages": [
                        {
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {
                                "name": "Python",
                                "version": "3.9"
                            }
                        },
                        {
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {
                                "name": "JavaScript",
                                "version": "ES6"
                            }
                        }
                    ]
                },
                "test_repo.json",
                False,
                []
        ),

        # Multiple languages, some without versions (warning)
        (
                {
                    "programming_languages": [
                        {
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {
                                "name": "Python",
                                "version": "3.9"
                            }
                        },
                        {
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {
                                "name": "JavaScript",
                                "version": None
                            }
                        },
                        {
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {
                                "name": "Java",
                                "version": None
                            }
                        }
                    ]
                },
                "test_repo.json",
                True,
                ["JavaScript", "Java"]
        ),

        # All languages without versions (warning)
        (
                {
                    "programming_languages": [
                        {
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {
                                "name": "Python",
                                "version": None
                            }
                        },
                        {
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {
                                "name": "R",
                                "version": None
                            }
                        }
                    ]
                },
                "test_repo.json",
                True,
                ["Python", "R"]
        ),

        # Language without name field
        (
                {
                    "programming_languages": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {
                            "version": None
                        }
                    }]
                },
                "test_repo.json",
                True,
                ["Unknown"]
        ),

        # Non-codemeta source (should not detect)
        (
                {
                    "programming_languages": [{
                        "source": "README.md",
                        "technique": "header_analysis",
                        "result": {
                            "name": "Python",
                            "version": None
                        }
                    }]
                },
                "test_repo.json",
                False,
                []
        ),

        # Wrong technique (should not detect)
        (
                {
                    "programming_languages": [{
                        "source": "repository/codemeta.json",
                        "technique": "file_exploration",
                        "result": {
                            "name": "Python",
                            "version": None
                        }
                    }]
                },
                "test_repo.json",
                False,
                []
        ),

        # Mixed sources, only codemeta detected
        (
                {
                    "programming_languages": [
                        {
                            "source": "README.md",
                            "technique": "header_analysis",
                            "result": {
                                "name": "Python",
                                "version": None
                            }
                        },
                        {
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {
                                "name": "JavaScript",
                                "version": None
                            }
                        }
                    ]
                },
                "test_repo.json",
                True,
                ["JavaScript"]
        ),

        # Version field exists but is explicitly None
        (
                {
                    "programming_languages": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {
                            "name": "C++",
                            "version": None
                        }
                    }]
                },
                "test_repo.json",
                True,
                ["C++"]
        ),

        # Version field missing entirely (treated as None)
        (
                {
                    "programming_languages": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {
                            "name": "Ruby"
                        }
                    }]
                },
                "test_repo.json",
                True,
                ["Ruby"]
        ),
    ])
    def test_detect_warning_scenarios(self, somef_data, file_name,
                                      expected_has_warning, expected_languages):
        """Test various programming language version warning scenarios"""
        result = detect_programming_language_no_version_pitfall(somef_data, file_name)

        assert result["has_warning"] == expected_has_warning
        assert result["file_name"] == file_name
        assert result["programming_languages_without_version"] == expected_languages

        if expected_has_warning:
            assert result["source"] is not None
            assert len(result["programming_languages_without_version"]) > 0

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_programming_language_no_version_pitfall(somef_data, "test.json")

        assert "has_warning" in result
        assert "file_name" in result
        assert "programming_languages_without_version" in result
        assert "source" in result

    @pytest.mark.parametrize("language_name", [
        "Python", "JavaScript", "Java", "C++", "C", "Go",
        "Rust", "Ruby", "PHP", "Swift", "Kotlin", "R"
    ])
    def test_different_programming_languages(self, language_name):
        """Test detection works for various programming languages"""
        somef_data = {
            "programming_languages": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {
                    "name": language_name,
                    "version": None
                }
            }]
        }

        result = detect_programming_language_no_version_pitfall(somef_data, "test.json")
        assert result["has_warning"] == True
        assert language_name in result["programming_languages_without_version"]

    def test_accumulates_multiple_languages_without_version(self):
        """Test that all languages without versions are accumulated"""
        somef_data = {
            "programming_languages": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"name": "Python", "version": None}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"name": "JavaScript", "version": None}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"name": "C++", "version": None}
                }
            ]
        }

        result = detect_programming_language_no_version_pitfall(somef_data, "test.json")
        assert result["has_warning"] == True
        assert len(result["programming_languages_without_version"]) == 3
        assert "Python" in result["programming_languages_without_version"]
        assert "JavaScript" in result["programming_languages_without_version"]
        assert "C++" in result["programming_languages_without_version"]

    def test_only_counts_null_versions_not_with_versions(self):
        """Test that only null versions are counted, not languages with versions"""
        somef_data = {
            "programming_languages": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"name": "Python", "version": "3.9"}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"name": "JavaScript", "version": None}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"name": "Java", "version": "11"}
                }
            ]
        }

        result = detect_programming_language_no_version_pitfall(somef_data, "test.json")
        assert result["has_warning"] == True
        assert len(result["programming_languages_without_version"]) == 1
        assert "JavaScript" in result["programming_languages_without_version"]
        assert "Python" not in result["programming_languages_without_version"]
        assert "Java" not in result["programming_languages_without_version"]

    def test_source_is_set_from_last_entry(self):
        """Test that source is set from entries (last one wins)"""
        somef_data = {
            "programming_languages": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"name": "Python", "version": None}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"name": "JavaScript", "version": None}
                }
            ]
        }

        result = detect_programming_language_no_version_pitfall(somef_data, "test.json")
        assert result["source"] == "repository/codemeta.json"

    def test_handles_missing_result_field(self):
        """Test handling when result field is missing"""
        somef_data = {
            "programming_languages": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser"
                # No result field
            }]
        }

        result = detect_programming_language_no_version_pitfall(somef_data, "test.json")
        # Should not crash, just return no warning
        assert result["has_warning"] == False

    def test_version_empty_string_not_treated_as_null(self):
        """Test that empty string version is not treated the same as None"""
        # Note: Current implementation only checks for None, not empty string
        somef_data = {
            "programming_languages": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {
                    "name": "Python",
                    "version": ""  # Empty string, not None
                }
            }]
        }

        result = detect_programming_language_no_version_pitfall(somef_data, "test.json")
        # Empty string is not None, so no warning
        assert result["has_warning"] == False

    def test_multiple_entries_same_language(self):
        """Test handling of multiple entries for the same language"""
        somef_data = {
            "programming_languages": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"name": "Python", "version": None}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"name": "Python", "version": None}
                }
            ]
        }

        result = detect_programming_language_no_version_pitfall(somef_data, "test.json")
        assert result["has_warning"] == True
        # Both entries should be added (no deduplication in current implementation)
        assert result["programming_languages_without_version"].count("Python") == 2

    @pytest.mark.parametrize("version_value", [
        "3.9", "2.7.18", "11", "ES6", "C++17", "1.0.0", "latest"
    ])
    def test_various_version_formats(self, version_value):
        """Test that various version formats are recognized as having version"""
        somef_data = {
            "programming_languages": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {
                    "name": "Language",
                    "version": version_value
                }
            }]
        }

        result = detect_programming_language_no_version_pitfall(somef_data, "test.json")
        assert result["has_warning"] == False

    def test_default_unknown_name_when_name_missing(self):
        """Test that 'Unknown' is used when name field is missing"""
        somef_data = {
            "programming_languages": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {
                    "version": None
                    # No name field
                }
            }]
        }

        result = detect_programming_language_no_version_pitfall(somef_data, "test.json")
        assert result["has_warning"] == True
        assert "Unknown" in result["programming_languages_without_version"]