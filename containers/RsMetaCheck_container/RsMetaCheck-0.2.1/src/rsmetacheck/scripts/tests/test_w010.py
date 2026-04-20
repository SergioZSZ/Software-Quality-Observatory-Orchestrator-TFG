import pytest
from unittest.mock import patch
from rsmetacheck.scripts.warnings.w010 import (
    is_git_remote_shorthand,
    detect_git_remote_shorthand_pitfall
)


class TestIsGitRemoteShorthand:
    """Test suite for is_git_remote_shorthand helper function"""

    @pytest.mark.parametrize("url,expected", [
        # Valid Git remote shorthand patterns
        ("github.com:user/repo.git", True),
        ("github.com:user/repo", True),
        ("gitlab.com:group/project.git", True),
        ("bitbucket.org:team/repository", True),
        ("git.example.com:user/project.git", True),
        ("server.com:path/to/repo", True),

        # With hyphens and dots in hostname
        ("git-server.com:user/repo.git", True),
        ("my.git.server.com:project.git", True),

        # With underscores and dots in path
        ("github.com:user/my_repo.git", True),
        ("github.com:org/repo.name.git", True),
        ("github.com:user/repo-name", True),

        # Full HTTP/HTTPS URLs (should return False)
        ("https://github.com/user/repo.git", False),
        ("http://gitlab.com/user/project.git", False),
        ("https://github.com/user/repo", False),

        # Invalid patterns
        ("not-a-url", False),
        ("just-text", False),
        ("user@host:repo", False),  # SSH format but with @
        ("github.com/user/repo", False),  # Missing colon
        (":invalid", False),
        ("github.com:", False),

        # Empty or None
        ("", False),
        ("   ", False),
        (None, False),

        # Edge cases
        ("a:b", True),  # Minimal valid pattern
        ("host.com:path", True),
        ("HOST.COM:PATH.GIT", True),  # Uppercase

        # With numbers
        ("git123.com:user/repo123.git", True),
        ("github.com:user123/repo456", True),

        # Multiple levels in path
        ("github.com:org/team/project.git", True),
        ("gitlab.com:group/subgroup/repo", True),
    ])
    def test_is_git_remote_shorthand_scenarios(self, url, expected):
        """Test various Git remote shorthand detection scenarios"""
        result = is_git_remote_shorthand(url)
        assert result == expected, f"Failed for URL: {url}"

    def test_is_git_remote_shorthand_with_non_string(self):
        """Test is_git_remote_shorthand with non-string inputs"""
        assert is_git_remote_shorthand(123) is False
        assert is_git_remote_shorthand([]) is False
        assert is_git_remote_shorthand({}) is False
        assert is_git_remote_shorthand(None) is False

    def test_is_git_remote_shorthand_whitespace_handling(self):
        """Test that whitespace is properly stripped"""
        assert is_git_remote_shorthand("  github.com:user/repo.git  ") is True
        assert is_git_remote_shorthand("\tgitlab.com:user/project\n") is True

    def test_http_https_prefix_rejection(self):
        """Test that URLs with http/https prefix are rejected"""
        urls_with_prefix = [
            "http://github.com:user/repo.git",
            "https://gitlab.com:project.git",
            "HTTP://example.com:path",
            "HTTPS://server.com:repo",
        ]

        for url in urls_with_prefix:
            assert is_git_remote_shorthand(url) is False, f"Should reject: {url}"


class TestDetectGitRemoteShorthandPitfall:
    """Test suite for detect_git_remote_shorthand_pitfall function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_warning,expected_url,expected_source_file", [
            # No code_repository key
            (
                    {},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # code_repository not a list
            (
                    {"code_repository": "github.com:user/repo"},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),
            (
                    {"code_repository": {}},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Empty code_repository list
            (
                    {"code_repository": []},
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Valid HTTPS URL from codemeta.json (no pitfall)
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/codemeta.json",
                            "result": {"value": "https://github.com/user/repo.git"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Git shorthand from codemeta.json (has pitfall)
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/codemeta.json",
                            "result": {"value": "github.com:user/repo.git"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "github.com:user/repo.git",
                    "codemeta.json"
            ),

            # Git shorthand without .git extension
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/package.json",
                            "result": {"value": "gitlab.com:user/project"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "gitlab.com:user/project",
                    "package.json"
            ),

            # Non-metadata source with shorthand (should not trigger)
            (
                    {
                        "code_repository": [{
                            "technique": "github_api",
                            "source": "README.md",
                            "result": {"value": "github.com:user/repo.git"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Metadata source from setup.py
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/setup.py",
                            "result": {"value": "bitbucket.org:team/repo.git"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "bitbucket.org:team/repo.git",
                    "setup.py"
            ),

            # Multiple entries, first valid, second with shorthand
            (
                    {
                        "code_repository": [
                            {
                                "technique": "github_api",
                                "source": "GitHub API",
                                "result": {"value": "https://github.com/user/repo"}
                            },
                            {
                                "technique": "code_parser",
                                "source": "repository/pyproject.toml",
                                "result": {"value": "github.com:user/repo"}
                            }
                        ]
                    },
                    "test_repo.json",
                    True,
                    "github.com:user/repo",
                    "pyproject.toml"
            ),

            # Missing result key
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/codemeta.json"
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
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/codemeta.json",
                            "result": {}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Empty source string
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "",
                            "result": {"value": "github.com:user/repo.git"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "github.com:user/repo.git",
                    None
            ),

            # pom.xml metadata source
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/pom.xml",
                            "result": {"value": "gitlab.com:group/project.git"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "gitlab.com:group/project.git",
                    "pom.xml"
            ),

            # composer.json metadata source
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/composer.json",
                            "result": {"value": "git.example.com:vendor/package"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "git.example.com:vendor/package",
                    "composer.json"
            ),

            # DESCRIPTION metadata source (R package)
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/DESCRIPTION",
                            "result": {"value": "github.com:user/rpackage.git"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "github.com:user/rpackage.git",
                    "DESCRIPTION"
            ),

            # requirements.txt metadata source
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/requirements.txt",
                            "result": {"value": "github.com:org/lib.git"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "github.com:org/lib.git",
                    "requirements.txt"
            ),
        ])
    def test_detect_git_shorthand_scenarios(self, somef_data, file_name,
                                            expected_has_warning, expected_url,
                                            expected_source_file):
        """Test various scenarios for Git remote shorthand detection"""
        with patch('metacheck.scripts.warnings.w010.extract_metadata_source_filename',
                   return_value=expected_source_file):
            result = detect_git_remote_shorthand_pitfall(somef_data, file_name)

            assert result["has_warning"] == expected_has_warning
            assert result["file_name"] == file_name
            assert result["repository_url"] == expected_url
            assert result["is_shorthand"] == expected_has_warning

            if expected_has_warning:
                assert result["metadata_source_file"] == expected_source_file

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_git_remote_shorthand_pitfall(somef_data, "test.json")

        assert "has_warning" in result
        assert "file_name" in result
        assert "repository_url" in result
        assert "source" in result
        assert "metadata_source_file" in result
        assert "is_shorthand" in result

    @pytest.mark.parametrize("metadata_file", [
        "codemeta.json", "DESCRIPTION", "composer.json",
        "package.json", "pom.xml", "pyproject.toml",
        "requirements.txt", "setup.py"
    ])
    def test_all_metadata_sources(self, metadata_file):
        """Test that all metadata file types are correctly processed"""
        somef_data = {
            "code_repository": [{
                "technique": "code_parser",
                "source": f"repository/{metadata_file}",
                "result": {"value": "github.com:user/repo.git"}
            }]
        }

        with patch('metacheck.scripts.warnings.w010.extract_metadata_source_filename',
                   return_value=metadata_file):
            result = detect_git_remote_shorthand_pitfall(somef_data, "test.json")
            assert result["has_warning"] is True
            assert result["metadata_source_file"] == metadata_file

    def test_stops_at_first_match(self):
        """Test that function returns after finding first shorthand"""
        somef_data = {
            "code_repository": [
                {
                    "technique": "code_parser",
                    "source": "repository/codemeta.json",
                    "result": {"value": "github.com:user/repo1.git"}
                },
                {
                    "technique": "code_parser",
                    "source": "repository/package.json",
                    "result": {"value": "gitlab.com:user/repo2.git"}
                }
            ]
        }

        with patch('metacheck.scripts.warnings.w010.extract_metadata_source_filename',
                   side_effect=["codemeta.json", "package.json"]):
            result = detect_git_remote_shorthand_pitfall(somef_data, "test.json")

            assert result["has_warning"] is True
            assert result["repository_url"] == "github.com:user/repo1.git"

    @pytest.mark.parametrize("shorthand_url", [
        "github.com:user/repo.git",
        "gitlab.com:group/project",
        "bitbucket.org:team/repository.git",
        "git.server.com:path/to/repo",
        "example.com:vendor/package.git",
    ])
    def test_various_shorthand_formats(self, shorthand_url):
        """Test detection of various shorthand URL formats"""
        somef_data = {
            "code_repository": [{
                "technique": "code_parser",
                "source": "repository/codemeta.json",
                "result": {"value": shorthand_url}
            }]
        }

        with patch('metacheck.scripts.warnings.w010.extract_metadata_source_filename',
                   return_value="codemeta.json"):
            result = detect_git_remote_shorthand_pitfall(somef_data, "test.json")
            assert result["has_warning"] is True
            assert result["repository_url"] == shorthand_url

    def test_missing_technique_field(self):
        """Test handling of missing technique field"""
        somef_data = {
            "code_repository": [{
                "source": "repository/codemeta.json",
                "result": {"value": "github.com:user/repo.git"}
            }]
        }

        with patch('metacheck.scripts.warnings.w010.extract_metadata_source_filename',
                   return_value="codemeta.json"):
            result = detect_git_remote_shorthand_pitfall(somef_data, "test.json")
            # Should still detect based on source matching
            assert result["has_warning"] is True