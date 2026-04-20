from typing import Dict
import re


def is_url(value: str) -> bool:
    """
    Check if a value is a URL.
    """
    if not value or not isinstance(value, str):
        return False

    url_patterns = [
        r'^https?://',  # HTTP/HTTPS URLs
        r'^www\.',  # URLs starting with www
        r'\.org',  # Contains .org
        r'\.com',  # Contains .com
        r'\.net',  # Contains .net
    ]

    value_lower = value.lower().strip()

    for pattern in url_patterns:
        if re.search(pattern, value_lower):
            return True

    return False


def detect_development_status_url_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when codemeta.json developmentStatus is a URL instead of a string.
    """
    result = {
        "has_warning": False,
        "file_name": file_name,
        "development_status": None,
        "source": None,
        "is_url": False
    }

    if "development_status" not in somef_data:
        return result

    dev_status_entries = somef_data["development_status"]
    if not isinstance(dev_status_entries, list):
        return result

    for entry in dev_status_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        if "codemeta.json" in source or (technique == "code_parser" and "codemeta" in source.lower()):
            if "result" in entry and "value" in entry["result"]:
                dev_status = entry["result"]["value"]

                if is_url(dev_status):
                    result["has_warning"] = True
                    result["development_status"] = dev_status
                    result["source"] = source
                    result["is_url"] = True
                    break

    return result