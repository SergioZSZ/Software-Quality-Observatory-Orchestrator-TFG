import pytest
from unittest.mock import patch
from rsmetacheck.scripts.pitfalls.p006 import (
    is_local_file_license,
    detect_local_file_license_pitfall
)


class TestIsLocalFileLicense:
    """Test suite for is_local_file_license function"""

    @pytest.mark.parametrize("license_value,expected", [
        # Empty or None
        ("", False),
        (None, False),

        # Valid license URLs (NOT local files)
        ("https://spdx.org/licenses/MIT.html", False),
        ("https://opensource.org/licenses/MIT", False),
        ("https://www.gnu.org/licenses/gpl-3.0.html", False),
        ("https://creativecommons.org/licenses/by/4.0/", False),
        ("https://www.apache.org/licenses/LICENSE-2.0", False),
        ("https://www.mozilla.org/en-US/MPL/2.0/", False),
        ("https://unlicense.org", False),
        ("https://choosealicense.com/licenses/mit/", False),

        # Valid license names (NOT local files)
        ("MIT", False),
        ("Apache-2.0", False),
        ("GPL-3.0", False),
        ("BSD-3-Clause", False),
        ("ISC", False),

        # Relative path indicators (local files)
        ("./LICENSE", True),
        ("../LICENSE.md", True),
        ("./license.txt", True),

        # Common license file names (local files)
        ("LICENSE", True),
        ("license", True),
        ("LICENSE.md", True),
        ("license.md", True),
        ("LICENSE.txt", True),
        ("license.txt", True),
        ("LICENSE.rst", True),
        ("COPYING", True),
        ("copying", True),
        ("COPYING.md", True),
        ("COPYRIGHT", True),
        ("copyright", True),
        ("COPYRIGHT.md", True),

        # British spelling
        ("LICENCE", True),
        ("licence.md", True),
        ("licence.txt", True),

        # File paths with separators (local files)
        ("docs/LICENSE.md", True),
        ("legal/license.txt", True),
        ("path\\to\\LICENSE", True),

        # Case variations
        ("License", True),
        ("License.MD", True),
        ("license.TXT", True),

        # URLs that look like license names should NOT be flagged
        ("http://example.com/LICENSE", False),
        ("https://example.com/license.md", False),

        # Exact matches
        ("license.md", True),
        ("license.txt", True),
        ("license.rst", True),

        # Edge cases
        ("MIT License", False),  # Has space, likely a name
        ("Apache License 2.0", False),  # Has spaces

        # Should catch these patterns
        ("readme.md", True),
        ("doc.txt", True),
        ("file.rst", True),
    ])
    def test_local_file_detection_scenarios(self, license_value, expected):
        """Test various license value scenarios for local file detection"""
        result = is_local_file_license(license_value)
        assert result == expected

    @pytest.mark.parametrize("valid_url", [
        "https://spdx.org/licenses/MIT.html",
        "https://opensource.org/licenses/Apache-2.0",
        "https://www.gnu.org/licenses/gpl-3.0.html",
        "https://creativecommons.org/licenses/by-sa/4.0/",
        "https://www.apache.org/licenses/LICENSE-2.0.txt",
        "https://www.mozilla.org/en-US/MPL/2.0/",
        "https://unlicense.org/",
        "https://choosealicense.com/licenses/mit/",
    ])
    def test_valid_license_urls_not_detected(self, valid_url):
        """Test that valid license URLs are not detected as local files"""
        result = is_local_file_license(valid_url)
        assert result == False

    @pytest.mark.parametrize("file_name", [
        "LICENSE", "license", "LICENSE.md", "license.md",
        "LICENSE.txt", "license.txt", "LICENSE.rst",
        "COPYING", "copying", "COPYING.md", "copying.txt",
        "COPYRIGHT", "copyright", "COPYRIGHT.md",
        "LICENCE", "licence", "licence.md", "licence.txt"
    ])
    def test_common_license_file_names(self, file_name):
        """Test that common license file names are detected"""
        result = is_local_file_license(file_name)
        assert result == True

    @pytest.mark.parametrize("path", [
        "./LICENSE",
        "../LICENSE.md",
        "docs/LICENSE",
        "legal/license.txt",
        "path/to/LICENSE.md",
    ])
    def test_paths_detected(self, path):
        """Test that file paths are detected as local files"""
        result = is_local_file_license(path)
        assert result == True


class TestDetectLocalFileLicensePitfall:
    """Test suite for detect_local_file_license_pitfall function"""

    @pytest.mark.parametrize("somef_data,file_name,expected_has_pitfall,expected_license_value", [
        # No license key
        (
                {},
                "test_repo.json",
                False,
                None
        ),

        # license not a list
        (
                {"license": "MIT"},
                "test_repo.json",
                False,
                None
        ),

        # Empty license list
        (
                {"license": []},
                "test_repo.json",
                False,
                None
        ),

        # Valid license name (no pitfall)
        (
                {
                    "license": [{
                        "technique": "code_parser",
                        "source": "repository/codemeta.json",
                        "result": {"value": "MIT"}
                    }]
                },
                "test_repo.json",
                False,
                None
        ),

        # Valid license URL (no pitfall)
        (
                {
                    "license": [{
                        "technique": "code_parser",
                        "source": "repository/package.json",
                        "result": {"value": "https://spdx.org/licenses/MIT.html"}
                    }]
                },
                "test_repo.json",
                False,
                None
        ),

        # Local file "LICENSE" (pitfall)
        (
                {
                    "license": [{
                        "technique": "code_parser",
                        "source": "repository/codemeta.json",
                        "result": {"value": "LICENSE"}
                    }]
                },
                "test_repo.json",
                True,
                "LICENSE"
        ),

        # Local file "license.md" (pitfall)
        (
                {
                    "license": [{
                        "technique": "code_parser",
                        "source": "repository/package.json",
                        "result": {"value": "license.md"}
                    }]
                },
                "test_repo.json",
                True,
                "license.md"
        ),

        # Relative path "./LICENSE" (pitfall)
        (
                {
                    "license": [{
                        "technique": "code_parser",
                        "source": "repository/setup.py",
                        "result": {"value": "./LICENSE"}
                    }]
                },
                "test_repo.json",
                True,
                "./LICENSE"
        ),

        # File path "docs/LICENSE.md" (pitfall)
        (
                {
                    "license": [{
                        "technique": "code_parser",
                        "source": "repository/codemeta.json",
                        "result": {"value": "docs/LICENSE.md"}
                    }]
                },
                "test_repo.json",
                True,
                "docs/LICENSE.md"
        ),

        # Source without metadata file but any metadata source pattern
        (
                {
                    "license": [{
                        "technique": "code_parser",
                        "source": "some/CODEMETA.JSON",
                        "result": {"value": "LICENSE"}
                    }]
                },
                "test_repo.json",
                True,
                "LICENSE"
        ),

        # Non-metadata source (should not detect)
        (
                {
                    "license": [{
                        "technique": "header_analysis",
                        "source": "README.md",
                        "result": {"value": "LICENSE"}
                    }]
                },
                "test_repo.json",
                False,
                None
        ),

        # Multiple entries, first non-metadata, second metadata with local file
        (
                {
                    "license": [
                        {
                            "technique": "header_analysis",
                            "source": "README.md",
                            "result": {"value": "MIT"}
                        },
                        {
                            "technique": "code_parser",
                            "source": "repository/pyproject.toml",
                            "result": {"value": "license.txt"}
                        }
                    ]
                },
                "test_repo.json",
                True,
                "license.txt"
        ),

        # Missing result or value
        (
                {
                    "license": [{
                        "technique": "code_parser",
                        "source": "repository/codemeta.json"
                    }]
                },
                "test_repo.json",
                False,
                None
        ),
    ])
    def test_detect_pitfall_scenarios(self, somef_data, file_name,
                                      expected_has_pitfall, expected_license_value):
        """Test various local file license detection scenarios"""
        with patch('metacheck.scripts.pitfalls.p006.extract_metadata_source_filename', return_value="test_file.json"):
            result = detect_local_file_license_pitfall(somef_data, file_name)

            assert result["has_pitfall"] == expected_has_pitfall
            assert result["file_name"] == file_name
            assert result["license_value"] == expected_license_value

            if expected_has_pitfall:
                assert result["source"] is not None
                assert result["metadata_source_file"] is not None
                assert result["is_local_file"] == True

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_local_file_license_pitfall(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "license_value" in result
        assert "source" in result
        assert "metadata_source_file" in result
        assert "is_local_file" in result

    @pytest.mark.parametrize("metadata_file", [
        "codemeta.json", "DESCRIPTION", "composer.json",
        "package.json", "pom.xml", "pyproject.toml",
        "requirements.txt", "setup.py"
    ])
    def test_all_metadata_sources(self, metadata_file):
        """Test that all metadata file types are correctly detected"""
        somef_data = {
            "license": [{
                "technique": "code_parser",
                "source": f"repository/{metadata_file}",
                "result": {"value": "LICENSE"}
            }]
        }

        with patch('metacheck.scripts.pitfalls.p006.extract_metadata_source_filename', return_value=metadata_file):
            result = detect_local_file_license_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] == True

    @pytest.mark.parametrize("local_file", [
        "LICENSE", "license", "LICENSE.md", "license.txt",
        "./LICENSE", "../LICENSE.md", "docs/LICENSE",
        "COPYING", "COPYRIGHT", "LICENCE"
    ])
    def test_different_local_file_patterns(self, local_file):
        """Test detection of different local file patterns"""
        somef_data = {
            "license": [{
                "technique": "code_parser",
                "source": "repository/codemeta.json",
                "result": {"value": local_file}
            }]
        }

        with patch('metacheck.scripts.pitfalls.p006.extract_metadata_source_filename', return_value="codemeta.json"):
            result = detect_local_file_license_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] == True

    def test_stops_at_first_pitfall(self):
        """Test that detection stops at first pitfall found"""
        somef_data = {
            "license": [
                {
                    "technique": "code_parser",
                    "source": "repository/codemeta.json",
                    "result": {"value": "LICENSE"}
                },
                {
                    "technique": "code_parser",
                    "source": "repository/package.json",
                    "result": {"value": "license.md"}
                }
            ]
        }

        with patch('metacheck.scripts.pitfalls.p006.extract_metadata_source_filename', return_value="test.json"):
            result = detect_local_file_license_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] == True
            assert result["license_value"] == "LICENSE"

    def test_source_fallback_to_technique(self):
        """Test that source falls back to technique when source is empty"""
        somef_data = {
            "license": [{
                "technique": "code_parser",
                "source": "",
                "result": {"value": "LICENSE"}
            }]
        }

        with patch('metacheck.scripts.pitfalls.p006.extract_metadata_source_filename', return_value=""):
            result = detect_local_file_license_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] == True
            assert "technique: code_parser" in result["source"]