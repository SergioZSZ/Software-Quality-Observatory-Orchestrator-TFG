from typing import Dict

def detect_programming_language_no_version_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when programming languages or requirements in codemeta.json do not have versions
    (version field is missing or null).
    """
    result = {
        "has_warning": False,
        "file_name": file_name,
        "programming_languages_without_version": [],
        "requirements_without_version": [],
        "source": None
    }

    if "programming_languages" in somef_data:
        programming_languages_entries = somef_data["programming_languages"]
        if isinstance(programming_languages_entries, list):
            for entry in programming_languages_entries:
                source = entry.get("source", "")
                technique = entry.get("technique", "")

                if technique == "code_parser" and "codemeta.json" in source:
                    if "result" in entry:
                        result_data = entry["result"]

                        if "version" not in result_data or result_data.get("version") is None:
                            lang_name = result_data.get("name", "Unknown")
                            result["programming_languages_without_version"].append(lang_name)
                            result["source"] = source
                            result["has_warning"] = True

    if "requirements" in somef_data:
        requirements_entries = somef_data["requirements"]
        if isinstance(requirements_entries, list):
            for entry in requirements_entries:
                source = entry.get("source", "")
                technique = entry.get("technique", "")

                if technique == "code_parser" and "codemeta.json" in source:
                    if "result" in entry:
                        result_data = entry["result"]

                        if "version" not in result_data or result_data.get("version") is None:
                            req_name = result_data.get("value", result_data.get("name", "Unknown"))
                            result["requirements_without_version"].append(req_name)
                            result["source"] = source
                            result["has_warning"] = True

    return result