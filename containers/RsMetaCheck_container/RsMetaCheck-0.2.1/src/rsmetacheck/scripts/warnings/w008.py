from typing import Dict
import re
from rsmetacheck.utils.pitfall_utils import extract_metadata_source_filename


def detect_author_name_list_warning(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when author's givenName is a list instead of a string (multiple authors in single field).
    """
    result = {
        "has_warning": False,
        "file_name": file_name,
        "author_value": None,
        "source": None,
        "metadata_source_file": None,
    }

    if "authors" not in somef_data:
        return result

    authors_entries = somef_data["authors"]
    if not isinstance(authors_entries, list):
        return result

    metadata_sources = ["codemeta.json", "DESCRIPTION", "composer.json", "package.json", "pom.xml", "pyproject.toml",
                        "requirements.txt", "setup.py"]

    for entry in authors_entries:
        source = entry.get("source", "")
        technique = entry.get("technique", "")

        is_metadata_source = (
                technique == "code_parser" and
                any(src in source for src in metadata_sources)
        )

        if is_metadata_source:
            if "result" in entry and "value" in entry["result"]:
                author_value = entry["result"]["value"]

                if isinstance(author_value, str):
                    # Look for patterns like "['William', 'Michael'] Landau" or similar list structures
                    list_pattern = r"\[.*?\]"
                    if re.search(list_pattern, author_value):
                        list_content = re.findall(r"\[(.*?)\]", author_value)
                        if list_content:
                            for content in list_content:
                                if "," in content and len(content.split(",")) > 1:
                                    result["has_warning"] = True
                                    result["author_value"] = author_value
                                    result["source"] = source
                                    result["metadata_source_file"] = extract_metadata_source_filename(source)
                                    break

    return result