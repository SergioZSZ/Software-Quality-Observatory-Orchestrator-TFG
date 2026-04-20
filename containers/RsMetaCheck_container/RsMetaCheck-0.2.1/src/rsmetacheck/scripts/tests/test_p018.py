import pytest
from rsmetacheck.scripts.pitfalls.p018 import (
    detect_raw_swhid_pitfall,
    is_raw_swhid
)


class TestIsRawSwhid:
    """Test suite for is_raw_swhid function"""

    @pytest.mark.parametrize("identifier,expected", [
        # Valid raw SWHIDs
        ("swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2", True),
        ("swh:1:dir:d198bc9d7a6bcf6db04f476d29314f157507d505", True),
        ("swh:1:rel:22ece559cc7cc2364edc5e5593d63ae8bd229f9f", True),
        ("swh:1:rev:309cf2674ee7a0749978cf8265ab91a60aea0f7d", True),
        ("swh:1:snp:1a8893e6a86f444e8be8e7bda6cb34fb1735a00e", True),

        # URLs (not raw)
        ("https://archive.softwareheritage.org/swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2", False),
        ("http://archive.softwareheritage.org/swh:1:dir:d198bc9d7a6bcf6db04f476d29314f157507d505", False),

        # Invalid formats
        ("swh:2:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2", False),  # Wrong version
        ("swh:1:cnt:94a9ed024d3859", False),  # Hash too short
        ("swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2extra", False),  # Hash too long
        ("swh:1:CNT:94a9ed024d3859793618152ea559a168bbcbb5e2", False),  # Uppercase type
        ("swh:1:cnt:94A9ED024D3859793618152EA559A168BBCBB5E2", False),  # Uppercase hash

        # Empty/None
        ("", False),
        (None, False),

        # Non-string
        (123, False),
        (["swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2"], False),

        # Whitespace handling
        ("  swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2  ", True),
        (" swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2", True),
        ("swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2 ", True),

        # Not SWHID
        ("https://github.com/user/repo", False),
        ("10.5281/zenodo.1234567", False),
        ("random string", False),
    ])
    def test_is_raw_swhid_scenarios(self, identifier, expected):
        """Test various scenarios for raw SWHID detection"""
        assert is_raw_swhid(identifier) == expected

    def test_all_valid_object_types(self):
        """Test all valid SWHID object types"""
        valid_types = ["cnt", "dir", "rel", "rev", "snp", "ori"]
        hash_value = "94a9ed024d3859793618152ea559a168bbcbb5e2"

        for obj_type in valid_types:
            swhid = f"swh:1:{obj_type}:{hash_value}"
            assert is_raw_swhid(swhid) is True, f"Failed for type: {obj_type}"


class TestDetectRawSwhidPitfall:
    """Test suite for detect_raw_swhid_pitfall function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_pitfall,expected_identifier,expected_is_raw", [
            # No identifier key
            (
                    {},
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # identifier not a list
            (
                    {"identifier": "swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2"},
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Empty identifier list
            (
                    {"identifier": []},
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Raw SWHID from codemeta.json (pitfall)
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2",
                    True
            ),

            # SWHID with URL from codemeta.json (no pitfall)
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {
                                "value": "https://archive.softwareheritage.org/swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Non-SWHID identifier from codemeta.json (no pitfall)
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "10.5281/zenodo.1234567"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Raw SWHID from non-codemeta source (no pitfall)
            (
                    {
                        "identifier": [{
                            "source": "README.md",
                            "technique": "header_analysis",
                            "result": {"value": "swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Missing result key
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser"
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Missing value in result
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {}
                        }]
                    },
                    "test_repo.json",
                    False,
                    None,
                    False
            ),

            # Multiple identifiers, first is raw SWHID
            (
                    {
                        "identifier": [
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2"}
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "10.5281/zenodo.1234567"}
                            }
                        ]
                    },
                    "test_repo.json",
                    True,
                    "swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2",
                    True
            ),

            # Raw SWHID with whitespace
            (
                    {
                        "identifier": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "  swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2  "}
                        }]
                    },
                    "test_repo.json",
                    True,
                    "  swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2  ",
                    True
            ),
        ])
    def test_detect_raw_swhid_scenarios(self, somef_data, file_name,
                                        expected_has_pitfall, expected_identifier,
                                        expected_is_raw):
        """Test various scenarios for raw SWHID detection"""
        result = detect_raw_swhid_pitfall(somef_data, file_name)

        assert result["has_pitfall"] == expected_has_pitfall
        assert result["file_name"] == file_name
        assert result["identifier_value"] == expected_identifier
        assert result["is_raw_swhid"] == expected_is_raw

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_raw_swhid_pitfall(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "identifier_value" in result
        assert "source" in result
        assert "is_raw_swhid" in result

    @pytest.mark.parametrize("swhid_type", ["cnt", "dir", "rel", "rev", "snp"])
    def test_all_swhid_types_detected(self, swhid_type):
        """Test that all SWHID types are properly detected"""
        hash_value = "94a9ed024d3859793618152ea559a168bbcbb5e2"
        swhid = f"swh:1:{swhid_type}:{hash_value}"

        somef_data = {
            "identifier": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": swhid}
            }]
        }

        result = detect_raw_swhid_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True
        assert result["identifier_value"] == swhid

    def test_codemeta_case_insensitive(self):
        """Test detection works with various codemeta.json case variations"""
        test_cases = [
            "repository/codemeta.json",
            "repository/CODEMETA.json",
            "repository/CodeMeta.json",
            "REPOSITORY/CODEMETA.JSON",
        ]

        for source in test_cases:
            somef_data = {
                "identifier": [{
                    "source": source,
                    "technique": "code_parser",
                    "result": {"value": "swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2"}
                }]
            }

            result = detect_raw_swhid_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] is True, f"Failed for source: {source}"

    def test_stops_at_first_raw_swhid(self):
        """Test that function stops after finding first raw SWHID"""
        somef_data = {
            "identifier": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2"}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "swh:1:dir:d198bc9d7a6bcf6db04f476d29314f157507d505"}
                }
            ]
        }

        result = detect_raw_swhid_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True
        assert result["identifier_value"] == "swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2"

    def test_mixed_sources_only_codemeta_checked(self):
        """Test with multiple sources, only codemeta should be checked"""
        somef_data = {
            "identifier": [
                {
                    "source": "README.md",
                    "technique": "header_analysis",
                    "result": {"value": "swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2"}
                },
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "swh:1:dir:d198bc9d7a6bcf6db04f476d29314f157507d505"}
                }
            ]
        }

        result = detect_raw_swhid_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is True
        assert result["identifier_value"] == "swh:1:dir:d198bc9d7a6bcf6db04f476d29314f157507d505"

    def test_http_vs_https_swhid_urls(self):
        """Test that both http and https SWHID URLs are not flagged as raw"""
        test_cases = [
            "https://archive.softwareheritage.org/swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2",
            "http://archive.softwareheritage.org/swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2",
        ]

        for url in test_cases:
            somef_data = {
                "identifier": [{
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": url}
                }]
            }

            result = detect_raw_swhid_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] is False, f"Failed for URL: {url}"

    def test_invalid_swhid_version(self):
        """Test that invalid SWHID version is not detected as raw SWHID"""
        somef_data = {
            "identifier": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": "swh:2:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2"}
            }]
        }

        result = detect_raw_swhid_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] is False

    def test_invalid_hash_length(self):
        """Test that invalid hash lengths are not detected as raw SWHID"""
        test_cases = [
            "swh:1:cnt:94a9ed024d38",  # Too short
            "swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2extra",  # Too long
        ]

        for swhid in test_cases:
            somef_data = {
                "identifier": [{
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": swhid}
                }]
            }

            result = detect_raw_swhid_pitfall(somef_data, "test.json")
            assert result["has_pitfall"] is False, f"Failed for SWHID: {swhid}"