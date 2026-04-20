from typing import Dict, List, Tuple
from rsmetacheck.utils.pitfall_utils import extract_metadata_source_filename


def extract_authors_from_somef(somef_data: Dict) -> List[Dict[str, any]]:
    """
    Extract all author entries from different sources in SoMEF output.
    Returns a list of dicts with source and author count information.
    """
    if "author" not in somef_data:
        return []

    author_entries = somef_data["author"]
    if not isinstance(author_entries, list):
        return []

    results = []

    for entry in author_entries:
        if "source" not in entry or "result" not in entry:
            continue

        source = entry["source"]
        result = entry["result"]

        author_count = 0
        authors_list = []

        if isinstance(result, list):
            author_count = len(result)
            authors_list = [get_author_identifier(author) for author in result]
        elif isinstance(result, dict):
            author_count = 1
            authors_list = [get_author_identifier(result)]
        elif isinstance(result, str): 
            author_count = 1
            authors_list = [get_author_identifier(result)]

        if author_count > 0:
            results.append({
                "source": source,
                "source_file": extract_metadata_source_filename(source),
                "author_count": author_count,
                "authors": authors_list
            })

    return results


def get_author_identifier(author: any) -> str:
    """
    Extract a string identifier for an author from various formats.
    """
    if isinstance(author, str):
        return author.strip()
    elif isinstance(author, dict):
        if "name" in author:
            return str(author["name"]).strip()
        elif "value" in author:
            return str(author["value"]).strip()
        elif "email" in author:
            return str(author["email"]).strip()
        else:
            return str(author)
    else:
        return str(author)


def find_author_count_inconsistencies(author_sources: List[Dict]) -> Tuple[bool, List[Dict]]:
    """
    Check if there are inconsistencies in author counts across different sources.
    Returns (has_inconsistency, inconsistency_details).
    """
    if len(author_sources) < 2:
        return False, []

    counts = {}
    for source_info in author_sources:
        count = source_info["author_count"]
        if count not in counts:
            counts[count] = []
        counts[count].append(source_info)

    if len(counts) <= 1:
        return False, []

    inconsistencies = []
    sorted_counts = sorted(counts.keys())

    for i in range(len(sorted_counts)):
        lower_count = sorted_counts[i]
        for j in range(i + 1, len(sorted_counts)):
            higher_count = sorted_counts[j]

            for lower_source in counts[lower_count]:
                for higher_source in counts[higher_count]:
                    inconsistencies.append({
                        "source_with_fewer": lower_source["source_file"],
                        "source_with_fewer_full": lower_source["source"],
                        "fewer_count": lower_count,
                        "fewer_authors": lower_source["authors"],
                        "source_with_more": higher_source["source_file"],
                        "source_with_more_full": higher_source["source"],
                        "more_count": higher_count,
                        "more_authors": higher_source["authors"],
                        "difference": higher_count - lower_count
                    })

    return len(inconsistencies) > 0, inconsistencies


def detect_inconsistent_author_count(somef_data: Dict, file_name: str) -> Dict:
    """
    Detect inconsistent author counts across different metadata files.
    Returns detection result with warning info.
    """
    result = {
        "has_warning": False,
        "file_name": file_name,
        "author_sources": [],
        "inconsistencies": [],
        "total_sources": 0,
        "min_author_count": 0,
        "max_author_count": 0
    }

    author_sources = extract_authors_from_somef(somef_data)

    if not author_sources:
        return result

    result["author_sources"] = author_sources
    result["total_sources"] = len(author_sources)

    counts = [src["author_count"] for src in author_sources]
    result["min_author_count"] = min(counts)
    result["max_author_count"] = max(counts)

    has_inconsistency, inconsistencies = find_author_count_inconsistencies(author_sources)

    if has_inconsistency:
        result["has_warning"] = True
        result["inconsistencies"] = inconsistencies

    return result