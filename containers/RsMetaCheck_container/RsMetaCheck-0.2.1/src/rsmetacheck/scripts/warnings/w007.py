from typing import Dict


def detect_empty_identifier_warning(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when codemeta.json identifier is empty.
    """
    result = {
        "has_warning": False,
        "file_name": file_name,
        "identifier_value": None,
        "source": None
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

                if not identifier_value or (isinstance(identifier_value, str) and not identifier_value.strip()):
                    result["has_warning"] = True
                    result["identifier_value"] = identifier_value
                    result["source"] = source
                    break

    return result