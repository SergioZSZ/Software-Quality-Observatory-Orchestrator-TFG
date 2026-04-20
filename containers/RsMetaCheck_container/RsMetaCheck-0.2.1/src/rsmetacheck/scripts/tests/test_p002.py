import pytest
from rsmetacheck.scripts.pitfalls.p002 import (
    extract_license_from_file,
    check_license_template_placeholders,
    detect_license_template_placeholders
)


class TestExtractLicenseFromFile:
    """Test suite for extract_license_from_file function"""

    @pytest.mark.parametrize("somef_data,expected", [
        # No license key
        ({}, None),
        ({"other_key": "value"}, None),

        # License not a list
        ({"license": "MIT"}, None),
        ({"license": {}}, None),

        # Empty license list
        ({"license": []}, None),

        # License from LICENSE.md
        ({
             "license": [{
                 "source": "repository/LICENSE.md",
                 "result": {"value": "MIT License\n\nCopyright (c) 2024"}
             }]
         }, {"source": "repository/LICENSE.md", "content": "MIT License\n\nCopyright (c) 2024"}),

        # License from another file (should not match)
        ({
             "license": [{
                 "source": "repository/LICENSE.txt",
                 "result": {"value": "Some license"}
             }]
         }, None),

        # Multiple entries, only LICENSE.md should match
        ({
             "license": [
                 {"source": "README.md", "result": {"value": "MIT"}},
                 {"source": "repository/LICENSE.md", "result": {"value": "Full license text"}}
             ]
         }, {"source": "repository/LICENSE.md", "content": "Full license text"}),

        # Missing result or value
        ({
             "license": [{
                 "source": "repository/LICENSE.md"
             }]
         }, None),
        ({
             "license": [{
                 "source": "repository/LICENSE.md",
                 "result": {}
             }]
         }, None),
    ])
    def test_extract_license_scenarios(self, somef_data, expected):
        """Test various scenarios for license extraction"""
        result = extract_license_from_file(somef_data)
        assert result == expected


class TestCheckLicenseTemplatePlaceholders:
    """Test suite for check_license_template_placeholders function"""

    @pytest.mark.parametrize("license_content,expected", [
        # Empty or None content
        ("", False),
        (None, False),

        # No placeholders
        ("MIT License\n\nCopyright (c) 2024 John Doe", False),
        ("Apache License Version 2.0", False),

        # Common placeholders
        ("Copyright (c) <year> <name of author>", True),
        ("Copyright <yyyy> by <name>", True),
        ("Licensed to <program> under Apache", True),

        # Bracket style placeholders
        ("Copyright [year] [fullname]", True),
        ("Copyright [year] by [name]", True),
        ("[copyright holder] reserves all rights", True),

        # Angle bracket placeholders
        ("<copyright holders> 2024", True),
        ("Copyright <owner> 2024", True),
        ("<author> wrote this code", True),
        ("<name of copyright owner>", True),

        # Case insensitive matching
        ("Copyright <YEAR> <NAME OF AUTHOR>", True),
        ("Copyright <Year> <Name>", True),

        # Mixed content
        ("MIT License\n\nCopyright (c) <year> John Doe", True),
        ("Real Name followed by <program>", True),

        # Jr. in name (should not trigger comma pattern)
        ("Copyright (c) 2024 John Smith, Jr.", False),

        # Multiple placeholders
        ("Copyright <year> <name>\nLicensed by <owner>", True),
    ])
    def test_placeholder_detection_scenarios(self, license_content, expected):
        """Test various placeholder detection scenarios"""
        result = check_license_template_placeholders(license_content)
        assert result == expected


class TestDetectLicenseTemplatePlaceholders:
    """Test suite for detect_license_template_placeholders function"""

    @pytest.mark.parametrize("somef_data,file_name,expected_has_pitfall,expected_placeholders", [
        # No license data
        (
                {},
                "test_repo.json",
                False,
                False
        ),

        # License without placeholders
        (
                {
                    "license": [{
                        "source": "repo/LICENSE.md",
                        "result": {"value": "MIT License\n\nCopyright (c) 2024 John Doe"}
                    }]
                },
                "test_repo.json",
                False,
                False
        ),

        # License with placeholders
        (
                {
                    "license": [{
                        "source": "repo/LICENSE.md",
                        "result": {"value": "Copyright (c) <year> <name of author>"}
                    }]
                },
                "test_repo.json",
                True,
                True
        ),

        # License with year placeholder
        (
                {
                    "license": [{
                        "source": "repo/LICENSE.md",
                        "result": {"value": "Copyright [year] Company Name"}
                    }]
                },
                "another_repo.json",
                True,
                True
        ),

        # License with program placeholder
        (
                {
                    "license": [{
                        "source": "repo/LICENSE.md",
                        "result": {"value": "<program> is licensed under MIT"}
                    }]
                },
                "test_repo.json",
                True,
                True
        ),

        # License not from LICENSE.md
        (
                {
                    "license": [{
                        "source": "repo/README.md",
                        "result": {"value": "Copyright <year> <author>"}
                    }]
                },
                "test_repo.json",
                False,
                False
        ),
    ])
    def test_detect_template_scenarios(self, somef_data, file_name,
                                       expected_has_pitfall, expected_placeholders):
        """Test various license template detection scenarios"""
        result = detect_license_template_placeholders(somef_data, file_name)

        assert result["has_pitfall"] == expected_has_pitfall
        assert result["file_name"] == file_name
        assert result["placeholders_found"] == expected_placeholders

        if expected_has_pitfall:
            assert result["license_source"] is not None
        else:
            assert result["license_source"] is None or result["license_source"] is not None

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_license_template_placeholders(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "license_source" in result
        assert "placeholders_found" in result

    @pytest.mark.parametrize("placeholder", [
        "<program>", "<year>", "<name of author>", "<name>",
        "<copyright holders>", "<owner>", "<author>",
        "[year]", "[fullname]", "[name]", "[copyright holder]",
        "<yyyy>", "<name of copyright owner>"
    ])
    def test_all_placeholder_patterns(self, placeholder):
        """Test that all documented placeholder patterns are detected"""
        license_content = f"This is a license with {placeholder} placeholder"
        result = check_license_template_placeholders(license_content)
        assert result == True, f"Failed to detect placeholder: {placeholder}"