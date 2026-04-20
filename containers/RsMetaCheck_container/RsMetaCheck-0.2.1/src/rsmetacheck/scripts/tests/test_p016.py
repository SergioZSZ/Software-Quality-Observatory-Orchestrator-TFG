import pytest
from rsmetacheck.scripts.pitfalls.p016 import (
    detect_different_repository_pitfall,
    normalize_repository_url
)


class TestNormalizeRepositoryUrl:
    """Test suite for normalize_repository_url function"""

    @pytest.mark.parametrize("url,expected", [
        # Basic normalization
        ("https://github.com/user/repo", "https://github.com/user/repo"),
        ("https://github.com/user/repo.git", "https://github.com/user/repo"),
        ("https://github.com/user/repo/", "https://github.com/user/repo"),
        ("https://github.com/user/repo.git/", "https://github.com/user/repo"),

        # Git+ prefix removal
        ("git+https://github.com/user/repo", "https://github.com/user/repo"),
        ("git+https://github.com/user/repo.git", "https://github.com/user/repo"),

        # SSH to HTTPS conversion
        ("git@github.com:user/repo", "https://github.com/user/repo"),
        ("git@github.com:user/repo.git", "https://github.com/user/repo"),
        ("git@gitlab.com:user/repo", "https://gitlab.com/user/repo"),

        # Case normalization
        ("HTTPS://GITHUB.COM/USER/REPO", "https://github.com/user/repo"),
        ("Git@GitHub.com:User/Repo", "https://github.com/user/repo"),

        # Empty/None handling
        ("", ""),
        (None, ""),

        # HTTP vs HTTPS (should be different after normalization)
        ("http://github.com/user/repo", "http://github.com/user/repo"),
        ("https://github.com/user/repo", "https://github.com/user/repo"),
    ])
    def test_url_normalization(self, url, expected):
        """Test various URL normalization scenarios"""
        assert normalize_repository_url(url) == expected


class TestDetectDifferentRepositoryPitfall:
    """Test suite for detect_different_repository_pitfall function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_pitfall,expected_github_url,expected_different_count", [
            # No code_repository key
            (
                    {},
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # code_repository not a list
            (
                    {"code_repository": "https://github.com/user/repo"},
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # Empty code_repository list
            (
                    {"code_repository": []},
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # Matching repositories (no pitfall)
            (
                    {
                        "code_repository": [
                            {
                                "source": "GitHub_API",
                                "technique": "GitHub_API",
                                "result": {"value": "https://github.com/user/repo"}
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "https://github.com/user/repo"}
                            }
                        ]
                    },
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # Matching after normalization (no pitfall)
            (
                    {
                        "code_repository": [
                            {
                                "source": "GitHub_API",
                                "technique": "GitHub_API",
                                "result": {"value": "https://github.com/user/repo"}
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "https://github.com/user/repo.git"}
                            }
                        ]
                    },
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # Different repositories (pitfall)
            (
                    {
                        "code_repository": [
                            {
                                "source": "GitHub_API",
                                "technique": "GitHub_API",
                                "result": {"value": "https://github.com/user/repo1"}
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "https://github.com/user/repo2"}
                            }
                        ]
                    },
                    "test_repo.json",
                    True,
                    "https://github.com/user/repo1",
                    1
            ),

            # Only GitHub API (no pitfall)
            (
                    {
                        "code_repository": [
                            {
                                "source": "GitHub_API",
                                "technique": "GitHub_API",
                                "result": {"value": "https://github.com/user/repo"}
                            }
                        ]
                    },
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # Only codemeta (no pitfall)
            (
                    {
                        "code_repository": [
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "https://github.com/user/repo"}
                            }
                        ]
                    },
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # Missing result key
            (
                    {
                        "code_repository": [
                            {
                                "source": "GitHub_API",
                                "technique": "GitHub_API"
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser"
                            }
                        ]
                    },
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # Missing value in result
            (
                    {
                        "code_repository": [
                            {
                                "source": "GitHub_API",
                                "technique": "GitHub_API",
                                "result": {}
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {}
                            }
                        ]
                    },
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # SSH vs HTTPS (should match after normalization)
            (
                    {
                        "code_repository": [
                            {
                                "source": "GitHub_API",
                                "technique": "GitHub_API",
                                "result": {"value": "https://github.com/user/repo"}
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "git@github.com:user/repo"}
                            }
                        ]
                    },
                    "test_repo.json",
                    False,
                    None,
                    0
            ),

            # Multiple metadata sources with different URLs
            (
                    {
                        "code_repository": [
                            {
                                "source": "GitHub_API",
                                "technique": "GitHub_API",
                                "result": {"value": "https://github.com/user/repo1"}
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "https://github.com/user/repo2"}
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "https://github.com/user/repo3"}
                            }
                        ]
                    },
                    "test_repo.json",
                    True,
                    "https://github.com/user/repo1",
                    2
            ),
        ])
    def test_detect_different_repository_scenarios(self, somef_data, file_name,
                                                   expected_has_pitfall, expected_github_url,
                                                   expected_different_count):
        """Test various scenarios for different repository detection"""
        result = detect_different_repository_pitfall(somef_data, file_name)

        assert result["has_pitfall"] == expected_has_pitfall
        assert result["file_name"] == file_name
        assert result["github_api_url"] == expected_github_url

        if expected_has_pitfall:
            assert len(result["different_urls"]) == expected_different_count

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_different_repository_pitfall(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "github_api_url" in result
        assert "metadata_urls" in result
        assert "different_urls" in result

    def test_case_insensitive_matching(self):
        """Test that URL matching is case insensitive"""
        somef_data = {
            "code_repository": [
                {
                    "source": "GitHub_API",
                    "technique": "GitHub_API",
                    "result": {"value": "https://github.com/user/repo"}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "HTTPS://GITHUB.COM/USER/REPO"}
                }
            ]
        }

        result = detect_different_repository_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is False

    def test_git_prefix_normalization(self):
        """Test that git+ prefix is properly normalized"""
        somef_data = {
            "code_repository": [
                {
                    "source": "GitHub_API",
                    "technique": "GitHub_API",
                    "result": {"value": "https://github.com/user/repo"}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "git+https://github.com/user/repo"}
                }
            ]
        }

        result = detect_different_repository_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is False


    def test_codemeta_lowercase_source_detection(self):
        """Test detection with lowercase codemeta in source"""
        somef_data = {
            "code_repository": [
                {
                    "source": "GitHub_API",
                    "technique": "GitHub_API",
                    "result": {"value": "https://github.com/user/repo1"}
                },
                {
                    "source": "repository/CODEMETA.JSON",
                    "technique": "code_parser",
                    "result": {"value": "https://github.com/user/repo2"}
                }
            ]
        }

        result = detect_different_repository_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True

    def test_non_codemeta_metadata_ignored(self):
        """Test that non-codemeta metadata sources are ignored"""
        somef_data = {
            "code_repository": [
                {
                    "source": "GitHub_API",
                    "technique": "GitHub_API",
                    "result": {"value": "https://github.com/user/repo1"}
                },
                {
                    "source": "repository/package.json",
                    "technique": "code_parser",
                    "result": {"value": "https://github.com/user/repo2"}
                }
            ]
        }

        result = detect_different_repository_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is False

    def test_different_hosts(self):
        """Test that different hosts are detected as different"""
        somef_data = {
            "code_repository": [
                {
                    "source": "GitHub_API",
                    "technique": "GitHub_API",
                    "result": {"value": "https://github.com/user/repo"}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "https://gitlab.com/user/repo"}
                }
            ]
        }

        result = detect_different_repository_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True