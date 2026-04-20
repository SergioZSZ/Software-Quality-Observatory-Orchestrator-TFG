from typing import Dict, List
import re
from urllib.parse import urlparse



def is_homepage_url(url: str) -> bool:
    """
    Check if a URL appears to be a homepage/wiki rather than a README file.
    Returns True if it's likely a homepage.
    """
    if not url:
        return False

    url_lower = url.lower()

    if 'raw.githubusercontent.com' in url_lower:
        return False

    # Check for documentation sites and wikis
    homepage_indicators = [
        '.readthedocs.io',
        '.github.io',
        'wiki',
        'docs.',
        'documentation'
    ]

    if ('github.com' in url_lower or 'gitlab.com' in url_lower):
        if 'readme' in url_lower or 'blob/' in url_lower:
            return False
        return True

    # Check for other homepage indicators
    for indicator in homepage_indicators:
        if indicator in url_lower:
            return True

    # Check for generic domains (.org, .com, .net)
    if any(domain in url_lower for domain in ['.org', '.com', '.net']):
        if any(ext in url_lower for ext in ['.md', '.txt', '.rst', '.html', 'readme']):
            return False
        return True

    return False


def detect_readme_homepage_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when README property in codemeta.json points to homepage/wiki instead of README file.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "readme_url": None,
        "source": None,
        "is_homepage": False
    }

    if "readme_url" not in somef_data:
        return result

    readme_entries = somef_data["readme_url"]
    if not isinstance(readme_entries, list):
        return result

    for entry in readme_entries:
        if "technique" in entry and entry["technique"] == "code_parser":
            if "source" in entry and "codemeta.json" in entry["source"]:
                if "result" in entry and "value" in entry["result"]:
                    readme_url = entry["result"]["value"]

                    if is_homepage_url(readme_url):
                        result["has_pitfall"] = True
                        result["readme_url"] = readme_url
                        result["source"] = entry["source"]
                        result["is_homepage"] = True
                        break

    return result