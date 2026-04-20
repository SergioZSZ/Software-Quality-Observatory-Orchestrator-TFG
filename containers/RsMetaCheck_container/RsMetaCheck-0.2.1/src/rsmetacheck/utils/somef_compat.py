import copy
from typing import Dict, Any

def normalize_somef_data(somef_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes the SoMEF output data (specifically format 0.10.1+) to ensure backward compatibility
    with detectors expecting 'source' and 'technique' to be strings.
    If 'source' or 'technique' are lists, it explodes the entry into multiple single-string entries.
    """
    normalized = copy.deepcopy(somef_data)

    for key, value in normalized.items():
        if isinstance(value, list) and key not in ["somef_provenance"]:
            new_entries = []
            for entry in value:
                if isinstance(entry, dict):
                    new_entries.extend(_expand_entry(entry))
                else:
                    new_entries.append(entry)
            normalized[key] = new_entries

    return normalized

def _expand_entry(entry: Dict[str, Any]) -> list[Dict[str, Any]]:
    entries = [entry]
    
    if "technique" in entry and isinstance(entry["technique"], list):
        new_entries = []
        for e in entries:
            for tech in e["technique"]:
                ne = copy.deepcopy(e)
                ne["technique"] = tech
                new_entries.append(ne)
        entries = new_entries
        
    if "source" in entry and isinstance(entry["source"], list):
        new_entries = []
        for e in entries:
            for src in e["source"]:
                ne = copy.deepcopy(e)
                ne["source"] = src
                new_entries.append(ne)
        entries = new_entries
        
    if "result" in entry and isinstance(entry["result"], dict) and "source" in entry["result"] and isinstance(entry["result"]["source"], list):
        new_entries = []
        for e in entries:
            for src in e["result"]["source"]:
                ne = copy.deepcopy(e)
                ne["result"]["source"] = src
                new_entries.append(ne)
        entries = new_entries

    return entries
