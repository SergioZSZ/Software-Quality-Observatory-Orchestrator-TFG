from typing import Dict
from rsmetacheck.utils.pitfall_utils import extract_metadata_source_filename

def is_local_file_license(license_value: str) -> bool:
    """
    Check if license value points to a local file instead of stating the license name.
    """
    if not license_value or not isinstance(license_value, str):
        return False

    license_lower = license_value.lower().strip()

    if license_lower.startswith('http://') or license_lower.startswith('https://'):
        return False

    if license_value.startswith('./') or license_value.startswith('../'):
        return True

    if ('/' in license_value or '\\' in license_value):
        return True

    license_file_names = [
        'license', 'license.md', 'license.txt', 'license.rst',
        'copying', 'copying.md', 'copying.txt',
        'copyright', 'copyright.md', 'copyright.txt',
        'licence', 'licence.md', 'licence.txt',  # British spelling
        'readme.md', 'doc.txt', 'file.rst'
    ]

    if license_lower in license_file_names:
        return True

    file_extensions = ['.md', '.txt', '.rst']
    if any(license_lower.endswith(ext) for ext in file_extensions):
        return True

    return False


def detect_local_file_license_pitfall(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect when license in metadata files points to a local file instead of stating the name.
    """
    result = {
        "has_pitfall": False,
        "file_name": file_name,
        "license_value": None,
        "source": None,
        "metadata_source_file": None,
        "is_local_file": False
    }

    if "license" not in somef_data:
        return result

    license_entries = somef_data["license"]
    if not isinstance(license_entries, list):
        return result

    metadata_sources = ["codemeta.json", "description", "composer.json", "package.json", "pom.xml", "pyproject.toml", "requirements.txt", "setup.py"]

    for entry in license_entries:
        technique = entry.get("technique", "")
        source = entry.get("source", "")

        if technique == "code_parser" or any(src in source.lower() for src in metadata_sources):
            if "result" in entry and "value" in entry["result"]:
                license_value = entry["result"]["value"]

                if is_local_file_license(license_value):
                    result["has_pitfall"] = True
                    result["license_value"] = license_value
                    result["source"] = source if source else f"technique: {technique}"
                    result["metadata_source_file"] = extract_metadata_source_filename(source)
                    result["is_local_file"] = True
                    break

    return result