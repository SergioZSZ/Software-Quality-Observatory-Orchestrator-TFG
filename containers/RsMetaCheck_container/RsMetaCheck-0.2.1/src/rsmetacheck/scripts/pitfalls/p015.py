from typing import Dict
import requests
from urllib.parse import urlparse


def is_valid_url_format(url: str) -> bool:
    """
    Check if URL has a valid format.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def check_ci_url_status(url: str, timeout: int = 10) -> Dict:
    """
    Check if continuous integration URL returns a valid response.
    """
    result = {
        "is_accessible": False,
        "status_code": None,
        "error": None
    }

    if not is_valid_url_format(url):
        result["error"] = "Invalid URL format"
        return result

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
        result["status_code"] = response.status_code

        # Consider 200-302 (except 300) as successful
        if 200 <= response.status_code < 300 or 300 < response.status_code <303 :
            result["is_accessible"] = True

    except requests.exceptions.RequestException as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"

    return result


def detect_ci_404_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when codemeta.json continuous integration link returns 404.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "ci_url": None,
        "source": None,
        "status_code": None,
        "error": None
    }

    if "continuous_integration" not in somef_data:
        return result

    ci_entries = somef_data["continuous_integration"]
    if not isinstance(ci_entries, list):
        return result

    for entry in ci_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        if "codemeta.json" in source or (technique == "code_parser" and "codemeta" in source.lower()):
            if "result" in entry and "value" in entry["result"]:
                ci_url = entry["result"]["value"]

                url_status = check_ci_url_status(ci_url)

                if not url_status["is_accessible"]:
                    result["has_pitfall"] = True
                    result["ci_url"] = ci_url
                    result["source"] = source
                    result["status_code"] = url_status["status_code"]
                    result["error"] = url_status["error"]
                    break

    return result