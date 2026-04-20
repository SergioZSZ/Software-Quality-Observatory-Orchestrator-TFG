from typing import Dict
import re

def is_software_archive_url(url: str) -> bool:
    """
    Check if URL points to a software archive instead of a research paper.
    """
    if not url or not isinstance(url, str):
        return False

    url = url.lower().strip()

    # Patterns that indicate software archives
    software_archive_patterns = [
        r'zenodo\.org',  # Zenodo software archives
        r'figshare\.com',  # Figshare software archives
        r'github\.com/.*/releases',  # GitHub releases
        r'sourceforge\.net',  # SourceForge
        r'archive\.org',  # Internet Archive
        r'codeocean\.com',  # CodeOcean
        r'osf\.io',  # Open Science Framework (when used for software)
        r'doi\.org/10\.5281',  # Zenodo DOIs
    ]

    for pattern in software_archive_patterns:
        if re.search(pattern, url):
            return True

    return False


def detect_reference_publication_archive_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when codemeta.json referencePublication refers to software archive instead of paper.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "reference_url": None,
        "source": None,
        "is_software_archive": False
    }

    if "reference_publication" not in somef_data:
        return result

    ref_pub_entries = somef_data["reference_publication"]
    if not isinstance(ref_pub_entries, list):
        return result

    for entry in ref_pub_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        if "codemeta.json" in source or (technique == "code_parser" and "codemeta" in source.lower()):
            if "result" in entry and "value" in entry["result"]:
                ref_url = entry["result"]["value"]

                if is_software_archive_url(ref_url):
                    result["has_pitfall"] = True
                    result["reference_url"] = ref_url
                    result["source"] = source
                    result["is_software_archive"] = True
                    break

    return result