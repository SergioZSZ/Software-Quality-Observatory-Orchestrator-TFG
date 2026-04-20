from typing import Dict, Optional
from rsmetacheck.utils.pitfall_utils import normalize_version
from rsmetacheck.utils.pitfall_utils import extract_metadata_source_filename

def extract_version_from_metadata(somef_data: Dict) -> Optional[Dict[str, str]]:
    """
    Extract version from metadata files (codemeta.json, DESCRIPTION, etc.) in SoMEF output.
    Returns a dict with source and version, or None if not found.
    """
    if "version" not in somef_data:
        return None

    version_entries = somef_data["version"]
    if not isinstance(version_entries, list):
        return None

    # Look for version from metadata files (codemeta.json, DESCRIPTION, etc.)
    metadata_sources = ["codemeta.json", "DESCRIPTION", "composer.json", "package.json", "pom.xml", "pyproject.toml", "requirements.txt", "setup.py"]

    for entry in version_entries:
        if "source" in entry:
            source = entry["source"]
            # Check if source contains any metadata file indicators
            if any(meta_file in source for meta_file in metadata_sources):
                if "result" in entry and "value" in entry["result"]:
                    return {
                        "source": source,
                        "version": entry["result"]["value"]
                    }
        elif "result" in entry and "source" in entry["result"]:

            source = entry["result"]["source"]
            if any(meta_file in source for meta_file in metadata_sources):
                if "value" in entry["result"]:
                    return {
                        "source": source,
                        "version": entry["result"]["value"]
                    }

    return None


def extract_latest_release_version(somef_data: Dict) -> Optional[str]:
    """
    Extract the version from the latest release (first element in releases array).
    """
    if "releases" not in somef_data:
        return None

    releases = somef_data["releases"]
    if not isinstance(releases, list) or len(releases) == 0:
        return None

    latest_release = releases[0]

    if isinstance(latest_release, dict):
        if "tag" in latest_release:
            return latest_release["tag"]
        elif "result" in latest_release and isinstance(latest_release["result"], dict):
            if "tag" in latest_release["result"]:
                return latest_release["result"]["tag"]

    return None

def detect_version_mismatch(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect version mismatch pitfall for a single repository.
    Returns detection result with pitfall info or None if no pitfall found.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "metadata_version": None,
        "release_version": None,
        "metadata_source": None,
        "metadata_source_file": None
    }

    metadata_version_info = extract_version_from_metadata(somef_data)

    release_version = extract_latest_release_version(somef_data)

    if metadata_version_info and release_version:
        metadata_version = normalize_version(metadata_version_info["version"])
        normalized_release_version = normalize_version(release_version)

        result["metadata_version"] = metadata_version
        result["release_version"] = normalized_release_version
        result["metadata_source"] = metadata_version_info["source"]
        result["metadata_source_file"] = extract_metadata_source_filename(metadata_version_info["source"])

        if metadata_version != normalized_release_version:
            result["has_pitfall"] = True

    return result