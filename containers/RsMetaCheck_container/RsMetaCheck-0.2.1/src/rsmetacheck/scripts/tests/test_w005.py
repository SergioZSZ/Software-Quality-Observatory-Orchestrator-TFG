import pytest
from unittest.mock import patch
from rsmetacheck.scripts.warnings.w005 import (
    detect_multiple_requirements_in_string,
    detect_multiple_requirements_string_warning
)


class TestDetectMultipleRequirementsInString:
    """Test suite for detect_multiple_requirements_in_string function"""

    @pytest.mark.parametrize("requirement_string,expected_count", [
        # Empty or None
        ("", 0),
        (None, 0),

        # Not a string
        (123, 0),
        ([], 0),

        # Single requirement
        ("Python 3.9", 0),
        ("numpy>=1.20.0", 0),
        ("A single package", 0),

        # Multiple spaces (separator)
        ("numpy  pandas", 2),
        ("package1  package2  package3", 3),

        # Capital letter pattern
        ("Python NumPy Pandas", 3),
        ("Java Spring Maven", 3),

        # Whitespace handling
        ("  numpy  pandas  ", 2),

        # Complex cases
        ("Python3 NumPy SciPy", 3),
    ])
    def test_multiple_requirements_detection(self, requirement_string, expected_count):
        """Test detection of multiple requirements in string"""
        result = detect_multiple_requirements_in_string(requirement_string)
        assert len(result) == expected_count

    def test_returns_empty_list_for_single_requirement(self):
        """Test that single requirements return empty list"""
        single_reqs = [
            "Python 3.9",
            "numpy>=1.20.0",
            "django",
            "A single package name"
        ]

        for req in single_reqs:
            result = detect_multiple_requirements_in_string(req)
            assert result == []

    def test_multiple_spaces_separator(self):
        """Test detection using multiple spaces as separator"""
        test_string = "numpy  pandas  scipy"
        result = detect_multiple_requirements_in_string(test_string)

        assert len(result) == 3
        assert "numpy" in result
        assert "pandas" in result
        assert "scipy" in result

    def test_capital_letter_pattern(self):
        """Test detection using capital letter pattern"""
        test_string = "Python NumPy Pandas"
        result = detect_multiple_requirements_in_string(test_string)

        assert len(result) == 3
        assert "Python" in result
        assert "NumPy" in result
        assert "Pandas" in result

    def test_strips_whitespace_from_results(self):
        """Test that detected requirements are stripped of whitespace"""
        test_string = "  numpy  pandas  "
        result = detect_multiple_requirements_in_string(test_string)

        for req in result:
            assert req == req.strip()


class TestDetectMultipleRequirementsStringWarning:
    """Test suite for detect_multiple_requirements_string_warning function"""

    @pytest.mark.parametrize("somef_data,file_name,expected_has_warning,expected_count", [
        # No requirements key
        (
                {},
                "test_repo.json",
                False,
                0
        ),

        # requirements not a list
        (
                {"requirements": "numpy pandas"},
                "test_repo.json",
                False,
                0
        ),

        # Empty requirements list
        (
                {"requirements": []},
                "test_repo.json",
                False,
                0
        ),

        # Single requirement (no warning)
        (
                {
                    "requirements": [{
                        "technique": "codemeta.json",
                        "source": "repository/codemeta.json",
                        "result": {"value": "Python 3.9"}
                    }]
                },
                "test_repo.json",
                False,
                0
        ),

        # Multiple requirements in single string (warning)
        (
                {
                    "requirements": [{
                        "technique": "codemeta.json",
                        "source": "repository/codemeta.json",
                        "result": {"value": "numpy  pandas  scipy"}
                    }]
                },
                "test_repo.json",
                True,
                3
        ),

        # Multiple requirements with capital letters (warning)
        (
                {
                    "requirements": [{
                        "source": "repository/setup.py",
                        "result": {"value": "Python NumPy Pandas"}
                    }]
                },
                "test_repo.json",
                True,
                3
        ),

        # List with single element containing multiple (warning)
        (
                {
                    "requirements": [{
                        "technique": "pom.xml",
                        "source": "repository/pom.xml",
                        "result": {"value": ["numpy  pandas"]}
                    }]
                },
                "test_repo.json",
                True,
                2
        ),

        # List with multiple elements (no warning - properly structured)
        (
                {
                    "requirements": [{
                        "technique": "codemeta.json",
                        "source": "repository/codemeta.json",
                        "result": {"value": ["numpy", "pandas"]}
                    }]
                },
                "test_repo.json",
                False,
                0
        ),
    ])
    def test_detect_warning_scenarios(self, somef_data, file_name,
                                      expected_has_warning, expected_count):
        """Test various multiple requirements string detection scenarios"""
        with patch('metacheck.scripts.warnings.w005.extract_metadata_source_filename', return_value="test_file"):
            result = detect_multiple_requirements_string_warning(somef_data, file_name)

            assert result["has_warning"] == expected_has_warning
            assert result["file_name"] == file_name
            assert result["count_detected"] == expected_count

            if expected_has_warning:
                assert result["requirement_string"] is not None
                assert len(result["detected_requirements"]) == expected_count

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_multiple_requirements_string_warning(somef_data, "test.json")

        assert "has_warning" in result
        assert "file_name" in result
        assert "requirement_string" in result
        assert "detected_requirements" in result
        assert "source" in result
        assert "metadata_source_file" in result
        assert "count_detected" in result

    @pytest.mark.parametrize("source", [
        "repository/codemeta.json",
        "repository/setup.py",
        "repository/pom.xml",
    ])
    def test_specific_metadata_sources(self, source):
        """Test that specific metadata sources are detected"""
        somef_data = {
            "requirements": [{
                "source": source,
                "result": {"value": "numpy  pandas"}
            }]
        }

        with patch('metacheck.scripts.warnings.w005.extract_metadata_source_filename', return_value=source.split('/')[-1]):
            result = detect_multiple_requirements_string_warning(somef_data, "test.json")
            assert result["has_warning"] == True

    def test_technique_matching(self):
        """Test that technique field is also used for matching"""
        somef_data = {
            "requirements": [{
                "technique": "codemeta.json",
                "source": "",
                "result": {"value": "Python NumPy"}
            }]
        }

        with patch('metacheck.scripts.warnings.w005.extract_metadata_source_filename', return_value=""):
            result = detect_multiple_requirements_string_warning(somef_data, "test.json")
            assert result["has_warning"] == True

    def test_stops_at_first_warning(self):
        """Test that detection stops at first warning found"""
        somef_data = {
            "requirements": [
                {
                    "technique": "codemeta.json",
                    "source": "repository/codemeta.json",
                    "result": {"value": "numpy  pandas"}
                },
                {
                    "technique": "codemeta.json",
                    "source": "repository/codemeta.json",
                    "result": {"value": "scipy  matplotlib"}
                }
            ]
        }

        with patch('metacheck.scripts.warnings.w005.extract_metadata_source_filename', return_value="codemeta.json"):
            result = detect_multiple_requirements_string_warning(somef_data, "test.json")
            assert result["has_warning"] == True
            assert "numpy" in result["detected_requirements"]

    def test_source_fallback_to_technique(self):
        """Test that source falls back to technique when source is empty"""
        somef_data = {
            "requirements": [{
                "technique": "setup.py",
                "source": "",
                "result": {"value": "numpy  pandas"}
            }]
        }

        with patch('metacheck.scripts.warnings.w005.extract_metadata_source_filename', return_value=""):
            result = detect_multiple_requirements_string_warning(somef_data, "test.json")
            assert result["has_warning"] == True
            assert "technique: setup.py" in result["source"]

    def test_non_string_value_types(self):
        """Test handling of non-string value types"""
        # Dict value
        somef_data1 = {
            "requirements": [{
                "technique": "codemeta.json",
                "source": "repository/codemeta.json",
                "result": {"value": {"packages": "numpy pandas"}}
            }]
        }

        with patch('metacheck.scripts.warnings.w005.extract_metadata_source_filename', return_value="codemeta.json"):
            result1 = detect_multiple_requirements_string_warning(somef_data1, "test.json")
            # Dict is not handled as multiple requirements
            assert result1["has_warning"] == False

        # Integer value
        somef_data2 = {
            "requirements": [{
                "technique": "codemeta.json",
                "source": "repository/codemeta.json",
                "result": {"value": 123}
            }]
        }

        with patch('metacheck.scripts.warnings.w005.extract_metadata_source_filename', return_value="codemeta.json"):
            result2 = detect_multiple_requirements_string_warning(somef_data2, "test.json")
            assert result2["has_warning"] == False

    def test_list_with_multiple_elements(self):
        """Test that properly structured lists don't trigger warning"""
        somef_data = {
            "requirements": [{
                "technique": "codemeta.json",
                "source": "repository/codemeta.json",
                "result": {"value": ["numpy", "pandas", "scipy"]}
            }]
        }

        with patch('metacheck.scripts.warnings.w005.extract_metadata_source_filename', return_value="codemeta.json"):
            result = detect_multiple_requirements_string_warning(somef_data, "test.json")
            # Multiple elements in list is correct format, no warning
            assert result["has_warning"] == False

    def test_list_with_single_concatenated_element(self):
        """Test that list with single concatenated element triggers warning"""
        somef_data = {
            "requirements": [{
                "technique": "codemeta.json",
                "source": "repository/codemeta.json",
                "result": {"value": ["numpy  pandas  scipy"]}
            }]
        }

        with patch('metacheck.scripts.warnings.w005.extract_metadata_source_filename', return_value="codemeta.json"):
            result = detect_multiple_requirements_string_warning(somef_data, "test.json")
            assert result["has_warning"] == True
            assert result["count_detected"] == 3

    @pytest.mark.parametrize("req_string,expected_reqs", [
        ("numpy  pandas", ["numpy", "pandas"]),
        ("Python NumPy SciPy", ["Python", "NumPy", "SciPy"]),
        ("package1  package2  package3", ["package1", "package2", "package3"]),
    ])
    def test_detected_requirements_content(self, req_string, expected_reqs):
        """Test that detected requirements contain expected packages"""
        somef_data = {
            "requirements": [{
                "technique": "codemeta.json",
                "source": "repository/codemeta.json",
                "result": {"value": req_string}
            }]
        }

        with patch('metacheck.scripts.warnings.w005.extract_metadata_source_filename', return_value="codemeta.json"):
            result = detect_multiple_requirements_string_warning(somef_data, "test.json")
            assert result["has_warning"] == True
            for expected_req in expected_reqs:
                assert expected_req in result["detected_requirements"]