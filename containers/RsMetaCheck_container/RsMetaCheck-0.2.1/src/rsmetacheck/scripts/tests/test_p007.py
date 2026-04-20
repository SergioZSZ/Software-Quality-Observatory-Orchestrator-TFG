import pytest
from rsmetacheck.scripts.pitfalls.p007 import detect_citation_missing_reference_publication_pitfall


class TestDetectCitationMissingReferencePublicationPitfall:
    """Test suite for detect_citation_missing_reference_publication_pitfall function"""

    @pytest.mark.parametrize(
        "somef_data,file_name,expected_has_pitfall,expected_codemeta_ref,expected_citation_ref,expected_citation_exists",
        [
            # No reference_publication key
            (
                    {},
                    "test_repo.json",
                    False,
                    False,
                    False,
                    False
            ),

            # reference_publication not a list
            (
                    {"reference_publication": "some string"},
                    "test_repo.json",
                    False,
                    False,
                    False,
                    False
            ),

            # Empty reference_publication list
            (
                    {"reference_publication": []},
                    "test_repo.json",
                    False,
                    False,
                    False,
                    False
            ),

            # Only codemeta has reference, no CITATION.cff in repo (no pitfall)
            (
                    {
                        "reference_publication": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "https://doi.org/10.1000/paper.123"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    True,
                    False,
                    False
            ),

            # Both codemeta and CITATION.cff have reference (no pitfall)
            (
                    {
                        "reference_publication": [
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "https://doi.org/10.1000/paper.123"}
                            },
                            {
                                "source": "repository/CITATION.cff",
                                "technique": "code_parser",
                                "result": {"value": "https://doi.org/10.1000/paper.123"}
                            }
                        ],
                        "authors": [{
                            "source": "repository/CITATION.cff",
                            "result": {"value": "Author Name"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    True,
                    True,
                    True
            ),

            # Codemeta has reference, CITATION.cff exists but no reference (pitfall)
            (
                    {
                        "reference_publication": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "https://doi.org/10.1000/paper.123"}
                        }],
                        "authors": [{
                            "source": "repository/CITATION.cff",
                            "result": {"value": "Author Name"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    True,
                    False,
                    True
            ),

            # Codemeta has reference, CITATION.cff detected in title field (pitfall)
            (
                    {
                        "reference_publication": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "https://doi.org/10.1000/paper.123"}
                        }],
                        "title": [{
                            "source": "repository/CITATION.cff",
                            "result": {"value": "Project Title"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    True,
                    False,
                    True
            ),

            # Codemeta has reference, CITATION.cff detected in description field (pitfall)
            (
                    {
                        "reference_publication": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "https://doi.org/10.1000/paper.123"}
                        }],
                        "description": [{
                            "source": "repository/CITATION.cff",
                            "result": {"value": "Description"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    True,
                    False,
                    True
            ),

            # Codemeta has reference, CITATION.cff detected in version field (pitfall)
            (
                    {
                        "reference_publication": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "https://doi.org/10.1000/paper.123"}
                        }],
                        "version": [{
                            "source": "repository/CITATION.cff",
                            "result": {"value": "1.0.0"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    True,
                    False,
                    True
            ),

            # Codemeta has reference, CITATION.cff detected in license field (pitfall)
            (
                    {
                        "reference_publication": [{
                            "source": "repository/codemeta.json",
                            "technique": "code_parser",
                            "result": {"value": "https://doi.org/10.1000/paper.123"}
                        }],
                        "license": [{
                            "source": "repository/CITATION.cff",
                            "result": {"value": "MIT"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    True,
                    False,
                    True
            ),

            # Only CITATION.cff has reference, not codemeta (no pitfall)
            (
                    {
                        "reference_publication": [{
                            "source": "repository/CITATION.cff",
                            "technique": "code_parser",
                            "result": {"value": "https://doi.org/10.1000/paper.123"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    False,
                    True,
                    False
            ),

            # Multiple codemeta references, CITATION.cff exists but no reference (pitfall)
            (
                    {
                        "reference_publication": [
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "https://doi.org/10.1000/paper.123"}
                            },
                            {
                                "source": "repository/codemeta.json",
                                "technique": "code_parser",
                                "result": {"value": "https://doi.org/10.1000/paper.456"}
                            }
                        ],
                        "authors": [{
                            "source": "repository/CITATION.cff",
                            "result": {"value": "Author Name"}
                        }]
                    },
                    "test_repo.json",
                    True,
                    True,
                    False,
                    True
            ),

            # Non-code_parser technique (should not detect codemeta reference)
            (
                    {
                        "reference_publication": [{
                            "source": "repository/codemeta.json",
                            "technique": "header_analysis",
                            "result": {"value": "https://doi.org/10.1000/paper.123"}
                        }],
                        "authors": [{
                            "source": "repository/CITATION.cff",
                            "result": {"value": "Author Name"}
                        }]
                    },
                    "test_repo.json",
                    False,
                    False,
                    False,
                    True
            ),
        ])
    def test_detect_pitfall_scenarios(self, somef_data, file_name, expected_has_pitfall,
                                      expected_codemeta_ref, expected_citation_ref,
                                      expected_citation_exists):
        """Test various citation missing reference publication scenarios"""
        result = detect_citation_missing_reference_publication_pitfall(somef_data, file_name)

        assert result["has_pitfall"] == expected_has_pitfall
        assert result["file_name"] == file_name
        assert result["codemeta_has_reference"] == expected_codemeta_ref
        assert result["citation_cff_has_reference"] == expected_citation_ref
        assert result["citation_cff_exists"] == expected_citation_exists

    def test_result_structure(self):
        """Test that result always has the expected structure"""
        somef_data = {}
        result = detect_citation_missing_reference_publication_pitfall(somef_data, "test.json")

        assert "has_pitfall" in result
        assert "file_name" in result
        assert "codemeta_has_reference" in result
        assert "citation_cff_has_reference" in result
        assert "citation_cff_exists" in result

    @pytest.mark.parametrize("category", ["authors", "title", "description", "version", "license"])
    def test_citation_cff_detection_in_all_categories(self, category):
        """Test that CITATION.cff is detected in all supported categories"""
        somef_data = {
            "reference_publication": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": "https://doi.org/10.1000/paper.123"}
            }],
            category: [{
                "source": "repository/CITATION.cff",
                "result": {"value": "test_value"}
            }]
        }

        result = detect_citation_missing_reference_publication_pitfall(somef_data, "test.json")
        assert result["has_pitfall"] == True
        assert result["citation_cff_exists"] == True

    def test_pitfall_requires_all_conditions(self):
        """Test that pitfall is only detected when all conditions are met"""
        # Condition 1: codemeta has reference - YES
        # Condition 2: CITATION.cff exists - NO
        # Result: No pitfall
        somef_data1 = {
            "reference_publication": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": "https://doi.org/10.1000/paper.123"}
            }]
        }
        result1 = detect_citation_missing_reference_publication_pitfall(somef_data1, "test.json")
        assert result1["has_pitfall"] == False

        # Condition 1: codemeta has reference - NO
        # Condition 2: CITATION.cff exists - YES
        # Result: No pitfall
        somef_data2 = {
            "authors": [{
                "source": "repository/CITATION.cff",
                "result": {"value": "Author"}
            }]
        }
        result2 = detect_citation_missing_reference_publication_pitfall(somef_data2, "test.json")
        assert result2["has_pitfall"] == False

        # Condition 1: codemeta has reference - YES
        # Condition 2: CITATION.cff exists - YES
        # Condition 3: CITATION.cff has reference - YES
        # Result: No pitfall
        somef_data3 = {
            "reference_publication": [
                {
                    "source": "repository/codemeta.json",
                    "technique": "code_parser",
                    "result": {"value": "https://doi.org/10.1000/paper.123"}
                },
                {
                    "source": "repository/CITATION.cff",
                    "technique": "code_parser",
                    "result": {"value": "https://doi.org/10.1000/paper.123"}
                }
            ]
        }
        result3 = detect_citation_missing_reference_publication_pitfall(somef_data3, "test.json")
        assert result3["has_pitfall"] == False

        # Condition 1: codemeta has reference - YES
        # Condition 2: CITATION.cff exists - YES
        # Condition 3: CITATION.cff has reference - NO
        # Result: Pitfall detected!
        somef_data4 = {
            "reference_publication": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": "https://doi.org/10.1000/paper.123"}
            }],
            "authors": [{
                "source": "repository/CITATION.cff",
                "result": {"value": "Author"}
            }]
        }
        result4 = detect_citation_missing_reference_publication_pitfall(somef_data4, "test.json")
        assert result4["has_pitfall"] == True

    def test_non_list_entries_handled(self):
        """Test that non-list entries in categories don't cause errors"""
        somef_data = {
            "reference_publication": [{
                "source": "repository/codemeta.json",
                "technique": "code_parser",
                "result": {"value": "https://doi.org/10.1000/paper.123"}
            }],
            "authors": "not a list",  # Invalid format
            "title": [{
                "source": "repository/CITATION.cff",
                "result": {"value": "Title"}
            }]
        }

        result = detect_citation_missing_reference_publication_pitfall(somef_data, "test.json")
        # Should still detect CITATION.cff from title
        assert result["citation_cff_exists"] == True
        assert result["has_pitfall"] == True


        result = detect_citation_missing_reference_publication_pitfall(somef_data, "test.json")
        assert result["codemeta_has_reference"] == True
        assert result["citation_cff_exists"] == True
        assert result["has_pitfall"] == True