import re
from typing import Dict, Optional


def extract_license_from_file(somef_data: Dict) -> Optional[Dict[str, str]]:
    """
    Extract license content from LICENSE file in SoMEF output.
    Returns a dict with source and content, or None if not found.
    """
    if "license" not in somef_data:
        return None

    license_entries = somef_data["license"]
    if not isinstance(license_entries, list):
        return None

    for entry in license_entries:
        if "source" in entry:
            source = entry["source"]
            if "license" in source.lower():
                if "result" in entry and "value" in entry["result"]:
                    return {
                        "source": source,
                        "content": entry["result"]["value"]
                    }

    return None


def check_license_template_placeholders(license_content: str) -> bool:
    """
    Check if license content contains template placeholders like <program>, <year>, <name of author>.
    """
    if not license_content:
        return False

    placeholder_patterns = [
        r'<program>',
        r'<year>',
        r'<name of author>',
        r'<name>',
        r'<copyright holders?>',
        r'<owner>',
        r'<author>',
        r'\[year\]',
        r'\[fullname\]',
        r'\[name\]',
        r'\[copyright holder\]',
        r'<yyyy>',
        r'<name of copyright owner>',
        r'\[yyyy\]',
        r'\[name of copyright owner\]',
    ]

    content_lower = license_content.lower()

    for pattern in placeholder_patterns:
        if re.search(pattern, content_lower):
            return True

    return False


def detect_license_template_placeholders(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect license template placeholder pitfall for a single repository.
    Returns detection result with pitfall info or None if no pitfall found.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "license_source": None,
        "placeholders_found": False
    }

    license_info = extract_license_from_file(somef_data)

    if license_info:
        license_content = license_info["content"]
        result["license_source"] = license_info["source"]

        has_template_placeholders = check_license_template_placeholders(license_content)

        if has_template_placeholders:
            result["has_pitfall"] = True
            result["placeholders_found"] = True

    return result