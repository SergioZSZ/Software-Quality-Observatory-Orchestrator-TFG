from typing import Dict


def get_codemeta_version(somef_data: Dict) -> str:
    """
    Get version from codemeta.json.
    """
    if "version" not in somef_data:
        return None

    version_entries = somef_data["version"]
    if not isinstance(version_entries, list):
        return None

    for entry in version_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        # Check if it's from codemeta.json
        if "codemeta.json" in source or (technique == "code_parser" and "codemeta" in source.lower()):
            if "result" in entry and "value" in entry["result"]:
                return entry["result"]["value"]

    return None


def get_other_metadata_versions(somef_data: Dict) -> list:
    """
    Get versions from other metadata sources (setup.py, pom.xml, etc).
    """
    if "version" not in somef_data:
        return []

    version_entries = somef_data["version"]
    if not isinstance(version_entries, list):
        return []

    other_versions = []
    metadata_sources = ["codemeta.json", "DESCRIPTION", "composer.json", "package.json", "pom.xml", "pyproject.toml", "requirements.txt", "setup.py"]

    for entry in version_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        if "codemeta.json" in source:
            continue

        if technique == "code_parser" or any(src in source.lower() for src in metadata_sources):
            if "result" in entry and "value" in entry["result"]:
                other_versions.append({
                    "version": entry["result"]["value"],
                    "source": source,
                    "technique": technique
                })

    return other_versions


def detect_codemeta_version_mismatch_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when codemeta.json version doesn't match other package metadata versions.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "codemeta_version": None,
        "metadata_source_file": None,
        "other_versions": [],
        "mismatched_versions": []
    }

    codemeta_version = get_codemeta_version(somef_data)
    if not codemeta_version:
        return result

    other_versions = get_other_metadata_versions(somef_data)
    if not other_versions:
        return result

    mismatched_versions = []
    for other_version_entry in other_versions:
        other_version = other_version_entry["version"]

        if codemeta_version.strip() != other_version.strip():
            mismatched_versions.append(other_version_entry)

    if mismatched_versions:
        result["has_pitfall"] = True
        result["codemeta_version"] = codemeta_version
        result["other_versions"] = other_versions
        result["mismatched_versions"] = mismatched_versions
        result["metadata_source_file"] = "codemeta.json"

    return result