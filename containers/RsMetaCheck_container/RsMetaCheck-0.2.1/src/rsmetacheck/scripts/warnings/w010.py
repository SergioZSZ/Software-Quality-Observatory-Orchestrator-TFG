from typing import Dict
import re
from rsmetacheck.utils.pitfall_utils import extract_metadata_source_filename

def is_git_remote_shorthand(url: str) -> bool:
    """
    Check if URL uses Git remote-style shorthand instead of full URL.
    """
    if not url or not isinstance(url, str):
        return False

    # Git remote shorthand patterns
    shorthand_patterns = [
        r'^[a-zA-Z0-9.-]+:[a-zA-Z0-9._/-]+\.git$',  # github.com:user/repo.git
        r'^[a-zA-Z0-9.-]+:[a-zA-Z0-9._/-]+$',  # github.com:user/repo
    ]

    url = url.strip()

    if url.startswith(('http://', 'https://')):
        return False

    for pattern in shorthand_patterns:
        if re.match(pattern, url):
            return True

    return False


def detect_git_remote_shorthand_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when metadata files use Git remote-style shorthand in codeRepository.
    """
    result = {
        "has_warning": False,
        "file_name": file_name,
        "repository_url": None,
        "source": None,
        "metadata_source_file": None,
        "is_shorthand": False
    }

    if "code_repository" not in somef_data:
        return result

    repo_entries = somef_data["code_repository"]
    if not isinstance(repo_entries, list):
        return result

    metadata_techniques = ["code_parser"]
    metadata_sources = ["codemeta.json", "DESCRIPTION", "composer.json", "package.json", "pom.xml", "pyproject.toml", "requirements.txt", "setup.py"]

    for entry in repo_entries:
        technique = entry.get("technique", "")
        source = entry.get("source", "")

        is_metadata_source = (
                technique in metadata_techniques or
                any(src in source.lower() for src in metadata_sources)
        )

        if is_metadata_source:
            if "result" in entry and "value" in entry["result"]:
                repo_url = entry["result"]["value"]

                if is_git_remote_shorthand(repo_url):
                    result["has_warning"] = True
                    result["repository_url"] = repo_url
                    result["source"] = source if source else f"technique: {technique}"
                    result["metadata_source_file"] = extract_metadata_source_filename(source)
                    result["is_shorthand"] = True
                    break

    return result