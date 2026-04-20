import json
from pathlib import Path
from typing import Iterable, Union
from rsmetacheck.utils.pitfall_utils import extract_programming_languages
from rsmetacheck.utils.json_ld_utils import create_pitfall_jsonld, save_individual_pitfall_jsonld
from rsmetacheck.utils.somef_compat import normalize_somef_data

# Pitfalls
from rsmetacheck.scripts.pitfalls.p001 import detect_version_mismatch
from rsmetacheck.scripts.pitfalls.p002 import detect_license_template_placeholders
from rsmetacheck.scripts.pitfalls.p003 import detect_multiple_authors_single_field_pitfall
from rsmetacheck.scripts.pitfalls.p004 import detect_readme_homepage_pitfall
from rsmetacheck.scripts.pitfalls.p005 import detect_reference_publication_archive_pitfall
from rsmetacheck.scripts.pitfalls.p006 import detect_local_file_license_pitfall
from rsmetacheck.scripts.pitfalls.p007 import detect_citation_missing_reference_publication_pitfall
from rsmetacheck.scripts.pitfalls.p008 import detect_invalid_software_requirement_pitfall
from rsmetacheck.scripts.pitfalls.p009 import detect_coderepository_homepage_pitfall
from rsmetacheck.scripts.pitfalls.p010 import detect_copyright_only_license
from rsmetacheck.scripts.pitfalls.p011 import detect_issue_tracker_format_pitfall
from rsmetacheck.scripts.pitfalls.p012 import detect_outdated_download_url_pitfall
from rsmetacheck.scripts.pitfalls.p013 import detect_license_no_version_pitfall
from rsmetacheck.scripts.pitfalls.p014 import detect_bare_doi_pitfall
from rsmetacheck.scripts.pitfalls.p015 import detect_ci_404_pitfall
from rsmetacheck.scripts.pitfalls.p016 import detect_different_repository_pitfall
from rsmetacheck.scripts.pitfalls.p017 import detect_codemeta_version_mismatch_pitfall
from rsmetacheck.scripts.pitfalls.p018 import detect_raw_swhid_pitfall
from rsmetacheck.scripts.pitfalls.p019 import detect_inconsistent_author_count

# Warnings
from rsmetacheck.scripts.warnings.w001 import detect_unversioned_requirements
from rsmetacheck.scripts.warnings.w002 import detect_outdated_datemodified
from rsmetacheck.scripts.warnings.w003 import detect_dual_license_missing_codemeta_pitfall
from rsmetacheck.scripts.warnings.w004 import detect_programming_language_no_version_pitfall
from rsmetacheck.scripts.warnings.w005 import detect_multiple_requirements_string_warning
from rsmetacheck.scripts.warnings.w006 import detect_identifier_name_warning
from rsmetacheck.scripts.warnings.w007 import detect_empty_identifier_warning
from rsmetacheck.scripts.warnings.w008 import detect_author_name_list_warning
from rsmetacheck.scripts.warnings.w009 import detect_development_status_url_pitfall
from rsmetacheck.scripts.warnings.w010 import detect_git_remote_shorthand_pitfall


def detect_all_pitfalls(json_files: Iterable[Path], pitfalls_output_dir: Union[str, Path], output_file: Union[str, Path], verbose: bool = False):
    """
    Detect all software repository pitfalls in SoMEF output files using modular detectors.
    Now also generates individual JSON-LD files for each repository.
    """

    pitfalls_output_dir = Path(pitfalls_output_dir)
    pitfalls_output_dir.mkdir(exist_ok=True, parents=True)
    json_files = list(json_files)

    if not json_files:
        print("No JSON files found for analysis.")
        return

    print(f"Analyzing {len(json_files)} SoMEF JSON files...")

    results = {
        "summary": {
            "total_repositories_analyzed": 0,
            "repositories_with_target_languages": 0,
            "individual_jsonld_files_created": 0,
            "total_pitfalls_detected": 0,  # Add this
            "total_warnings_detected": 0,  # Add this
            "target_languages": ["Python", "Java", "C++", "C", "R", "Rust"],
            "evaluated_repositories": {}
        },
        "pitfalls & warnings": [
            {
                "pitfall_code": "P001",
                "pitfall_desc": "The metadata file (codemeta or other) has a version which does not correspond to the version used in the latest release",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P002",
                "pitfall_desc": "LICENSE file contains template placeholders like <program>, <year>, <name of author> that were not replaced",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P003",
                "pitfall_desc": "Metadata files have multiple authors in single field instead of a list",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P004",
                "pitfall_desc": "In codemeta.json README property pointing to their homepage/wiki instead of README file",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P005",
                "pitfall_desc": "codemeta.json referencePublication refers to software archive instead of paper",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P006",
                "pitfall_desc": "The metadata file has License pointing to a local file instead of stating the name",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P007",
                "pitfall_desc": "CITATION.cff does not have referencePublication even though it's referenced in codemeta.json",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P008",
                "pitfall_desc": "The metadata file softwareRequirement points to an invalid page",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P009",
                "pitfall_desc": "The metadata file coderepository points to their homepage",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P010",
                "pitfall_desc": "LICENSE file only contains copyright information without actual license terms",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P011",
                "pitfall_desc": "codemeta.json IssueTracker violates the expected URL format",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P012",
                "pitfall_desc": "codemeta.json downloadURL is outdated",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P013",
                "pitfall_desc": "The metadata file License does not have the specific version",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P014",
                "pitfall_desc": "codemeta.json uses bare DOIs in the identifier field instead of full https://doi.org/ URL",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P015",
                "pitfall_desc": "In codemeta.json contIntegration link returns 404",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P016",
                "pitfall_desc": "The metadata file codeRepository does not point to the same repository",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P017",
                "pitfall_desc": "codemeta.json version does not match the package's",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P018",
                "pitfall_desc": "codemeta.json Identifier uses raw SWHIDs without their resolvable URL",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "P019",
                "pitfall_desc": "Inconsistent author counts found across metadata files",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "warning_code": "W001",
                "warning_desc": "Software requirements in metadata files don't have version specifications",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "warning_code": "W002",
                "warning_desc": "The dateModified in codemeta.json is outdated compared to the actual repository last update date",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "warning_code": "W003",
                "warning_desc": "Codemeta.json repository has multiple licenses but only one is listed",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "warning_code": "W004",
                "warning_desc": "Programming languages in codemeta.json do not have versions",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "warning_code": "W005",
                "warning_desc": "The metadata file softwareRequirements have more than one req, but it's written as one string",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "warning_code": "W006",
                "warning_desc": "codemeta.json Identifier is a name instead of a valid unique identifier, but an identifier exist",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "warning_code": "W007",
                "warning_desc": "codemeta.json Identifier is empty",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "warning_code": "W008",
                "warning_desc": "The metadata file GivenName is a list instead of a string",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "W009",
                "pitfall_desc": "codemeta.json developmentStatus is a URL instead of a string",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            },
            {
                "pitfall_code": "W010",
                "pitfall_desc": "The metadata file codeRepository uses Git remote-style shorthand instead of full URL",
                "count": 0,
                "percentage": 0.0,
                "languages": {}
            }
        ]
    }

    total_pitfalls = 0
    total_warnings = 0
    total_repos = 0
    repos_with_target_languages = 0
    jsonld_files_created = 0
    pitfall_counts = [0] * 29

    pitfall_detectors = [
        (detect_version_mismatch, "P001"),  # Index 0 -> P001
        (detect_license_template_placeholders, "P002"),  # Index 1 -> P002  
        (detect_multiple_authors_single_field_pitfall, "P003"),  # Index 2 -> P003
        (detect_readme_homepage_pitfall, "P004"),  # Index 3 -> P004
        (detect_reference_publication_archive_pitfall, "P005"),  # Index 4 -> P005
        (detect_local_file_license_pitfall, "P006"),  # Index 5 -> P006
        (detect_citation_missing_reference_publication_pitfall, "P007"),  # Index 6 -> P007
        (detect_invalid_software_requirement_pitfall, "P008"),  # Index 7 -> P008
        (detect_coderepository_homepage_pitfall, "P009"),  # Index 8 -> P009
        (detect_copyright_only_license, "P010"),  # Index 9 -> P010
        (detect_issue_tracker_format_pitfall, "P011"),  # Index 10 -> P011
        (detect_outdated_download_url_pitfall, "P012"),  # Index 11 -> P012
        (detect_license_no_version_pitfall, "P013"),  # Index 12 -> P013
        (detect_bare_doi_pitfall, "P014"),  # Index 13 -> P014
        (detect_ci_404_pitfall, "P015"),  # Index 14 -> P015
        (detect_different_repository_pitfall, "P016"),  # Index 15 -> P016
        (detect_codemeta_version_mismatch_pitfall, "P017"),  # Index 16 -> P017
        (detect_raw_swhid_pitfall, "P018"),  # Index 17 -> P018
        (detect_inconsistent_author_count, "P019"),  # Index 18 -> P019
        (detect_unversioned_requirements, "W001"),  # Index 19 -> W001
        (detect_outdated_datemodified, "W002"),  # Index 20 -> W002
        (detect_dual_license_missing_codemeta_pitfall, "W003"),
        (detect_programming_language_no_version_pitfall, "W004"),  # Index 21 -> W004
        (detect_multiple_requirements_string_warning, "W005"),  # Index 22 -> W005
        (detect_identifier_name_warning, "W006"),  # Index 23 -> W006
        (detect_empty_identifier_warning, "W007"),  # Index 24 -> W007
        (detect_author_name_list_warning, "W008"),  # Index 25 -> W008
        (detect_development_status_url_pitfall, "W009"),  # Index 26 -> W009
        (detect_git_remote_shorthand_pitfall, "W010"),  # Index 27 -> W010
    ]

    for json_file in json_files:
        total_repos += 1

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                somef_data = json.load(f)

            somef_data = normalize_somef_data(somef_data)

            languages = extract_programming_languages(somef_data)

            if languages:
                repos_with_target_languages += 1

            repo_pitfall_results = []

            for idx, (detector_func, pitfall_code) in enumerate(pitfall_detectors):
                try:
                    pitfall_result = detector_func(somef_data, json_file.name)

                    pitfall_result["pitfall_code"] = pitfall_code
                    repo_pitfall_results.append(pitfall_result)

                    has_pitfall = pitfall_result.get("has_pitfall", False)
                    has_warning = pitfall_result.get("has_warning", False)
                    has_issue = has_pitfall or has_warning

                    if has_issue:
                        pitfall_counts[idx] += 1

                        if has_pitfall:
                            total_pitfalls += 1
                        if has_warning:
                            total_warnings += 1

                        if languages:
                            for lang in languages:
                                if lang in results["pitfalls & warnings"][idx]["languages"]:
                                    results["pitfalls & warnings"][idx]["languages"][lang] += 1
                                else:
                                    results["pitfalls & warnings"][idx]["languages"][lang] = 1

                        issue_type = "Pitfall" if pitfall_result.get("has_pitfall", False) else "Warning"
                        print(f"{pitfall_code} - {issue_type} found in {json_file.name}")

                except Exception as e:
                    print(f"Error running {pitfall_code} detector on {json_file.name}: {e}")
                    continue

            try:
                has_any_issue = any(
                    result.get("has_pitfall", False) or result.get("has_warning", False)
                    for result in repo_pitfall_results
                )

                if has_any_issue or verbose:
                    jsonld_data = create_pitfall_jsonld(somef_data, repo_pitfall_results, json_file.name, verbose=verbose)
                    saved_file = save_individual_pitfall_jsonld(jsonld_data, pitfalls_output_dir, json_file.name)

                    if saved_file:
                        jsonld_files_created += 1
                        print(f"Created JSON-LD file: {saved_file}")

            except Exception as e:
                print(f"Error creating JSON-LD for {json_file.name}: {e}")

            try:
                repo_name = json_file.name
                if "full_name" in somef_data and somef_data["full_name"]:
                    for item in somef_data["full_name"]:
                        if "result" in item and "value" in item["result"]:
                            repo_name = item["result"]["value"]
                            break
                            
                repo_url = "Unknown"
                if "code_repository" in somef_data and somef_data["code_repository"]:
                    for item in somef_data["code_repository"]:
                        if "result" in item and "value" in item["result"]:
                            repo_url = item["result"]["value"]
                            break
                
                from rsmetacheck.utils.json_ld_utils import fetch_latest_commit_id
                commit_id = fetch_latest_commit_id(repo_url)
                results["summary"]["evaluated_repositories"][repo_name] = {
                    "url": repo_url,
                    "commit_id": commit_id
                }
            except Exception as e:
                print(f"Error extracting commit ID for summary for {json_file.name}: {e}")

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file {json_file}: {e}")
            continue
        except Exception as e:
            print(f"Error processing file {json_file}: {e}")
            continue

    results["summary"]["total_repositories_analyzed"] = total_repos
    results["summary"]["repositories_with_target_languages"] = repos_with_target_languages
    results["summary"]["individual_jsonld_files_created"] = jsonld_files_created
    results["summary"]["total_pitfalls_detected"] = total_pitfalls
    results["summary"]["total_warnings_detected"] = total_warnings

    for i, count in enumerate(pitfall_counts):
        pitfall_code_str = pitfall_detectors[i][1]
        results["pitfalls & warnings"][i]["pitfall"] = f"https://w3id.org/rsmetacheck/catalog/#{pitfall_code_str}"
        results["pitfalls & warnings"][i]["count"] = count
        if total_repos > 0:
            results["pitfalls & warnings"][i]["percentage"] = round((count / total_repos) * 100, 2)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n=== PITFALL/WARNING DETECTION COMPLETE ===")
        print(f"Total repositories analyzed: {total_repos}")
        print(f"Repositories with target languages: {repos_with_target_languages}")
        print(f"Individual JSON-LD files created: {jsonld_files_created}")
        print(f"JSON-LD files saved to: {pitfalls_output_dir}")

        for i, (_, pitfall_code) in enumerate(pitfall_detectors):
            print(f"{pitfall_code}: {pitfall_counts[i]} ({results['pitfalls & warnings'][i]['percentage']}%)")

        print(f"Summary results saved to: {output_file}")

    except Exception as e:
        print(f"Error writing output file: {e}")


def main(input_dir=None, somef_json_paths=None, pitfalls_dir=None, analysis_output=None, verbose=False):
    """
    Main function to run all pitfall detections.

    Args:
        input_dir (str|Path, optional): Directory containing SoMEF outputs.
        somef_json_paths (Iterable[Path], optional): Explicit list of SoMEF output JSON files.
        pitfalls_dir (str|Path, optional): Directory to save pitfall JSON-LD files.
        analysis_output (str|Path, optional): Path to save summary results JSON.
        verbose (bool, optional): Include both detected AND undetected pitfalls in JSON-LD.

    Note: Provide either input_dir OR somef_json_paths, not both.
          If both are provided, somef_json_paths takes precedence.
    """
    project_root = Path.cwd()

    pitfalls_directory = Path(pitfalls_dir) if pitfalls_dir else project_root / "pitfalls_outputs"
    output_file = Path(analysis_output) if analysis_output else project_root / "analysis_results.json"

    if somef_json_paths:
        json_files = [Path(p) for p in somef_json_paths]
        print(f"Using {len(json_files)} explicitly provided JSON files")
    elif input_dir:
        input_dir = Path(input_dir)
        if not input_dir.exists():
            print(f"Error: Directory not found: {input_dir}")
            return
        json_files = list(input_dir.glob("*.json"))
        print(f"Found {len(json_files)} JSON files in {input_dir}")
    else:
        print("Error: No input directory or JSON file list provided.")
        return

    if not json_files:
        print("No JSON files found for analysis.")
        return

    detect_all_pitfalls(json_files, pitfalls_directory, output_file, verbose)

if __name__ == "__main__":
    main()
