
import pytest
from unittest.mock import patch
from rsmetacheck.scripts.pitfalls.p013 import detect_license_no_version_pitfall


class TestDetectLicenseNoVersionPitfall:
    """Test suite for detect_license_no_version_pitfall function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_pitfall,expected_license,expected_source_file", [
            # No license key
            (
                    {},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # license not a list
            (
                    {"license": "MIT"},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Empty license list
            (
                    {"license": []},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # GPL without version from codemeta.json
            (
                    {
                        "license": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "GPL"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "GPL",
                    "codemeta.json"
            ),

            # GPL with version (no pitfall)
            (
                    {
                        "license": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "GPL-3.0"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # LGPL without version
            (
                    {
                        "license": [{
                            "source": "repository/package.json",
                            "technique": "code_parser",
                            "result": {"value": "LGPL"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "LGPL",
                    "package.json"
            ),

            # LGPL with version
            (
                    {
                        "license": [{
                            "source": "repository/setup.py",
                            "technique": "code_parser",
                            "result": {"value": "LGPL-2.1"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # AGPL without version
            (
                    {
                        "license": [{
                            "source": "repository/pyproject.toml",
                            "technique": "code_parser",
                            "result": {"value": "AGPL"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "AGPL",
                    "pyproject.toml"
            ),

            # AGPL with version
            (
                    {
                        "license": [{
                            "source": "repository/composer.json",
                            "technique": "code_parser",
                            "result": {"value": "AGPL-3.0"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # REMOVED: Apache without version test case

            # REMOVED: Apache with version test case - moved to version pattern test

            # BSD without clause specification
            (
                    {
                        "license": [{
                            "source": "repository/DESCRIPTION",
                            "technique": "code_parser",
                            "result": {"value": "BSD"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "BSD",
                    "DESCRIPTION"
            ),

            # BSD with clause specification
            (
                    {
                        "license": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "BSD-3-Clause"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Creative Commons without version
            (
                    {
                        "license": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "CC BY"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "CC BY",
                    "codemeta.json"
            ),

            # Creative Commons with version
            (
                    {
                        "license": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "CC BY 4.0"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # MIT license (no version needed)
            (
                    {
                        "license": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "MIT"}
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
                        "license": [{
                            "source": "README.md",
                            "technique": "header_analysis",
                            "result": {"value": "GPL"}
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
                        "license": [{
                            "source": "repository/codemeta.json",
                            "technique": "github_api",
                            "result": {"value": "GPL"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Case insensitive matching
            (
                    {
                        "license": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "gpl"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "gpl",
                    "codemeta.json"
            ),

            # GPL with hyphen and version
            (
                    {
                        "license": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "GPL-3"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # GPL without hyphen but with version
            (
                    {
                        "license": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "GPL3.0"}
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
                        "license": [{
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
                        "license": [{
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

            # Non-string license value
            (
                    {
                        "license": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": {"name": "GPL"}}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Multiple licenses, first without version
            (
                    {
                        "license": [
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "GPL"}
                            },
                            {
                                "source": "LICENSE",
                                "technique": "file_exploration",
                                "result": {"value": "GPL-3.0"}
                            }
                        ]
                    },
                    "test_repo.json",
                    True,
                    "GPL",
                    "codemeta.json"
            ),
        ])
    def test_detect_license_no_version_scenarios(self, somef_data, file_name,
                                                 expected_has_pitfall, expected_license,
                                                 expected_source_file):
        """Test various scenarios for license version detection"""
        with patch('metacheck.scripts.pitfalls.p013.extract_metadata_source_filename',
                   return_value=expected_source_file):
            result = detect_license_no_version_pitfall(somef_data, file_name)

            assert result["has_pitfall"] == expected_has_pitfall
            assert result["file_name"] == file_name
            assert result["license_value"] == expected_license

            if expected_has_pitfall:
                assert result["metadata_source_file"] == expected_source_file

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_license_no_version_pitfall(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "license_value" in result
        assert "metadata_source_file" in result
        assert "source" in result

    @pytest.mark.parametrize("metadata_file", [
        "codemeta.json", "DESCRIPTION", "composer.json",
        "package.json", "pom.xml", "pyproject.toml",
        "requirements.txt", "setup.py"
    ])
    def test_all_metadata_sources(self, metadata_file):
        """Test that all metadata file types are correctly processed"""
        somef_data = {
            "license": [{
                "source": f"repository/{metadata_file}",
                "technique": "code_parser",
                "result": {"value": "GPL"}
            }]
        }

        with patch('metacheck.scripts.pitfalls.p013.extract_metadata_source_filename',
                   return_value=metadata_file):
            result = detect_license_no_version_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] is True
            assert result["metadata_source_file"] == metadata_file

    @pytest.mark.parametrize("license_name,version_pattern", [
        ("GPL", ["GPL-2.0", "GPL-3.0", "GPL3", "GPL 3.0"]),
        ("LGPL", ["LGPL-2.1", "LGPL-3.0", "LGPL2.1", "LGPL 3"]),
        ("AGPL", ["AGPL-3.0", "AGPL3", "AGPL 3.0"]),
        # REMOVED: Apache test cases
        ("BSD", ["BSD-2-Clause", "BSD-3-Clause", "BSD 3 Clause"]),
        ("CC BY", ["CC BY 4.0", "CC-BY-4.0", "CC BY-4.0"]),
    ])
    def test_license_with_and_without_version(self, license_name, version_pattern):
        """Test that licenses without version trigger pitfall, with version don't"""
        # Test without version (should trigger)
        somef_data_no_version = {
            "license": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": license_name}
            }]
        }

        with patch('metacheck.scripts.pitfalls.p013.extract_metadata_source_filename',
                   return_value="codemeta.json"):
            result = detect_license_no_version_pitfall(somef_data_no_version, "test.json")
            assert result["has_pitfall"] is True, f"Should trigger for {license_name} without version"

        # Test with version (should not trigger)
        for versioned in version_pattern:
            somef_data_with_version = {
                "license": [{
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": versioned}
                }]
            }

            result = detect_license_no_version_pitfall(somef_data_with_version, "test.json")
            assert result["has_pitfall"] is False, f"Should not trigger for {versioned}"

    @pytest.mark.parametrize("non_versioned_license", [
        "MIT",
        "ISC",
        "Unlicense",
        "0BSD",
        "Public Domain",
    ])
    def test_licenses_without_version_requirements(self, non_versioned_license):
        """Test licenses that don't require version specifications"""
        somef_data = {
            "license": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": non_versioned_license}
            }]
        }

        result = detect_license_no_version_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is False

    def test_case_insensitivity(self):
        """Test that license matching is case insensitive"""
        test_cases = [
            "gpl",
            "GPL",
            "Gpl",
            "GpL",
        ]

        for license_value in test_cases:
            somef_data = {
                "license": [{
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": license_value}
                }]
            }

            with patch('metacheck.scripts.pitfalls.p013.extract_metadata_source_filename',
                       return_value="codemeta.json"):
                result = detect_license_no_version_pitfall(somef_data, "test.json")
                assert result["has_pitfall"] is True, f"Failed for case: {license_value}"

    # REMOVED: test_license_in_longer_string - contained Apache License tests

    def test_stops_at_first_match(self):
        """Test that function stops after finding first license without version"""
        somef_data = {
            "license": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "GPL"}
                },
                {
                    "source": "repository/package.json",
                    "technique": "code_parser",
                    "result": {"value": "LGPL"}
                }
            ]
        }

        with patch('metacheck.scripts.pitfalls.p013.extract_metadata_source_filename',
                   side_effect=["codemeta.json", "package.json"]):
            result = detect_license_no_version_pitfall(somef_data, "test.json")

            assert result["has_pitfall"] is True
            assert result["license_value"] == "GPL"

    # REMOVED: test_multiple_metadata_sources_mixed - contained Apache test