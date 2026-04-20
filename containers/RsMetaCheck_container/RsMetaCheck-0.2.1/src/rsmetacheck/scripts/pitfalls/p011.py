import requests
from typing import Dict


def is_url_accessible(url: str, timeout: int = 10) -> bool:
    """
    Check if a URL is accessible by making an HTTP request.
    Returns True if the URL returns a successful HTTP status code.
    """
    try:
        # Clean up the URL - remove leading/trailing whitespace and newlines
        clean_url = url.strip()

        # Make a HEAD request first (faster than GET)
        response = requests.head(clean_url, timeout=timeout, allow_redirects=True)

        # If HEAD is not allowed, try GET
        if response.status_code == 405:  # Method Not Allowed
            response = requests.get(clean_url, timeout=timeout, allow_redirects=True)

        # Consider 2xx and 3xx status codes as successful
        return response.status_code < 400

    except requests.exceptions.RequestException:
        # Any request exception means the URL is not accessible
        return False
    except Exception:
        # Any other exception means the URL is not accessible
        return False


def detect_issue_tracker_format_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when codemeta.json IssueTracker URL is not accessible.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "issue_url": None,
        "source": None,
        "format_violation": None
    }

    if "issue_tracker" not in somef_data:
        return result

    issues_entries = somef_data["issue_tracker"]
    if not isinstance(issues_entries, list):
        return result

    for entry in issues_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        if "codemeta.json" in source or (technique == "code_parser" and "codemeta" in source.lower()):
            if "result" in entry and "value" in entry["result"]:
                issue_url = entry["result"]["value"]

                # Check if URL is accessible
                if not is_url_accessible(issue_url):
                    result["has_pitfall"] = True
                    result["issue_url"] = issue_url
                    result["source"] = source
                    result["format_violation"] = "URL is not accessible or returns error status"
                    break

    return result