from typing import Dict
import re


def is_raw_swhid(identifier: str) -> bool:
    """
    Check if identifier is a raw SWHID without resolvable URL.
    """
    if not identifier or not isinstance(identifier, str):
        return False

    identifier = identifier.strip()

    # If it already has a URL scheme, it's not raw
    if identifier.startswith(('http://', 'https://')):
        return False

    # Check if it's a raw SWHID pattern
    swhid_pattern = r'^swh:1:[a-z]+:[a-f0-9]{40}$'

    if re.match(swhid_pattern, identifier):
        return True

    return False


def detect_raw_swhid_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when codemeta.json identifier uses raw SWHIDs without resolvable URL.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "identifier_value": None,
        "source": None,
        "is_raw_swhid": False
    }

    if "identifier" not in somef_data:
        return result

    identifier_entries = somef_data["identifier"]
    if not isinstance(identifier_entries, list):
        return result

    for entry in identifier_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        if "codemeta.json" in source or (technique == "code_parser" and "codemeta" in source.lower()):
            if "result" in entry and "value" in entry["result"]:
                identifier_value = entry["result"]["value"]

                if is_raw_swhid(identifier_value):
                    result["has_pitfall"] = True
                    result["identifier_value"] = identifier_value
                    result["source"] = source
                    result["is_raw_swhid"] = True
                    break

    return result