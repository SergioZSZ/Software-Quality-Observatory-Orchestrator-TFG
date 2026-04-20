from typing import Dict


def detect_citation_missing_reference_publication_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when CITATION.cff doesn't have referencePublication even though it's referenced in codemeta.json.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "codemeta_has_reference": False,
        "citation_cff_has_reference": False,
        "citation_cff_exists": False
    }

    if "reference_publication" in somef_data:
        ref_pub_entries = somef_data["reference_publication"]
        if isinstance(ref_pub_entries, list):
            for entry in ref_pub_entries:
                source = entry.get("source", "")
                technique = entry.get("technique", "")

                if technique == "code_parser" and "codemeta.json" in source:
                    if "result" in entry and "value" in entry["result"]:
                        result["codemeta_has_reference"] = True

                elif "CITATION.cff" in source:
                    if "result" in entry and "value" in entry["result"]:
                        result["citation_cff_has_reference"] = True

    citation_cff_sources = ["authors", "title", "description", "version", "license"]
    for category in citation_cff_sources:
        if category in somef_data:
            entries = somef_data[category]
            if isinstance(entries, list):
                for entry in entries:
                    source = entry.get("source", "")
                    if "CITATION.cff" in source:
                        result["citation_cff_exists"] = True
                        break

        if result["citation_cff_exists"]:
            break

    if (result["codemeta_has_reference"] and
            result["citation_cff_exists"] and
            not result["citation_cff_has_reference"]):
        result["has_pitfall"] = True

    return result