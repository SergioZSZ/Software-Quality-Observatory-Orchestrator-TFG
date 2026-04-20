import pytest
from unittest.mock import patch
from rsmetacheck.scripts.pitfalls.p009 import (
    is_repository_url,
    is_homepage_url_repo,
    detect_coderepository_homepage_pitfall
)


class TestIsRepositoryUrl:
    """Test suite for is_repository_url helper function"""

    @pytest.mark.parametrize("url,expected", [
        # Valid repository URLs
        ("https://github.com/user/repo", True),
        ("https://gitlab.com/user/project", True),
        ("https://bitbucket.org/team/repo", True),
        ("https://sourceforge.net/projects/myproject", True),
        ("https://git.example.com/repo", True),
        ("https://example.com/repo.git", True),

        # Case insensitive
        ("HTTPS://GITHUB.COM/USER/REPO", True),
        ("https://GitLab.com/project", True),

        # Homepage URLs (should return False)
        ("https://example.org", False),
        ("https://www.example.com", False),
        ("https://docs.example.com", False),

        # Empty or None
        ("", False),
        (None, False),

        # Edge cases
        ("https://github.com", False),  # No repo path
        ("github.com/user/repo", True),  # Without protocol
        ("git.company.com/project", True),
    ])
    def test_is_repository_url_scenarios(self, url, expected):
        """Test various repository URL detection scenarios"""
        result = is_repository_url(url)
        assert result == expected, f"Failed for URL: {url}"

    def test_all_repository_indicators(self):
        """Test all repository URL indicators"""
        indicators = [
            "github.com/",
            "gitlab.com/",
            "bitbucket.org/",
            "sourceforge.net/projects/",
            "git.",
            ".git"
        ]

        for indicator in indicators:
            url = f"https://{indicator}test"
            result = is_repository_url(url)
            assert result is True, f"Failed for indicator: {indicator}"


class TestIsHomepageUrlRepo:
    """Test suite for is_homepage_url_repo helper function"""

    @pytest.mark.parametrize("url,expected", [
        # Homepage URLs
        ("https://example.org/", True),
        ("https://www.example.com/", True),
        ("https://myproject.io/", True),
        ("https://docs.example.com/", True),
        ("https://documentation.example.org/", True),
        ("https://example.readthedocs.io/", True),
        ("https://user.github.io/project", True),

        # Repository URLs (should return False)
        ("https://github.com/user/repo", False),
        ("https://gitlab.com/project", False),
        ("https://bitbucket.org/team/repo", False),

        # Case insensitive
        ("HTTPS://WWW.EXAMPLE.COM/", True),
        ("https://Docs.Example.org/", True),

        # Edge cases
        ("", False),
        (None, False),

        # Mixed cases - repository URL with .org should not be homepage
        ("https://github.org/user/repo", False),  # Has github indicator
        ("https://example.org/projects/repo.git", False),  # Has .git indicator
    ])
    def test_is_homepage_url_repo_scenarios(self, url, expected):
        """Test various homepage URL detection scenarios"""
        result = is_homepage_url_repo(url)
        assert result == expected, f"Failed for URL: {url}"

    def test_homepage_indicators(self):
        """Test all homepage indicators"""
        indicators = [
            ".org/",
            ".com/",
            ".net/",
            ".io/",
            "www.",
            "docs.",
            "documentation",
            "readthedocs",
            "github.io"
        ]

        for indicator in indicators:
            url = f"https://{indicator}test"
            # Only test if it's not also a repository URL
            if not is_repository_url(url):
                result = is_homepage_url_repo(url)
                assert result is True, f"Failed for indicator: {indicator}"

    def test_repository_takes_precedence(self):
        """Test that repository URLs are not classified as homepage"""
        # These have homepage indicators but are actually repositories
        repo_urls = [
            "https://github.com/user/repo",  # Has .com
            "https://gitlab.org/project",  # Has .org
            "https://bitbucket.net/team/repo",  # Has .net
        ]

        for url in repo_urls:
            result = is_homepage_url_repo(url)
            assert result is False, f"Should not be homepage: {url}"


class TestDetectCodeRepositoryHomepagePitfall:
    """Test suite for detect_coderepository_homepage_pitfall function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_pitfall,expected_url,expected_source_file", [
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
                    {"code_repository": "https://example.com"},
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

            # Valid repository URL (no pitfall)
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/codemeta.json",
                            "result": {"value": "https://github.com/user/repo"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    None
            ),

            # Homepage URL instead of repository (has pitfall)
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/codemeta.json",
                            "result": {"value": "https://www.example.org/"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "https://www.example.org/",
                    "codemeta.json"
            ),

            # Documentation URL (has pitfall)
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/package.json",
                            "result": {"value": "https://docs.example.com/"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "https://docs.example.com/",
                    "package.json"
            ),

            # github.io page (has pitfall)
            (
                    {
                        "code_repository": [{
                            "technique": "code_parser",
                            "source": "repository/setup.py",
                            "result": {"value": "https://user.github.io/project"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "https://user.github.io/project",
                    "setup.py"
            ),

            # Non-metadata source (should not trigger)
            (
                    {
                        "code_repository": [{
                            "technique": "github_api",
                            "source": "README.md",
                            "result": {"value": "https://www.example.org/"}
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
        ])
    def test_detect_coderepository_homepage_scenarios(self, somef_data, file_name,
                                                      expected_has_pitfall, expected_url,
                                                      expected_source_file):
        """Test various scenarios for code repository homepage detection"""
        with patch('metacheck.scripts.pitfalls.p009.extract_metadata_source_filename',
                   return_value=expected_source_file):
            result = detect_coderepository_homepage_pitfall(somef_data, file_name)

            assert result["has_pitfall"] == expected_has_pitfall
            assert result["file_name"] == file_name
            assert result["repository_url"] == expected_url
            assert result["is_homepage"] == expected_has_pitfall

            if expected_has_pitfall:
                assert result["metadata_source_file"] == expected_source_file

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_coderepository_homepage_pitfall(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "repository_url" in result
        assert "source" in result
        assert "metadata_source_file" in result
        assert "is_homepage" in result

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
                "result": {"value": "https://www.example.org/"}
            }]
        }

        with patch('metacheck.scripts.pitfalls.p009.extract_metadata_source_filename',
                   return_value=metadata_file):
            result = detect_coderepository_homepage_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] is True
            assert result["metadata_source_file"] == metadata_file

    def test_stops_at_first_match(self):
        """Test that function stops after finding first homepage URL"""
        somef_data = {
            "code_repository": [
                {
                    "technique": "code_parser",
                    "source": "repository/codemeta.json",
                    "result": {"value": "https://www.example1.org/"}
                },
                {
                    "technique": "code_parser",
                    "source": "repository/package.json",
                    "result": {"value": "https://www.example2.org/"}
                }
            ]
        }

        with patch('metacheck.scripts.pitfalls.p009.extract_metadata_source_filename',
                   side_effect=["codemeta.json", "package.json"]):
            result = detect_coderepository_homepage_pitfall(somef_data, "test.json")

            assert result["has_pitfall"] is True
            assert result["repository_url"] == "https://www.example1.org/"

    @pytest.mark.parametrize("homepage_url", [
        "https://www.example.org/",
        "https://example.com/project",
        "https://docs.project.io/",
        "https://documentation.example.net/",
        "https://project.readthedocs.io/",
        "https://user.github.io/project",
    ])
    def test_various_homepage_urls(self, homepage_url):
        """Test detection of various homepage URL formats"""
        somef_data = {
            "code_repository": [{
                "technique": "code_parser",
                "source": "repository/codemeta.json",
                "result": {"value": homepage_url}
            }]
        }

        with patch('metacheck.scripts.pitfalls.p009.extract_metadata_source_filename',
                   return_value="codemeta.json"):
            result = detect_coderepository_homepage_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] is True
            assert result["repository_url"] == homepage_url

    @pytest.mark.parametrize("repo_url", [
        "https://github.com/user/repo",
        "https://gitlab.com/group/project",
        "https://bitbucket.org/team/repository",
        "https://sourceforge.net/projects/myproject",
        "https://git.example.com/repo",
    ])
    def test_valid_repository_urls_no_pitfall(self, repo_url):
        """Test that valid repository URLs don't trigger pitfall"""
        somef_data = {
            "code_repository": [{
                "technique": "code_parser",
                "source": "repository/codemeta.json",
                "result": {"value": repo_url}
            }]
        }

        result = detect_coderepository_homepage_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is False

    def test_source_matching_by_technique(self):
        """Test that technique matching works"""
        # Test with technique in metadata_sources list
        somef_data = {
            "code_repository": [{
                "technique": "codemeta.json",
                "source": "some/path",
                "result": {"value": "https://www.example.org/"}
            }]
        }

        with patch('metacheck.scripts.pitfalls.p009.extract_metadata_source_filename',
                   return_value="codemeta.json"):
            result = detect_coderepository_homepage_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] is True

    def test_source_matching_by_source_field(self):
        """Test that source field matching works"""
        somef_data = {
            "code_repository": [{
                "technique": "other_technique",
                "source": "repository/codemeta.json",
                "result": {"value": "https://www.example.org/"}
            }]
        }

        with patch('metacheck.scripts.pitfalls.p009.extract_metadata_source_filename',
                   return_value="codemeta.json"):
            result = detect_coderepository_homepage_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] is True

    def test_multiple_entries_mixed_sources(self):
        """Test with multiple entries from different sources"""
        somef_data = {
            "code_repository": [
                {
                    "technique": "github_api",
                    "source": "GitHub API",
                    "result": {"value": "https://github.com/user/repo"}
                },
                {
                    "technique": "code_parser",
                    "source": "repository/codemeta.json",
                    "result": {"value": "https://www.example.org/"}
                }
            ]
        }

        with patch('metacheck.scripts.pitfalls.p009.extract_metadata_source_filename',
                   return_value="codemeta.json"):
            result = detect_coderepository_homepage_pitfall(somef_data, "test.json")

            assert result["has_pitfall"] is True
            assert result["repository_url"] == "https://www.example.org/"

    def test_empty_source_field(self):
        """Test handling of empty source field"""
        somef_data = {
            "code_repository": [{
                "technique": "code_parser",
                "source": "",
                "result": {"value": "https://www.example.org/"}
            }]
        }

        with patch('metacheck.scripts.pitfalls.p009.extract_metadata_source_filename',
                   return_value=None):
            result = detect_coderepository_homepage_pitfall(somef_data, "test.json")
            # Should use technique in source field if source is empty
            assert "technique: code_parser" in result.get("source", "")