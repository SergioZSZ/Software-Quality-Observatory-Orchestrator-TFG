import re
from typing import Dict


def detect_dual_license_missing_codemeta_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when repository has multiple licenses but codemeta.json only lists one.
    """
    result = {
        "has_warning": False,
        "file_name": file_name,
        "has_dual_license_indicator": False,
        "codemeta_license_count": 0,
        "dual_license_source": None
    }

    if "license" not in somef_data:
        return result

    license_entries = somef_data["license"]
    if not isinstance(license_entries, list):
        return result

    dual_license_patterns = [
        r"dual[\s-]?licen[cs]ed?",
        r"dually[\s-]?licen[cs]ed?",
        r"multiple[\s-]?licen[cs]es?",
        r"(?:is|are)\s+licen[cs]ed?\s+under.*(?:and|or).*licen[cs]e", 
        r"choose.*(?:between|from|your).*licen[cs]e",  
        r"either.*or.*licen[cs]e",  
        r"\d+\..*licen[cs]e.*\n.*\d+\..*licen[cs]e",
        r"licen[cs]e.*options?",
        r"available\s+under.*(?:two|multiple|either).*licen[cs]es?",
        r"licen[cs]ed? under.*(?:and|or)"
    ]

    has_dual_license_indicator = False
    dual_license_source = None
    codemeta_license_count = 0

    for entry in license_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        if technique == "code_parser" and "codemeta.json" in source:
            codemeta_license_count += 1
        else:
            if not has_dual_license_indicator and "result" in entry and "value" in entry["result"]:
                license_text = entry["result"]["value"]
                if isinstance(license_text, str):
                    license_text_lower = license_text.lower()
                    for pattern in dual_license_patterns:
                        if re.search(pattern, license_text_lower):
                            has_dual_license_indicator = True
                            dual_license_source = source
                            break

    result["has_dual_license_indicator"] = has_dual_license_indicator
    result["codemeta_license_count"] = codemeta_license_count
    result["dual_license_source"] = dual_license_source

    if has_dual_license_indicator and codemeta_license_count <= 1:
        result["has_warning"] = True

    return result