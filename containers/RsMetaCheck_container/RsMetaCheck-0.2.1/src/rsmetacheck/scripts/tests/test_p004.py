import pytest
from rsmetacheck.scripts.pitfalls.p004 import (
    is_homepage_url,
    detect_readme_homepage_pitfall
)


class TestIsHomepageUrl:
    """Test suite for is_homepage_url function"""

    @pytest.mark.parametrize("url,expected", [
        # Empty or None
        ("", False),
        (None, False),

        # ReadTheDocs URLs (homepage)
        ("https://myproject.readthedocs.io", True),
        ("https://myproject.readthedocs.io/en/latest/", True),

        # GitHub Pages (homepage)
        ("https://username.github.io", True),
        ("https://username.github.io/project", True),

        # Wiki URLs (homepage)
        ("https://github.com/user/repo/wiki", True),
        ("https://gitlab.com/user/repo/wiki", True),

        # Documentation sites (homepage)
        ("https://docs.python.org", True),
        ("https://documentation.example.com", True),

        # GitHub repository root (homepage)
        ("https://github.com/user/repo", True),
        ("https://github.com/user/repo/", True),
        ("https://gitlab.com/user/repo", True),

        # GitHub README files (NOT homepage)
        ("https://github.com/user/repo/blob/main/README.md", False),
        ("https://github.com/user/repo/readme.md", False),
        ("https://github.com/user/repo/README", False),
        ("https://gitlab.com/user/repo/blob/master/README.md", False),

        # .org, .com, .net domains (homepage)
        ("https://example.org", True),
        ("https://example.com", True),
        ("https://example.net", True),

        # Raw content URLs (depends on context)
        ("https://raw.githubusercontent.com/user/repo/main/README.md", False),

        # Mixed case
        ("https://GitHub.com/user/repo", True),
        ("https://github.com/user/repo/Blob/main/README.md", False),

        # Edge cases
        ("https://github.com", True),
        ("https://docs.github.com", True),
    ])
    def test_homepage_detection_scenarios(self, url, expected):
        """Test various URL scenarios for homepage detection"""
        result = is_homepage_url(url)
        assert result == expected

    @pytest.mark.parametrize("url", [
        "https://github.com/user/repo/blob/main/README.md",
        "https://github.com/user/repo/blob/master/readme.txt",
        "https://gitlab.com/user/repo/blob/main/README.rst",
        "https://raw.githubusercontent.com/user/repo/main/README.md",
    ])
    def test_readme_files_not_detected_as_homepage(self, url):
        """Test that README file URLs are not detected as homepages"""
        result = is_homepage_url(url)
        assert result == False

    @pytest.mark.parametrize("indicator", [
        '.readthedocs.io',
        '.github.io',
        'wiki',
        'docs.',
        'documentation',
        '.org',
        '.com',
        '.net'
    ])
    def test_all_homepage_indicators(self, indicator):
        """Test that all homepage indicators are detected"""
        url = f"https://example{indicator}/path"
        result = is_homepage_url(url)
        assert result == True


class TestDetectReadmeHomepagePitfall:
    """Test suite for detect_readme_homepage_pitfall function"""

    @pytest.mark.parametrize("somef_data,file_name,expected_has_pitfall,expected_url", [
        # No readme_url key
        (
                {},
                "test_repo.json",
                False,
                None
        ),

        # readme_url not a list
        (
                {"readme_url": "https://example.com"},
                "test_repo.json",
                False,
                None
        ),

        # Empty readme_url list
        (
                {"readme_url": []},
                "test_repo.json",
                False,
                None
        ),

        # Valid README file URL (no pitfall)
        (
                {
                    "readme_url": [{
                        "technique": "code_parser",
                        "source": "repository/codemeta.json",
                        "result": {"value": "https://github.com/user/repo/blob/main/README.md"}
                    }]
                },
                "test_repo.json",
                False,
                None
        ),

        # Homepage URL in codemeta (pitfall)
        (
                {
                    "readme_url": [{
                        "technique": "code_parser",
                        "source": "repository/codemeta.json",
                        "result": {"value": "https://github.com/user/repo"}
                    }]
                },
                "test_repo.json",
                True,
                "https://github.com/user/repo"
        ),

        # ReadTheDocs URL (pitfall)
        (
                {
                    "readme_url": [{
                        "technique": "code_parser",
                        "source": "repository/codemeta.json",
                        "result": {"value": "https://myproject.readthedocs.io"}
                    }]
                },
                "test_repo.json",
                True,
                "https://myproject.readthedocs.io"
        ),

        # Wiki URL (pitfall)
        (
                {
                    "readme_url": [{
                        "technique": "code_parser",
                        "source": "repository/codemeta.json",
                        "result": {"value": "https://github.com/user/repo/wiki"}
                    }]
                },
                "test_repo.json",
                True,
                "https://github.com/user/repo/wiki"
        ),

        # GitHub Pages URL (pitfall)
        (
                {
                    "readme_url": [{
                        "technique": "code_parser",
                        "source": "repository/codemeta.json",
                        "result": {"value": "https://username.github.io/project"}
                    }]
                },
                "test_repo.json",
                True,
                "https://username.github.io/project"
        ),

        # Non-codemeta source (should not detect)
        (
                {
                    "readme_url": [{
                        "technique": "other_method",
                        "source": "README.md",
                        "result": {"value": "https://github.com/user/repo"}
                    }]
                },
                "test_repo.json",
                False,
                None
        ),

        # Wrong technique (should not detect)
        (
                {
                    "readme_url": [{
                        "technique": "header_analysis",
                        "source": "repository/codemeta.json",
                        "result": {"value": "https://github.com/user/repo"}
                    }]
                },
                "test_repo.json",
                False,
                None
        ),

        # Multiple entries, first non-codemeta, second codemeta with homepage
        (
                {
                    "readme_url": [
                        {
                            "technique": "other_method",
                            "source": "README.md",
                            "result": {"value": "https://github.com/user/repo/blob/main/README.md"}
                        },
                        {
                            "technique": "code_parser",
                            "source": "repository/codemeta.json",
                            "result": {"value": "https://docs.example.com"}
                        }
                    ]
                },
                "test_repo.json",
                True,
                "https://docs.example.com"
        ),

        # Missing result or value
        (
                {
                    "readme_url": [{
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
                                      expected_has_pitfall, expected_url):
        """Test various README homepage pitfall detection scenarios"""
        result = detect_readme_homepage_pitfall(somef_data, file_name)

        assert result["has_pitfall"] == expected_has_pitfall
        assert result["file_name"] == file_name
        assert result["readme_url"] == expected_url

        if expected_has_pitfall:
            assert result["source"] is not None
            assert result["is_homepage"] == True

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_readme_homepage_pitfall(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "readme_url" in result
        assert "source" in result
        assert "is_homepage" in result

    @pytest.mark.parametrize("homepage_type,url", [
        ("readthedocs", "https://project.readthedocs.io"),
        ("github_pages", "https://user.github.io"),
        ("wiki", "https://github.com/user/repo/wiki"),
        ("docs_site", "https://docs.example.com"),
        ("repo_root", "https://github.com/user/repo"),
    ])
    def test_different_homepage_types(self, homepage_type, url):
        """Test detection of different types of homepage URLs"""
        somef_data = {
            "readme_url": [{
                "technique": "code_parser",
                "source": "repository/codemeta.json",
                "result": {"value": url}
            }]
        }

        result = detect_readme_homepage_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] == True

    def test_stops_at_first_pitfall(self):
        """Test that detection stops at first pitfall found"""
        somef_data = {
            "readme_url": [
                {
                    "technique": "code_parser",
                    "source": "repository/codemeta.json",
                    "result": {"value": "https://first-homepage.com"}
                },
                {
                    "technique": "code_parser",
                    "source": "repository/codemeta.json",
                    "result": {"value": "https://second-homepage.com"}
                }
            ]
        }

        result = detect_readme_homepage_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] == True
        assert result["readme_url"] == "https://first-homepage.com"