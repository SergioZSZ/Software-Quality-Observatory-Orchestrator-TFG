from typing import Dict, Optional, Tuple
from datetime import datetime
import re


def extract_github_api_date_updated(somef_data: Dict) -> Optional[str]:
    """
    Extract date_updated from GitHub API in SoMEF output.
    Returns the date string or None if not found.
    """
    if "date_updated" not in somef_data:
        return None

    date_entries = somef_data["date_updated"]
    if not isinstance(date_entries, list):
        return None

    # Look for date from GitHub API
    for entry in date_entries:
        if "technique" in entry and entry["technique"] == "GitHub_API":
            if "result" in entry and "value" in entry["result"]:
                return entry["result"]["value"]

    return None


def extract_codemeta_date_modified(somef_data: Dict) -> Optional[Dict[str, str]]:
    """
    Extract dateModified from codemeta.json in SoMEF output.
    Returns a dict with source and date, or None if not found.
    """
    if "date_updated" not in somef_data:
        return None

    date_entries = somef_data["date_updated"]
    if not isinstance(date_entries, list):
        return None

    for entry in date_entries:
        if "source" in entry:
            source = entry["source"]
            if "codemeta.json" in source:
                if "result" in entry and "value" in entry["result"]:
                    return {
                        "source": source,
                        "date": entry["result"]["value"]
                    }
        elif "technique" in entry and entry["technique"] == "code_parser":
            if "result" in entry and "value" in entry["result"]:
                return {
                    "source": "codemeta.json (code_parser)",
                    "date": entry["result"]["value"]
                }

    return None


def normalize_date_for_comparison(date_string: str) -> Optional[datetime]:
    """
    Normalize different date formats to datetime objects for comparison.
    Handles formats like:
    - "2025-02-05T18:00:24Z"
    - "2023-11-17"
    - "2022-03-11T19:01:51.720Z"
    """
    if not date_string:
        return None

    date_string = date_string.strip()

    date_formats = [
        "%Y-%m-%dT%H:%M:%SZ",  # "2025-02-05T18:00:24Z"
        "%Y-%m-%dT%H:%M:%S.%fZ",  # "2022-03-11T19:01:51.720Z"
        "%Y-%m-%d",  # "2023-11-17"
        "%Y-%m-%dT%H:%M:%S",  # Without Z
        "%Y-%m-%dT%H:%M:%S.%f",  # With microseconds, no Z
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    date_match = re.match(r'^(\d{4}-\d{2}-\d{2})', date_string)
    if date_match:
        try:
            return datetime.strptime(date_match.group(1), "%Y-%m-%d")
        except ValueError:
            pass

    return None


def calculate_date_difference_days(date1: datetime, date2: datetime) -> int:
    """
    Calculate the difference in days between two datetime objects.
    Returns absolute difference in days.
    """
    diff = abs((date1 - date2).days)
    return diff


def detect_outdated_datemodified(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect outdated dateModified in codemeta.json warning for a single repository.
    Returns detection result with warning info.
    """
    result = {
        "has_warning": False,
        "file_name": file_name,
        "github_api_date": None,
        "codemeta_date": None,
        "codemeta_source": None,
        "difference_days": 0,
        "github_api_date_parsed": None,
        "codemeta_date_parsed": None
    }

    github_api_date = extract_github_api_date_updated(somef_data)

    codemeta_data = extract_codemeta_date_modified(somef_data)

    if not github_api_date or not codemeta_data:
        return result

    result["github_api_date"] = github_api_date
    result["codemeta_date"] = codemeta_data["date"]
    result["codemeta_source"] = codemeta_data["source"]

    github_date_parsed = normalize_date_for_comparison(github_api_date)
    codemeta_date_parsed = normalize_date_for_comparison(codemeta_data["date"])

    if not github_date_parsed or not codemeta_date_parsed:
        return result

    result["github_api_date_parsed"] = github_date_parsed.isoformat()
    result["codemeta_date_parsed"] = codemeta_date_parsed.isoformat()

    difference_days = calculate_date_difference_days(github_date_parsed, codemeta_date_parsed)
    result["difference_days"] = difference_days

    if github_date_parsed > codemeta_date_parsed and difference_days > 1:
        result["has_warning"] = True

    return result