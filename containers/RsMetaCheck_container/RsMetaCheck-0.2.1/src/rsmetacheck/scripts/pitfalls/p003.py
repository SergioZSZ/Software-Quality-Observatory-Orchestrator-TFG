
from typing import Dict
import re
from rsmetacheck.utils.pitfall_utils import extract_metadata_source_filename

def has_multiple_authors_in_single_field(author_value: str) -> bool:
    """
    Check if a single author field contains multiple authors.
    """
    if not author_value or not isinstance(author_value, str):
        return False

    # Common patterns indicating multiple authors
    multiple_author_patterns = [
        r' and ',  # "John Smith and Jane Doe"
        r' & ',  # "John Smith & Jane Doe"
        r',(?!\s+Jr\.?)',  # "John Smith, Jane Doe" (but not "Smith, Jr.")
        r';',  # "John Smith; Jane Doe"
        r'\n',  # Multi-line authors
    ]

    author_value = author_value.strip()

    # Check for patterns that suggest multiple authors
    for pattern in multiple_author_patterns:
        if re.search(pattern, author_value, re.IGNORECASE):
            return True

    return False


def detect_multiple_authors_single_field_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when metadata files have multiple authors in a single field instead of a list.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "author_value": None,
        "source": None,
        "metadata_source_file": None,
        "multiple_authors_detected": False
    }

    if "authors" not in somef_data:
        return result

    authors_entries = somef_data["authors"]
    if not isinstance(authors_entries, list):
        return result

    # Define metadata sources to check (convert to lowercase for comparison)
    metadata_sources = ["codemeta.json", "description", "composer.json", "package.json", "pom.xml", "pyproject.toml",
                        "requirements.txt", "setup.py"]

    for entry in authors_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        is_metadata_source = (
                technique == "code_parser" and
                any(src in source.lower() for src in metadata_sources)
        )

        if is_metadata_source:
            if "result" in entry and "value" in entry["result"]:
                author_value = entry["result"]["value"]

                # Handle different value formats
                if isinstance(author_value, str):
                    if has_multiple_authors_in_single_field(author_value):
                        result["has_pitfall"] = True
                        result["author_value"] = author_value
                        result["source"] = source
                        result["metadata_source_file"] = extract_metadata_source_filename(source)
                        result["multiple_authors_detected"] = True
                        break

                elif isinstance(author_value, dict) and "name" in author_value:
                    # Handle structured author data
                    name_value = author_value["name"]
                    if isinstance(name_value, str) and has_multiple_authors_in_single_field(name_value):
                        result["has_pitfall"] = True
                        result["author_value"] = name_value
                        result["source"] = source
                        result["metadata_source_file"] = extract_metadata_source_filename(source)
                        result["multiple_authors_detected"] = True
                        break

    return result