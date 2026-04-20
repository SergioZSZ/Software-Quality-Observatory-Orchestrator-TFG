import pytest
from rsmetacheck.scripts.pitfalls.p005 import (
    is_software_archive_url,
    detect_reference_publication_archive_pitfall
)


class TestIsSoftwareArchiveUrl:
    """Test suite for is_software_archive_url function"""

    @pytest.mark.parametrize("url,expected", [
        # Empty or None
        ("", False),
        (None, False),

        # Not a string
        (123, False),
        ([], False),
        ({}, False),

        # Zenodo URLs (software archive)
        ("https://zenodo.org/record/12345", True),
        ("https://www.zenodo.org/record/67890", True),
        ("http://zenodo.org/communities/software", True),

        # Figshare URLs (software archive)
        ("https://figshare.com/articles/software/title/12345", True),
        ("https://www.figshare.com/s/abcdef123456", True),

        # GitHub releases (software archive)
        ("https://github.com/user/repo/releases", True),
        ("https://github.com/user/repo/releases/tag/v1.0.0", True),
        ("https://github.com/user/repo/releases/latest", True),

        # SourceForge (software archive)
        ("https://sourceforge.net/projects/myproject", True),
        ("https://www.sourceforge.net/projects/myproject/files/", True),

        # Internet Archive (software archive)
        ("https://archive.org/details/software", True),
        ("https://www.archive.org/download/software/file.zip", True),

        # CodeOcean (software archive)
        ("https://codeocean.com/capsule/12345", True),
        ("https://www.codeocean.com/capsule/67890/tree", True),

        # OSF (software archive)
        ("https://osf.io/abc123", True),
        ("https://www.osf.io/xyz789/", True),

        # Zenodo DOI (software archive)
        ("https://doi.org/10.5281/zenodo.12345", True),
        ("http://dx.doi.org/10.5281/zenodo.67890", True),

        # Research paper URLs (NOT software archive)
        ("https://doi.org/10.1000/journal.12345", False),
        ("https://arxiv.org/abs/2101.12345", False),
        ("https://doi.org/10.1109/journal.2021.12345", False),
        ("https://dl.acm.org/doi/10.1145/12345", False),
        ("https://ieeexplore.ieee.org/document/12345", False),

        # GitHub repository (NOT releases)
        ("https://github.com/user/repo", False),
        ("https://github.com/user/repo/blob/main/README.md", False),

        # Case insensitive
        ("https://ZENODO.ORG/record/12345", True),
        ("https://GitHub.com/user/repo/RELEASES", True),

        # With whitespace
        ("  https://zenodo.org/record/12345  ", True),

        # Publisher DOIs (NOT Zenodo)
        ("https://doi.org/10.1038/nature12345", False),
    ])
    def test_software_archive_detection_scenarios(self, url, expected):
        """Test various URL scenarios for software archive detection"""
        result = is_software_archive_url(url)
        assert result == expected

    @pytest.mark.parametrize("pattern", [
        "zenodo.org",
        "figshare.com",
        "github.com/.*/releases",
        "sourceforge.net",
        "archive.org",
        "codeocean.com",
        "osf.io",
        "doi.org/10.5281",
    ])
    def test_all_archive_patterns(self, pattern):
        """Test that all software archive patterns are detected"""
        # Create a URL that matches the pattern
        if "github.com" in pattern:
            url = "https://github.com/user/repo/releases"
        elif "doi.org" in pattern:
            url = "https://doi.org/10.5281/zenodo.12345"
        else:
            url = f"https://{pattern.replace('/', '')}/test"

        result = is_software_archive_url(url)
        assert result == True


class TestDetectReferencePublicationArchivePitfall:
    """Test suite for detect_reference_publication_archive_pitfall function"""

    @pytest.mark.parametrize("somef_data,file_name,expected_has_pitfall,expected_url", [
        # No reference_publication key
        (
                {},
                "test_repo.json",
                False,
                None
        ),

        # reference_publication not a list
        (
                {"reference_publication": "some string"},
                "test_repo.json",
                False,
                None
        ),

        # Empty reference_publication list
        (
                {"reference_publication": []},
                "test_repo.json",
                False,
                None
        ),

        # Valid research paper DOI (no pitfall)
        (
                {
                    "reference_publication": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {"value": "https://doi.org/10.1000/journal.12345"}
                    }]
                },
                "test_repo.json",
                False,
                None
        ),

        # Zenodo archive URL (pitfall)
        (
                {
                    "reference_publication": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {"value": "https://zenodo.org/record/12345"}
                    }]
                },
                "test_repo.json",
                True,
                "https://zenodo.org/record/12345"
        ),

        # GitHub releases URL (pitfall)
        (
                {
                    "reference_publication": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {"value": "https://github.com/user/repo/releases/tag/v1.0.0"}
                    }]
                },
                "test_repo.json",
                True,
                "https://github.com/user/repo/releases/tag/v1.0.0"
        ),

        # Figshare URL (pitfall)
        (
                {
                    "reference_publication": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {"value": "https://figshare.com/articles/software/title/12345"}
                    }]
                },
                "test_repo.json",
                True,
                "https://figshare.com/articles/software/title/12345"
        ),

        # Zenodo DOI (pitfall)
        (
                {
                    "reference_publication": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser",
                        "result": {"value": "https://doi.org/10.5281/zenodo.67890"}
                    }]
                },
                "test_repo.json",
                True,
                "https://doi.org/10.5281/zenodo.67890"
        ),

        # Source without "codemeta.json" but technique is code_parser
        (
                {
                    "reference_publication": [{
                        "source": "some/path/CODEMETA.json",
                        "technique": "code_parser",
                        "result": {"value": "https://zenodo.org/record/12345"}
                    }]
                },
                "test_repo.json",
                True,
                "https://zenodo.org/record/12345"
        ),

        # Non-codemeta source (should not detect)
        (
                {
                    "reference_publication": [{
                        "source": "README.md",
                        "technique": "header_analysis",
                        "result": {"value": "https://zenodo.org/record/12345"}
                    }]
                },
                "test_repo.json",
                False,
                None
        ),

        # Multiple entries, first valid, second archive
        (
                {
                    "reference_publication": [
                        {
                            "source": "README.md",
                            "technique": "header_analysis",
                            "result": {"value": "https://doi.org/10.1000/journal.12345"}
                        },
                        {
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "https://zenodo.org/record/12345"}
                        }
                    ]
                },
                "test_repo.json",
                True,
                "https://zenodo.org/record/12345"
        ),

        # Missing result or value
        (
                {
                    "reference_publication": [{
                        "source": "repository/codemeta.json",
                        "technique": "code_parser"
                    }]
                },
                "test_repo.json",
                False,
                None
        ),
    ])
    def test_detect_pitfall_scenarios(self, somef_data, file_name,
                                      expected_has_pitfall, expected_url):
        """Test various reference publication archive detection scenarios"""
        result = detect_reference_publication_archive_pitfall(somef_data, file_name)

        assert result["has_pitfall"] == expected_has_pitfall
        assert result["file_name"] == file_name
        assert result["reference_url"] == expected_url

        if expected_has_pitfall:
            assert result["source"] is not None
            assert result["is_software_archive"] == True

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_reference_publication_archive_pitfall(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "reference_url" in result
        assert "source" in result
        assert "is_software_archive" in result

    @pytest.mark.parametrize("archive_type,url", [
        ("zenodo", "https://zenodo.org/record/12345"),
        ("figshare", "https://figshare.com/articles/software/title/12345"),
        ("github_releases", "https://github.com/user/repo/releases"),
        ("sourceforge", "https://sourceforge.net/projects/myproject"),
        ("archive_org", "https://archive.org/details/software"),
        ("codeocean", "https://codeocean.com/capsule/12345"),
        ("osf", "https://osf.io/abc123"),
        ("zenodo_doi", "https://doi.org/10.5281/zenodo.12345"),
    ])
    def test_different_archive_types(self, archive_type, url):
        """Test detection of different types of software archives"""
        somef_data = {
            "reference_publication": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": url}
            }]
        }

        result = detect_reference_publication_archive_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] == True

    def test_stops_at_first_pitfall(self):
        """Test that detection stops at first pitfall found"""
        somef_data = {
            "reference_publication": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "https://zenodo.org/record/11111"}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "https://zenodo.org/record/22222"}
                }
            ]
        }

        result = detect_reference_publication_archive_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] == True
        assert result["reference_url"] == "https://zenodo.org/record/11111"