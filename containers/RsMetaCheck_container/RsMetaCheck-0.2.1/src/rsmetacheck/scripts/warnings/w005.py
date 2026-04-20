from typing import Dict, List
import re
from rsmetacheck.utils.pitfall_utils import extract_metadata_source_filename


def detect_multiple_requirements_in_string(requirement_string: str) -> List[str]:
    """
    Detect if a requirement string contains multiple requirements.
    Returns list of detected requirements or empty list if just one.
    """
    if not requirement_string or not isinstance(requirement_string, str):
        return []

    # Clean the string
    req_str = requirement_string.strip()

    # Patterns that might indicate multiple requirements
    # Split by common separators but be careful not to split version specifiers
    potential_separators = [
        r'\s{2,}',  # Multiple spaces
        r'\s+(?=[A-Za-z])',  # Space followed by letter (new requirement)
        r',\s*',  # Comma separation
        r';\s*',  # Semicolon separation
    ]

    detected_requirements = []

    if re.search(r'\s{2,}', req_str):
        parts = re.split(r'\s{2,}', req_str)
        if len(parts) > 1:
            detected_requirements = [part.strip() for part in parts if part.strip()]

    if not detected_requirements:
        if re.search(r'\s+[A-Z][A-Za-z]', req_str):
            parts = re.split(r'\s+(?=[A-Z])', req_str)
            if len(parts) > 1:
                detected_requirements = [part.strip() for part in parts if part.strip()]

    return detected_requirements if len(detected_requirements) > 1 else []


def detect_multiple_requirements_string_warning(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when software requirements have multiple requirements written as one string.
    """
    result = {
        "has_warning": False,
        "file_name": file_name,
        "requirement_string": None,
        "detected_requirements": [],
        "source": None,
        "metadata_source_file": None,
        "count_detected": 0
    }

    if "requirements" not in somef_data:
        return result

    requirements_entries = somef_data["requirements"]
    if not isinstance(requirements_entries, list):
        return result

    metadata_sources = ["codemeta.json", "DESCRIPTION", "composer.json", "package.json", "pom.xml", "pyproject.toml", "requirements.txt", "setup.py"]

    for entry in requirements_entries:
        technique = entry.get("technique", "")
        source = entry.get("source", "")

        if technique in metadata_sources or any(
                src in source.lower() for src in ["codemeta.json", "setup.py", "pom.xml"]):
            if "result" in entry and "value" in entry["result"]:
                requirement_value = entry["result"]["value"]

                if isinstance(requirement_value, str):
                    detected_reqs = detect_multiple_requirements_in_string(requirement_value)

                    if detected_reqs:
                        result["has_warning"] = True
                        result["requirement_string"] = requirement_value
                        result["detected_requirements"] = detected_reqs
                        result["source"] = source if source else f"technique: {technique}"
                        result["metadata_source_file"] = extract_metadata_source_filename(source)
                        result["count_detected"] = len(detected_reqs)
                        break

                elif isinstance(requirement_value, list) and len(requirement_value) == 1:
                    single_req = requirement_value[0]
                    if isinstance(single_req, str):
                        detected_reqs = detect_multiple_requirements_in_string(single_req)

                        if detected_reqs:
                            result["has_warning"] = True
                            result["requirement_string"] = single_req
                            result["detected_requirements"] = detected_reqs
                            result["source"] = source if source else f"technique: {technique}"
                            result["metadata_source_file"] = extract_metadata_source_filename(source)
                            result["count_detected"] = len(detected_reqs)
                            break

    return result