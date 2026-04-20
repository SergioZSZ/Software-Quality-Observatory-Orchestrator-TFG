from typing import Dict
import requests
import re
from urllib.parse import urlparse
from rsmetacheck.utils.pitfall_utils import extract_metadata_source_filename


def is_valid_url_format(url: str) -> bool:
    """
    Check if URL has a valid format.
    """
    if url is None:
        raise ValueError("URL cannot be None")

    if not url or not isinstance(url, str):
        return False

    if url.startswith(('git+', 'git://', 'svn+', 'hg+', 'bzr+')):
        return True

    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def check_url_status(url: str, timeout: int = 10) -> Dict:
    """
    Check if URL returns a valid response (not 404 or other error).
    """
    result = {
        "is_accessible": False,
        "status_code": None,
        "error": None
    }

    if not is_valid_url_format(url):
        result["error"] = "Invalid URL format"
        return result

    if url.startswith(('git+', 'git://', 'svn+', 'hg+', 'bzr+')):
        result["is_accessible"] = True
        result["status_code"] = 200
        return result

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
        result["status_code"] = response.status_code

        if (200 <= response.status_code < 300) or response.status_code == 301:
            result["is_accessible"] = True

    except requests.exceptions.RequestException as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"

    return result


def extract_urls_from_requirements(requirement_text: str) -> list:
    """
    Extract URLs from software requirement text.
    """
    if not requirement_text:
        return []

    url_patterns = [
        r'https?://[^\s<>"\']+',  # HTTP/HTTPS URLs
        r'www\.[^\s<>"\']+',  # URLs starting with www
    ]

    urls = []
    for pattern in url_patterns:
        matches = re.findall(pattern, requirement_text, re.IGNORECASE)
        urls.extend(matches)

    cleaned_urls = []
    for url in urls:
        url = re.sub(r'[,;.!?)]$', '', url)
        if url:
            cleaned_urls.append(url)

    return cleaned_urls


def detect_invalid_software_requirement_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when metadata files have software requirements pointing to invalid pages.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "invalid_urls": [],
        "source": None,
        "metadata_source_file": None,
        "requirement_text": None
    }

    if "requirements" not in somef_data:
        return result

    req_entries = somef_data["requirements"]
    if not isinstance(req_entries, list):
        return result

    metadata_sources = ["codemeta.json", "description", "composer.json", "package.json", "pom.xml", "pyproject.toml",
                        "requirements.txt", "setup.py"]

    for entry in req_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        is_metadata_source = (
                technique == "code_parser" and
                any(src in source.lower() for src in metadata_sources)
        )

        if is_metadata_source:
            if "result" in entry and "value" in entry["result"]:
                req_value = entry["result"]["value"]

                if isinstance(req_value, str) and is_valid_url_format(req_value):
                    url_status = check_url_status(req_value)

                    if not url_status["is_accessible"]:
                        result["has_pitfall"] = True
                        result["invalid_urls"] = [{
                            "url": req_value,
                            "status_code": url_status["status_code"],
                            "error": url_status["error"]
                        }]
                        result["source"] = source
                        result["metadata_source_file"] = extract_metadata_source_filename(source)
                        result["requirement_text"] = req_value
                        break
                else:
                    requirement_text = ""
                    if isinstance(req_value, str):
                        requirement_text = req_value
                    elif isinstance(req_value, list):
                        requirement_text = " ".join(str(item) for item in req_value)
                    elif isinstance(req_value, dict):
                        for key in ["name", "value", "description", "text"]:
                            if key in req_value:
                                requirement_text += str(req_value[key]) + " "

                    if requirement_text:
                        urls = extract_urls_from_requirements(requirement_text)

                        if urls:
                            invalid_urls = []

                            for url in urls:
                                url_status = check_url_status(url)

                                if not url_status["is_accessible"]:
                                    invalid_urls.append({
                                        "url": url,
                                        "status_code": url_status["status_code"],
                                        "error": url_status["error"]
                                    })

                            if invalid_urls:
                                result["has_pitfall"] = True
                                result["invalid_urls"] = invalid_urls
                                result["source"] = source
                                result["metadata_source_file"] = extract_metadata_source_filename(source)
                                result["requirement_text"] = requirement_text
                                break

    return result