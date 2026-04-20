from typing import Dict
import re
from rsmetacheck.utils.pitfall_utils import extract_metadata_source_filename


def detect_license_no_version_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when license from metadata files doesn't have specific version.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "license_value": None,
        "metadata_source_file": None,
        "source": None
    }

    if "license" not in somef_data:
        return result

    license_entries = somef_data["license"]
    if not isinstance(license_entries, list):
        return result

    metadata_sources = ["codemeta.json", "DESCRIPTION", "composer.json", "package.json", "pom.xml", "pyproject.toml",
                        "requirements.txt", "setup.py"]

    versioned_patterns = {
        "GPL": r"\bGPL[-\s]?\d+(\.\d+)?",
        "LGPL": r"\bLGPL[-\s]?\d+(\.\d+)?",
        "AGPL": r"\bAGPL[-\s]?\d+(\.\d+)?",
        "Apache": r"\bApache[-\s]?\d+(\.\d+)?",
        "CC": r"\bCC[- ]BY[-\s]?\d+(\.\d+)?",
        "BSD": r"\bBSD[-\s]\d+[-\s]Clause"
    }

    for entry in license_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        is_metadata_source = (
                technique == "code_parser" and
                any(src in source for src in metadata_sources)
        )

        if is_metadata_source:
            if "result" in entry and "value" in entry["result"]:
                license_value = entry["result"]["value"]

                if isinstance(license_value, str):
                    license_upper = license_value.upper()

                    if "0BSD" in license_value:
                        continue
                    
                    if "LICENSEREF-" in license_upper:
                        continue

                    for license_name, version_pattern in versioned_patterns.items():
                        if re.search(rf"\b{license_name}\b", license_upper):
                            if not re.search(version_pattern, license_upper, re.IGNORECASE):
                                result["has_pitfall"] = True
                                result["license_value"] = license_value
                                result["source"] = source
                                result["metadata_source_file"] = extract_metadata_source_filename(source)
                                return result

    return result