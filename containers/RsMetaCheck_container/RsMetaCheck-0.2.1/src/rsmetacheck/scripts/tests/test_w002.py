import pytest
from datetime import datetime, timedelta
from rsmetacheck.scripts.warnings.w002 import (
    extract_github_api_date_updated,
    extract_codemeta_date_modified,
    normalize_date_for_comparison,
    calculate_date_difference_days,
    detect_outdated_datemodified
)


class TestExtractGithubApiDateUpdated:
    """Test suite for extract_github_api_date_updated function"""

    @pytest.mark.parametrize("somef_data,expected", [
        # No date_updated key
        ({}, None),
        ({"other_key": "value"}, None),

        # date_updated not a list
        ({"date_updated": "2024-01-01"}, None),
        ({"date_updated": {}}, None),

        # Empty date_updated list
        ({"date_updated": []}, None),

        # Date from GitHub API
        ({
             "date_updated": [{
                 "technique": "GitHub_API",
                 "result": {"value": "2025-02-05T18:00:24Z"}
             }]
         }, "2025-02-05T18:00:24Z"),

        # Multiple entries, only GitHub_API should match
        ({
             "date_updated": [
                 {"technique": "other_method", "result": {"value": "2024-01-01"}},
                 {"technique": "GitHub_API", "result": {"value": "2025-02-05T18:00:24Z"}}
             ]
         }, "2025-02-05T18:00:24Z"),

        # Missing result or value
        ({
             "date_updated": [{
                 "technique": "GitHub_API"
             }]
         }, None),
        ({
             "date_updated": [{
                 "technique": "GitHub_API",
                 "result": {}
             }]
         }, None),

        # Wrong technique
        ({
             "date_updated": [{
                 "technique": "code_parser",
                 "result": {"value": "2024-01-01"}
             }]
         }, None),
    ])
    def test_extract_github_date_scenarios(self, somef_data, expected):
        """Test various scenarios for GitHub API date extraction"""
        result = extract_github_api_date_updated(somef_data)
        assert result == expected


class TestExtractCodemetaDateModified:
    """Test suite for extract_codemeta_date_modified function"""

    @pytest.mark.parametrize("somef_data,expected", [
        # No date_updated key
        ({}, None),

        # Date from codemeta.json in source
        ({
             "date_updated": [{
                 "source": "repository/codemeta.json",
                 "result": {"value": "2023-11-17"}
             }]
         }, {"source": "repository/codemeta.json", "date": "2023-11-17"}),

        # Date from code_parser technique
        ({
             "date_updated": [{
                 "technique": "code_parser",
                 "result": {"value": "2024-05-20"}
             }]
         }, {"source": "codemeta.json (code_parser)", "date": "2024-05-20"}),

        # Multiple entries, codemeta should be found
        ({
             "date_updated": [
                 {"source": "README.md", "result": {"value": "2024-01-01"}},
                 {"source": "repository/codemeta.json", "result": {"value": "2023-11-17"}}
             ]
         }, {"source": "repository/codemeta.json", "date": "2023-11-17"}),

        # Missing result or value
        ({
             "date_updated": [{
                 "source": "repository/codemeta.json"
             }]
         }, None),

        # Non-codemeta source
        ({
             "date_updated": [{
                 "source": "repository/package.json",
                 "result": {"value": "2024-01-01"}
             }]
         }, None),
    ])
    def test_extract_codemeta_date_scenarios(self, somef_data, expected):
        """Test various scenarios for codemeta date extraction"""
        result = extract_codemeta_date_modified(somef_data)
        assert result == expected


class TestNormalizeDateForComparison:
    """Test suite for normalize_date_for_comparison function"""

    @pytest.mark.parametrize("date_string,expected_date", [
        # Standard ISO format with Z
        ("2025-02-05T18:00:24Z", datetime(2025, 2, 5, 18, 0, 24)),

        # ISO format with milliseconds
        ("2022-03-11T19:01:51.720Z", datetime(2022, 3, 11, 19, 1, 51, 720000)),

        # Date only
        ("2023-11-17", datetime(2023, 11, 17)),

        # ISO format without Z
        ("2024-05-20T10:30:00", datetime(2024, 5, 20, 10, 30, 0)),

        # With microseconds, no Z
        ("2024-01-15T14:22:33.123456", datetime(2024, 1, 15, 14, 22, 33, 123456)),

        # Partial date extraction
        ("2023-12-25T00:00:00+00:00", datetime(2023, 12, 25)),

        # Empty or None
        ("", None),
        (None, None),

        # Invalid format
        ("not-a-date", None),
        ("2024/01/01", None),

        # Whitespace
        ("  2023-11-17  ", datetime(2023, 11, 17)),
    ])
    def test_normalize_date_scenarios(self, date_string, expected_date):
        """Test various date format normalization scenarios"""
        result = normalize_date_for_comparison(date_string)
        assert result == expected_date


class TestCalculateDateDifferenceDays:
    """Test suite for calculate_date_difference_days function"""

    @pytest.mark.parametrize("date1,date2,expected_days", [
        # Same date
        (datetime(2024, 1, 1), datetime(2024, 1, 1), 0),

        # One day difference
        (datetime(2024, 1, 2), datetime(2024, 1, 1), 1),
        (datetime(2024, 1, 1), datetime(2024, 1, 2), 1),

        # One week difference
        (datetime(2024, 1, 8), datetime(2024, 1, 1), 7),

        # One month difference (approximately)
        (datetime(2024, 2, 1), datetime(2024, 1, 1), 31),

        # One year difference
        (datetime(2025, 1, 1), datetime(2024, 1, 1), 366),  # 2024 is leap year

        # Large difference
        (datetime(2025, 12, 31), datetime(2020, 1, 1), 2191),

        # Order doesn't matter (absolute value)
        (datetime(2024, 1, 1), datetime(2024, 1, 10), 9),
        (datetime(2024, 1, 10), datetime(2024, 1, 1), 9),
    ])
    def test_calculate_difference_scenarios(self, date1, date2, expected_days):
        """Test various date difference calculation scenarios"""
        result = calculate_date_difference_days(date1, date2)
        assert result == expected_days


class TestDetectOutdatedDatemodified:
    """Test suite for detect_outdated_datemodified function"""

    @pytest.mark.parametrize("somef_data,file_name,expected_has_warning,expected_diff_days", [
        # No data
        (
                {},
                "test_repo.json",
                False,
                0
        ),

        # Missing GitHub API date
        (
                {
                    "date_updated": [{
                        "source": "repository/codemeta.json",
                        "result": {"value": "2023-11-17"}
                    }]
                },
                "test_repo.json",
                False,
                0
        ),

        # Missing codemeta date
        (
                {
                    "date_updated": [{
                        "technique": "GitHub_API",
                        "result": {"value": "2025-02-05T18:00:24Z"}
                    }]
                },
                "test_repo.json",
                False,
                0
        ),

        # Dates match (no warning)
        (
                {
                    "date_updated": [
                        {"technique": "GitHub_API", "result": {"value": "2023-11-17T00:00:00Z"}},
                        {"source": "repository/codemeta.json", "result": {"value": "2023-11-17"}}
                    ]
                },
                "test_repo.json",
                False,
                0
        ),

        # GitHub date newer by 1 day (no warning, threshold is > 1)
        (
                {
                    "date_updated": [
                        {"technique": "GitHub_API", "result": {"value": "2023-11-18T00:00:00Z"}},
                        {"source": "repository/codemeta.json", "result": {"value": "2023-11-17"}}
                    ]
                },
                "test_repo.json",
                False,
                1
        ),

        # GitHub date newer by 10 days (warning)
        (
                {
                    "date_updated": [
                        {"technique": "GitHub_API", "result": {"value": "2023-11-27T00:00:00Z"}},
                        {"source": "repository/codemeta.json", "result": {"value": "2023-11-17"}}
                    ]
                },
                "test_repo.json",
                True,
                10
        ),

        # GitHub date newer by 80 days (warning)
        (
                {
                    "date_updated": [
                        {"technique": "GitHub_API", "result": {"value": "2025-02-05T18:00:24Z"}},
                        {"source": "repository/codemeta.json", "result": {"value": "2023-11-17"}}
                    ]
                },
                "test_repo.json",
                True,
                446
        ),

        # Codemeta date newer than GitHub (no warning)
        (
                {
                    "date_updated": [
                        {"technique": "GitHub_API", "result": {"value": "2023-11-17T00:00:00Z"}},
                        {"source": "repository/codemeta.json", "result": {"value": "2023-11-27"}}
                    ]
                },
                "test_repo.json",
                False,
                10
        ),
    ])
    def test_detect_outdated_scenarios(self, somef_data, file_name,
                                       expected_has_warning, expected_diff_days):
        """Test various outdated dateModified detection scenarios"""
        result = detect_outdated_datemodified(somef_data, file_name)

        assert result["has_warning"] == expected_has_warning
        assert result["file_name"] == file_name
        assert result["difference_days"] == expected_diff_days

        if expected_has_warning:
            assert result["github_api_date"] is not None
            assert result["codemeta_date"] is not None
            assert result["codemeta_source"] is not None

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_outdated_datemodified(somef_data, "test.json")

        assert "has_warning" in result
        assert "file_name" in result
        assert "github_api_date" in result
        assert "codemeta_date" in result
        assert "codemeta_source" in result
        assert "difference_days" in result
        assert "github_api_date_parsed" in result
        assert "codemeta_date_parsed" in result

    def test_parsed_dates_format(self):
        """Test that parsed dates are in ISO format"""
        somef_data = {
            "date_updated": [
                {"technique": "GitHub_API", "result": {"value": "2025-02-05T18:00:24Z"}},
                {"source": "repository/codemeta.json", "result": {"value": "2023-11-17"}}
            ]
        }

        result = detect_outdated_datemodified(somef_data, "test.json")

        if result["github_api_date_parsed"]:
            # Should be parseable as ISO format
            datetime.fromisoformat(result["github_api_date_parsed"])

        if result["codemeta_date_parsed"]:
            datetime.fromisoformat(result["codemeta_date_parsed"])

    @pytest.mark.parametrize("days_diff,should_warn", [
        (0, False),
        (1, False),
        (2, True),
        (7, True),
        (30, True),
        (365, True),
    ])
    def test_warning_threshold(self, days_diff, should_warn):
        """Test that warning threshold is correctly applied (> 1 day)"""
        github_date = "2024-01-10T00:00:00Z"
        codemeta_date_obj = datetime(2024, 1, 10) - timedelta(days=days_diff)
        codemeta_date = codemeta_date_obj.strftime("%Y-%m-%d")

        somef_data = {
            "date_updated": [
                {"technique": "GitHub_API", "result": {"value": github_date}},
                {"source": "repository/codemeta.json", "result": {"value": codemeta_date}}
            ]
        }

        result = detect_outdated_datemodified(somef_data, "test.json")
        assert result["has_warning"] == should_warn