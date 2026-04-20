import pytest
from unittest.mock import patch
from rsmetacheck.scripts.warnings.w001 import (
    extract_requirements_from_metadata,
    check_requirement_has_version,
    analyze_requirements_versions,
    detect_unversioned_requirements
)


class TestExtractRequirementsFromMetadata:
    """Test suite for extract_requirements_from_metadata function"""

    @pytest.mark.parametrize("somef_data,expected", [
        # No requirements key
        ({}, None),
        ({"other_key": "value"}, None),

        # Requirements not a list
        ({"requirements": "numpy"}, None),
        ({"requirements": {}}, None),

        # Empty requirements list
        ({"requirements": []}, None),

        # Requirements from codemeta.json
        ({
             "requirements": [{
                 "source": "repository/codemeta.json",
                 "result": {"name": "numpy", "version": "1.20.0"}
             }]
         }, {"source": "repository/codemeta.json", "requirement": {"name": "numpy", "version": "1.20.0"}}),

        # Requirements from package.json
        ({
             "requirements": [{
                 "source": "repository/package.json",
                 "result": [
                     {"name": "express", "version": "^4.17.1"},
                     {"name": "react"}
                 ]
             }]
         }, {"source": "repository/package.json",
             "requirement": [{"name": "express", "version": "^4.17.1"}, {"name": "react"}]}),

        # Requirements from requirements.txt
        ({
             "requirements": [{
                 "source": "repository/requirements.txt",
                 "result": {"value": "numpy==1.20.0"}
             }]
         }, {"source": "repository/requirements.txt", "requirement": {"value": "numpy==1.20.0"}}),

        # Non-metadata source (should not match)
        ({
             "requirements": [{
                 "source": "README.md",
                 "result": {"name": "numpy"}
             }]
         }, None),

        # Multiple entries, first non-metadata
        ({
             "requirements": [
                 {"source": "README.md", "result": {"name": "lib1"}},
                 {"source": "repository/setup.py", "result": {"name": "lib2"}}
             ]
         }, {"source": "repository/setup.py", "requirement": {"name": "lib2"}}),
    ])
    def test_extract_requirements_scenarios(self, somef_data, expected):
        """Test various scenarios for requirements extraction"""
        result = extract_requirements_from_metadata(somef_data)
        assert result == expected


class TestCheckRequirementHasVersion:
    """Test suite for check_requirement_has_version function"""

    @pytest.mark.parametrize("requirement,expected", [
        # Has version field with value
        ({"name": "numpy", "version": "1.20.0"}, True),
        ({"name": "pandas", "version": ">=1.0.0"}, True),
        ({"version": "2.5.1"}, True),

        # Has version field but empty
        ({"name": "numpy", "version": ""}, False),
        ({"name": "numpy", "version": "   "}, False),

        # No version field but has operators in value
        ({"value": "numpy==1.20.0"}, True),
        ({"value": "pandas>=1.0.0"}, True),
        ({"value": "requests<=2.25.0"}, True),
        ({"value": "flask>1.0"}, True),
        ({"value": "django<3.0"}, True),
        ({"value": "pytest~=6.0"}, True),
        ({"value": "black!=20.8b1"}, True),
        ({"value": "fastapi^0.65.0"}, True),
        ({"value": "uvicorn~0.13.0"}, True),

        # No version information
        ({"name": "numpy"}, False),
        ({"value": "pandas"}, False),
        ({"name": "requests", "description": "HTTP library"}, False),

        # Empty or missing fields
        ({}, False),
        ({"name": ""}, False),
        ({"value": ""}, False),
    ])
    def test_version_detection_scenarios(self, requirement, expected):
        """Test various scenarios for version detection in requirements"""
        result = check_requirement_has_version(requirement)
        assert result == expected


class TestAnalyzeRequirementsVersions:
    """Test suite for analyze_requirements_versions function"""

    @pytest.mark.parametrize("requirements_data,expected_total,expected_unversioned,expected_names", [
        # Single requirement with version
        (
                {"requirement": {"name": "numpy", "version": "1.20.0"}},
                1, 0, []
        ),

        # Single requirement without version
        (
                {"requirement": {"name": "pandas"}},
                1, 1, ["pandas"]
        ),

        # Multiple requirements, all versioned
        (
                {"requirement": [
                    {"name": "numpy", "version": "1.20.0"},
                    {"value": "pandas>=1.0.0"},
                    {"value": "requests==2.25.0"}
                ]},
                3, 0, []
        ),

        # Multiple requirements, some unversioned
        (
                {"requirement": [
                    {"name": "numpy", "version": "1.20.0"},
                    {"name": "pandas"},
                    {"value": "requests"}
                ]},
                3, 2, ["pandas", "requests"]
        ),

        # All requirements unversioned
        (
                {"requirement": [
                    {"name": "numpy"},
                    {"name": "pandas"},
                    {"value": "requests"}
                ]},
                3, 3, ["numpy", "pandas", "requests"]
        ),

        # Empty requirements list
        (
                {"requirement": []},
                0, 0, []
        ),

        # Mixed formats with value field
        (
                {"requirement": [
                    {"value": "numpy==1.20.0"},
                    {"value": "pandas"},
                    {"name": "requests", "version": "2.25.0"}
                ]},
                3, 1, ["pandas"]
        ),

        # Requirements with unknown names
        (
                {"requirement": [
                    {"version": "1.0.0"},
                    {}
                ]},
                2, 1, ["unknown"]
        ),

        # Invalid requirement data
        (
                {"requirement": "not a dict or list"},
                0, 0, []
        ),
    ])
    def test_analyze_requirements_scenarios(self, requirements_data, expected_total,
                                            expected_unversioned, expected_names):
        """Test various scenarios for analyzing requirements versions"""
        total, unversioned, names = analyze_requirements_versions(requirements_data)

        assert total == expected_total
        assert unversioned == expected_unversioned
        assert names == expected_names


class TestDetectUnversionedRequirements:
    """Test suite for detect_unversioned_requirements function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_warning,expected_total,expected_unversioned,expected_percentage", [
            # No requirements data
            (
                    {},
                    "test_repo.json",
                    False,
                    0,
                    0,
                    0.0
            ),

            # All requirements versioned
            (
                    {
                        "requirements": [{
                            "source": "repository/requirements.txt",
                            "result": [
                                {"value": "numpy==1.20.0"},
                                {"value": "pandas>=1.0.0"}
                            ]
                        }]
                    },
                    "test_repo.json",
                    False,
                    2,
                    0,
                    0.0
            ),

            # Some requirements unversioned (50%)
            (
                    {
                        "requirements": [{
                            "source": "repository/package.json",
                            "result": [
                                {"name": "express", "version": "^4.17.1"},
                                {"name": "react"}
                            ]
                        }]
                    },
                    "test_repo.json",
                    True,
                    2,
                    1,
                    50.0
            ),

            # All requirements unversioned (100%)
            (
                    {
                        "requirements": [{
                            "source": "repository/setup.py",
                            "result": [
                                {"name": "numpy"},
                                {"name": "pandas"},
                                {"name": "requests"}
                            ]
                        }]
                    },
                    "test_repo.json",
                    True,
                    3,
                    3,
                    100.0
            ),

            # One unversioned out of three (33.33%)
            (
                    {
                        "requirements": [{
                            "source": "repository/pyproject.toml",
                            "result": [
                                {"name": "lib1", "version": "1.0.0"},
                                {"name": "lib2", "version": "2.0.0"},
                                {"name": "lib3"}
                            ]
                        }]
                    },
                    "test_repo.json",
                    True,
                    3,
                    1,
                    33.33
            ),
        ])
    def test_detect_unversioned_scenarios(self, somef_data, file_name, expected_has_warning,
                                          expected_total, expected_unversioned, expected_percentage):
        """Test various unversioned requirements detection scenarios"""
        with patch('metacheck.scripts.warnings.w001.extract_metadata_source_filename', return_value="test_file"):
            result = detect_unversioned_requirements(somef_data, file_name)

            assert result["has_warning"] == expected_has_warning
            assert result["file_name"] == file_name
            assert result["total_requirements"] == expected_total
            assert result["unversioned_count"] == expected_unversioned
            assert result["percentage_unversioned"] == expected_percentage

            if expected_has_warning:
                assert len(result["unversioned_requirements"]) == expected_unversioned
                assert result["metadata_source"] is not None

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_unversioned_requirements(somef_data, "test.json")

        assert "has_warning" in result
        assert "file_name" in result
        assert "metadata_source" in result
        assert "metadata_source_file" in result
        assert "total_requirements" in result
        assert "unversioned_count" in result
        assert "unversioned_requirements" in result
        assert "percentage_unversioned" in result

    @pytest.mark.parametrize("metadata_file", [
        "codemeta.json", "DESCRIPTION", "composer.json",
        "package.json", "pom.xml", "pyproject.toml",
        "requirements.txt", "setup.py"
    ])
    def test_all_metadata_sources(self, metadata_file):
        """Test that all metadata file types are correctly processed"""
        somef_data = {
            "requirements": [{
                "source": f"repository/{metadata_file}",
                "result": {"name": "lib1"}
            }]
        }

        with patch('metacheck.scripts.warnings.w001.extract_metadata_source_filename', return_value=metadata_file):
            result = detect_unversioned_requirements(somef_data, "test.json")
            assert result["total_requirements"] > 0

    @pytest.mark.parametrize("operator", ["==", ">=", "<=", ">", "<", "~=", "!=", "^", "~"])
    def test_all_version_operators(self, operator):
        """Test that all version operators are recognized"""
        requirement = {"value": f"package{operator}1.0.0"}
        result = check_requirement_has_version(requirement)
        assert result == True, f"Failed to detect operator: {operator}"

    def test_percentage_calculation(self):
        """Test percentage calculation accuracy"""
        test_cases = [
            (3, 1, 33.33),
            (4, 1, 25.0),
            (3, 2, 66.67),
            (10, 7, 70.0),
        ]

        for total, unversioned, expected_pct in test_cases:
            somef_data = {
                "requirements": [{
                    "source": "repository/requirements.txt",
                    "result": [{"name": f"lib{i}", "version": "1.0" if i >= unversioned else None}
                               for i in range(total)]
                }]
            }

            with patch('metacheck.scripts.warnings.w001.extract_metadata_source_filename', return_value="test_file"):
                result = detect_unversioned_requirements(somef_data, "test.json")
                assert result["percentage_unversioned"] == expected_pct