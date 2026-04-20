from typing import Dict, List
import re


def is_valid_identifier(identifier: str) -> bool:
    """
    Check if identifier appears to be a valid unique identifier (DOI, URL) rather than a name.
    """
    if not identifier or not isinstance(identifier, str):
        return False

    identifier = identifier.strip()

    if not identifier:
        return False

    # Check for DOI patterns
    doi_patterns = [
        r'^doi:10\.\d+/.+',  # doi:10.xxxx/yyyy format
        r'^10\.\d+/.+'  # 10.xxxx/yyyy format (bare DOI)
    ]

    for pattern in doi_patterns:
        if re.match(pattern, identifier, re.IGNORECASE):
            return True

    if identifier.lower() in ['doi:', '10.']:
        return False

    url_pattern = r'^https?://.+'
    if re.match(url_pattern, identifier, re.IGNORECASE):
        return True

    if identifier.lower().startswith('ftp://'):
        return False

    if ' ' in identifier and not any(char in identifier for char in ['/', ':', '.']):
        return False

    if identifier.replace(' ', '').replace('-', '').replace('_', '').isalpha():
        return False

    return True


def has_doi_in_other_sources(identifier_entries: List[Dict]) -> bool:
    """
    Check if there's a valid DOI in non-codemeta sources.
    """
    for entry in identifier_entries:
        source = entry.get("source", "")

        if "codemeta.json" in source.lower():
            continue

        if "result" in entry and "value" in entry["result"]:
            identifier_value = entry["result"]["value"]

            if isinstance(identifier_value, str):
                # Check for DOI patterns
                doi_patterns = [
                    r'^doi:10\.\d+/.+',  # doi:10.xxxx/yyyy format
                    r'^10\.\d+/.+'  # 10.xxxx/yyyy format (bare DOI)
                ]

                for pattern in doi_patterns:
                    if re.match(pattern, identifier_value, re.IGNORECASE):
                        return True

    return False


def detect_identifier_name_warning(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when codemeta.json identifier is a name instead of a valid unique identifier,
    but an identifier exists elsewhere.
    """
    result = {
        "has_warning": False,
        "file_name": file_name,
        "codemeta_identifier": None,
        "other_identifier": None,
        "codemeta_source": None,
        "other_source": None,
        "has_valid_identifier_elsewhere": False,
        "other_identifiers": []
    }

    if "identifier" not in somef_data:
        return result

    identifier_entries = somef_data["identifier"]
    if not isinstance(identifier_entries, list):
        return result

    codemeta_identifier = None
    codemeta_source = None
    other_identifier = None
    other_source = None
    other_identifiers = []

    for entry in identifier_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        is_codemeta = (
                "codemeta.json" in source.lower() or
                (technique == "code_parser" and "codemeta" in source.lower())
        )

        if is_codemeta:
            if "result" in entry and "value" in entry["result"]:
                if codemeta_identifier is None:  # Use first one found
                    codemeta_identifier = entry["result"]["value"]
                    codemeta_source = source
                    break  # Stop at first codemeta identifier

    for entry in identifier_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        is_codemeta = (
                "codemeta.json" in source.lower() or
                (technique == "code_parser" and "codemeta" in source.lower())
        )

        if is_codemeta:
            continue

        if "result" in entry and "value" in entry["result"]:
            identifier_value = entry["result"]["value"]

            if is_valid_identifier(identifier_value):
                other_identifiers.append({
                    "value": identifier_value,
                    "source": source
                })

                if other_identifier is None:
                    other_identifier = identifier_value
                    other_source = source

    result["codemeta_identifier"] = codemeta_identifier
    result["codemeta_source"] = codemeta_source
    result["other_identifier"] = other_identifier
    result["other_source"] = other_source
    result["other_identifiers"] = other_identifiers
    result["has_valid_identifier_elsewhere"] = len(other_identifiers) > 0

    if (codemeta_identifier and
            not is_valid_identifier(codemeta_identifier) and
            other_identifier):
        result["has_warning"] = True

    return result