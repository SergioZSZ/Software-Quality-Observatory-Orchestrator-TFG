import pytest
from rsmetacheck.scripts.pitfalls.p017 import (
    detect_codemeta_version_mismatch_pitfall,
    get_codemeta_version,
    get_other_metadata_versions
)


class TestGetCodemetaVersion:
    """Test suite for get_codemeta_version function"""

    @pytest.mark.parametrize(
        "somef_data,expected_version", [
            # No version key
            ({}, None),

            # version not a list
            ({"version": "1.0.0"}, None),

            # Empty version list
            ({"version": []}, None),

            # Version from codemeta.json
            (
                    {
                        "version": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "1.2.3"}
                        }]
                    },
                    "1.2.3"
            ),

            # Version from codemeta with lowercase source
            (
                    {
                        "version": [{
                            "source": "repository/CODEMETA.json",
                            "technique": "code_parser",
                            "result": {"value": "2.0.0"}
                        }]
                    },
                    "2.0.0"
            ),

            # Multiple versions, one from codemeta
            (
                    {
                        "version": [
                            {
                                "source": "repository/setup.py",
                                "technique": "code_parser",
                                "result": {"value": "1.0.0"}
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "1.2.3"}
                            }
                        ]
                    },
                    "1.2.3"
            ),

            # No codemeta version
            (
                    {
                        "version": [{
                            "source": "repository/setup.py",
                            "technique": "code_parser",
                            "result": {"value": "1.0.0"}
                        }]
                    },
                    None
            ),

            # Missing result key
            (
                    {
                        "version": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser"
                        }]
                    },
                    None
            ),

            # Missing value in result
            (
                    {
                        "version": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {}
                        }]
                    },
                    None
            ),
        ])
    def test_get_codemeta_version_scenarios(self, somef_data, expected_version):
        """Test various scenarios for getting codemeta version"""
        assert get_codemeta_version(somef_data) == expected_version


class TestGetOtherMetadataVersions:
    """Test suite for get_other_metadata_versions function"""

    def test_no_version_key(self):
        """Test with no version key"""
        assert get_other_metadata_versions({}) == []

    def test_version_not_list(self):
        """Test with version not being a list"""
        assert get_other_metadata_versions({"version": "1.0.0"}) == []

    def test_empty_version_list(self):
        """Test with empty version list"""
        assert get_other_metadata_versions({"version": []}) == []

    def test_single_metadata_version(self):
        """Test extracting single metadata version"""
        somef_data = {
            "version": [{
                "source": "repository/setup.py",
                "technique": "code_parser",
                "result": {"value": "1.0.0"}
            }]
        }

        result = get_other_metadata_versions(somef_data)
        assert len(result) == 1
        assert result[0]["version"] == "1.0.0"
        assert result[0]["source"] == "repository/setup.py"

    def test_multiple_metadata_versions(self):
        """Test extracting multiple metadata versions"""
        somef_data = {
            "version": [
                {
                    "source": "repository/setup.py",
                    "technique": "code_parser",
                    "result": {"value": "1.0.0"}
                },
                {
                    "source": "repository/package.json",
                    "technique": "code_parser",
                    "result": {"value": "1.0.1"}
                }
            ]
        }

        result = get_other_metadata_versions(somef_data)
        assert len(result) == 2

    def test_excludes_codemeta_version(self):
        """Test that codemeta.json version is excluded"""
        somef_data = {
            "version": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "1.0.0"}
                },
                {
                    "source": "repository/setup.py",
                    "technique": "code_parser",
                    "result": {"value": "1.0.1"}
                }
            ]
        }

        result = get_other_metadata_versions(somef_data)
        assert len(result) == 1
        assert result[0]["version"] == "1.0.1"

    @pytest.mark.parametrize("metadata_source", [
        "repository/DESCRIPTION",
        "repository/composer.json",
        "repository/package.json",
        "repository/pom.xml",
        "repository/pyproject.toml",
        "repository/requirements.txt",
        "repository/setup.py"
    ])
    def test_all_metadata_sources(self, metadata_source):
        """Test that all metadata sources are recognized"""
        somef_data = {
            "version": [{
                "source": metadata_source,
                "technique": "code_parser",
                "result": {"value": "1.0.0"}
            }]
        }

        result = get_other_metadata_versions(somef_data)
        assert len(result) == 1
        assert result[0]["source"] == metadata_source


class TestDetectCodemetaVersionMismatchPitfall:
    """Test suite for detect_codemeta_version_mismatch_pitfall function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_pitfall,expected_codemeta_version,expected_mismatch_count", [
            # No version key
            (
                    {},
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # No codemeta version
            (
                    {
                        "version": [{
                            "source": "repository/setup.py",
                            "technique": "code_parser",
                            "result": {"value": "1.0.0"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # Codemeta version but no other versions
            (
                    {
                        "version": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "1.0.0"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # Matching versions (no pitfall)
            (
                    {
                        "version": [
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "1.0.0"}
                            },
                            {
                                "source": "repository/setup.py",
                                "technique": "code_parser",
                                "result": {"value": "1.0.0"}
                            }
                        ]
                    },
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # Mismatched versions (pitfall)
            (
                    {
                        "version": [
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "1.0.0"}
                            },
                            {
                                "source": "repository/setup.py",
                                "technique": "code_parser",
                                "result": {"value": "1.0.1"}
                            }
                        ]
                    },
                    "test_repo.json",
                    True,
                    "1.0.0",
                    1
            ),

            # Multiple mismatched versions
            (
                    {
                        "version": [
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "1.0.0"}
                            },
                            {
                                "source": "repository/setup.py",
                                "technique": "code_parser",
                                "result": {"value": "1.0.1"}
                            },
                            {
                                "source": "repository/package.json",
                                "technique": "code_parser",
                                "result": {"value": "1.0.2"}
                            }
                        ]
                    },
                    "test_repo.json",
                    True,
                    "1.0.0",
                    2
            ),

            # Mixed matching and mismatched
            (
                    {
                        "version": [
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "1.0.0"}
                            },
                            {
                                "source": "repository/setup.py",
                                "technique": "code_parser",
                                "result": {"value": "1.0.0"}
                            },
                            {
                                "source": "repository/package.json",
                                "technique": "code_parser",
                                "result": {"value": "1.0.1"}
                            }
                        ]
                    },
                    "test_repo.json",
                    True,
                    "1.0.0",
                    1
            ),

            # Whitespace handling (should match after strip)
            (
                    {
                        "version": [
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "  1.0.0  "}
                            },
                            {
                                "source": "repository/setup.py",
                                "technique": "code_parser",
                                "result": {"value": "1.0.0"}
                            }
                        ]
                    },
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # Whitespace in mismatch
            (
                    {
                        "version": [
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "  1.0.0  "}
                            },
                            {
                                "source": "repository/setup.py",
                                "technique": "code_parser",
                                "result": {"value": "1.0.1"}
                            }
                        ]
                    },
                    "test_repo.json",
                    True,
                    "  1.0.0  ",
                    1
            ),
        ])
    def test_detect_version_mismatch_scenarios(self, somef_data, file_name,
                                               expected_has_pitfall, expected_codemeta_version,
                                               expected_mismatch_count):
        """Test various scenarios for version mismatch detection"""
        result = detect_codemeta_version_mismatch_pitfall(somef_data, file_name)

        assert result["has_pitfall"] == expected_has_pitfall
        assert result["file_name"] == file_name
        assert result["codemeta_version"] == expected_codemeta_version

        if expected_has_pitfall:
            assert len(result["mismatched_versions"]) == expected_mismatch_count
            assert result["metadata_source_file"] == "codemeta.json"

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_codemeta_version_mismatch_pitfall(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "codemeta_version" in result
        assert "metadata_source_file" in result
        assert "other_versions" in result
        assert "mismatched_versions" in result

    def test_semantic_version_strict_comparison(self):
        """Test that version comparison is strict (not semantic)"""
        somef_data = {
            "version": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "1.0"}
                },
                {
                    "source": "repository/setup.py",
                    "technique": "code_parser",
                    "result": {"value": "1.0.0"}
                }
            ]
        }

        result = detect_codemeta_version_mismatch_pitfall(somef_data, "test.json")
        # These should be considered different since it's string comparison
        assert result["has_pitfall"] is True

    def test_version_with_prefix(self):
        """Test versions with v prefix are treated as different"""
        somef_data = {
            "version": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "v1.0.0"}
                },
                {
                    "source": "repository/setup.py",
                    "technique": "code_parser",
                    "result": {"value": "1.0.0"}
                }
            ]
        }

        result = detect_codemeta_version_mismatch_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True

    def test_case_sensitive_versions(self):
        """Test that version comparison is case sensitive"""
        somef_data = {
            "version": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "1.0.0-BETA"}
                },
                {
                    "source": "repository/setup.py",
                    "technique": "code_parser",
                    "result": {"value": "1.0.0-beta"}
                }
            ]
        }

        result = detect_codemeta_version_mismatch_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True

    def test_other_versions_includes_all_metadata(self):
        """Test that other_versions includes all non-codemeta metadata"""
        somef_data = {
            "version": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "1.0.0"}
                },
                {
                    "source": "repository/setup.py",
                    "technique": "code_parser",
                    "result": {"value": "1.0.1"}
                },
                {
                    "source": "repository/package.json",
                    "technique": "code_parser",
                    "result": {"value": "1.0.0"}
                }
            ]
        }

        result = detect_codemeta_version_mismatch_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True
        assert len(result["other_versions"]) == 2
        assert len(result["mismatched_versions"]) == 1

    def test_all_other_versions_mismatch(self):
        """Test when all other versions mismatch"""
        somef_data = {
            "version": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "1.0.0"}
                },
                {
                    "source": "repository/setup.py",
                    "technique": "code_parser",
                    "result": {"value": "2.0.0"}
                },
                {
                    "source": "repository/package.json",
                    "technique": "code_parser",
                    "result": {"value": "3.0.0"}
                }
            ]
        }

        result = detect_codemeta_version_mismatch_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True
        assert len(result["mismatched_versions"]) == 2
        assert result["mismatched_versions"][0]["version"] == "2.0.0"
        assert result["mismatched_versions"][1]["version"] == "3.0.0"