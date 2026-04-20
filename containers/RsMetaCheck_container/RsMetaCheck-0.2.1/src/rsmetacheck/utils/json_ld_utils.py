import json
import re
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from urllib.error import HTTPError, URLError


def _fetch_gitlab_commit_id(host: str, project_path: str) -> str:
    """
    Fetch the latest commit ID from a GitLab.com instance.

    Uses the GitLab API v4 endpoint with a URL-encoded project path so that
    namespace separators ('/'→'%2F') are transmitted correctly.
    Returns the commit ID string or 'Unknown' if unreachable or not found.
    """
    encoded_path = urllib.parse.quote(project_path, safe="")
    api_url = f"{host}/api/v4/projects/{encoded_path}/repository/commits?per_page=1"
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("id", "Unknown")
    except (URLError, HTTPError, json.JSONDecodeError):
        pass
    return "Unknown"


def fetch_latest_commit_id(repo_url: str) -> str:
    """
    Attempts to fetch the latest commit ID for a given repository URL.
    Supports GitHub, GitLab.com (HTTPS only).
    Returns the commit ID string or 'Unknown' if not found.
    """
    if not repo_url or repo_url == "Unknown":
        return "Unknown"
        
    if "github.com" in repo_url:
        match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
        if match:
            owner, repo = match.groups()
            if repo.endswith('.git'):
                repo = repo[:-4]
            
            api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/HEAD"
            try:
                req = urllib.request.Request(
                    api_url, 
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    return data.get('sha', 'Unknown')
            except (URLError, HTTPError, json.JSONDecodeError):
                pass

    elif repo_url.startswith("https://"):
        # Handles gitlab.com and any self-hosted GitLab instance.
        # The GitLab API v4 is tried; a failed request returns 'Unknown' gracefully.
        parsed = urllib.parse.urlparse(repo_url)
        host = f"{parsed.scheme}://{parsed.netloc}"
        project_path = parsed.path.strip("/")
        if project_path.endswith(".git"):
            project_path = project_path[:-4]
        if project_path:
            return _fetch_gitlab_commit_id(host, project_path)

    return "Unknown"


def extract_software_info_from_somef(somef_data: Dict) -> Dict:
    """
    Extract software information from SoMEF data for the assessedSoftware section.
    """
    software_info = {
        "@type": "schema:SoftwareApplication",
        "name": "Unknown",
        "softwareVersion": "Unknown",
        "url": "Unknown",
    }

    if "full_name" in somef_data:
        for entry in somef_data["full_name"]:
            if "result" in entry and "value" in entry["result"]:
                software_info["name"] = entry["result"]["value"]
                break

    if "releases" in somef_data:
        releases = somef_data["releases"]
        if isinstance(releases, list) and len(releases) > 0:
            latest_release = releases[0]
            if isinstance(latest_release, dict):
                if "tag" in latest_release:
                    software_info["softwareVersion"] = latest_release["tag"]
                elif "result" in latest_release and isinstance(latest_release["result"], dict):
                    if "tag" in latest_release["result"]:
                        software_info["softwareVersion"] = latest_release["result"]["tag"]

    if "code_repository" in somef_data:
        for entry in somef_data["code_repository"]:
            if "result" in entry and "value" in entry["result"]:
                software_info["url"] = entry["result"]["value"]
                break

    if "identifier" in somef_data:
        for entry in somef_data["identifier"]:
            if "result" in entry and "value" in entry["result"]:
                identifier_value = entry["result"]["value"]
                if identifier_value.startswith("https://doi.org/"):
                    software_info["schema:identifier"] = {"@id": identifier_value}
                elif identifier_value.startswith("10."):
                    software_info["schema:identifier"] = {"@id": f"https://doi.org/{identifier_value}"}
                break

    # Add commit ID
    software_info["commit_id"] = fetch_latest_commit_id(software_info.get("url", "Unknown"))

    return software_info


def get_pitfall_description(pitfall_code: str) -> str:
    """
    Get the description of how a given pitfall/warning is detected.
    """
    descriptions = {
        # Pitfalls (P001-P018)
        "P001": "Compares the version found in the metadata file with the latest repository release tag.",
        "P002": "Searches for common template placeholders (e.g., <program>, <year>) within the LICENSE file.",
        "P003": "Analyzes author fields in metadata to see if multiple distinct authors are merged into a single string.",
        "P004": "Checks the README property in codemeta.json to see if it links to a homepage or wiki rather than the actual README file.",
        "P005": "Checks the referencePublication in codemeta.json to verify it points to a paper rather than a software archive.",
        "P006": "Checks if the License property in the metadata file points to a local file path instead of an SPDX license identifier.",
        "P007": "Checks CITATION.cff for a referencePublication when codemeta.json includes one but the CFF file does not.",
        "P008": "Validates the URLs provided in the softwareRequirement field to ensure they return a successful HTTP status.",
        "P009": "Checks if the codeRepository field points to a project homepage rather than the actual source code repository.",
        "P010": "Analyzes the LICENSE file to determine if it only contains a copyright notice without any actual usage terms.",
        "P011": "Validates the IssueTracker URL format in codemeta.json against expected provider patterns (e.g., GitHub issues).",
        "P012": "Validates the downloadURL in codemeta.json to ensure the link is active and valid.",
        "P013": "Checks if the declared License in the metadata lacks a specific version number.",
        "P014": "Checks the identifier field in codemeta.json to see if it uses a bare DOI string instead of a full HTTPS URL.",
        "P015": "Sends a request to the contIntegration URL in codemeta.json to verify it does not return a 404 Not Found error.",
        "P016": "Compares the origin repository URL with the codeRepository URL in the metadata file to ensure they match.",
        "P017": "Compares the version field in codemeta.json against the package manager version.",
        "P018": "Checks the Identifier field in codemeta.json to see if it contains raw SWHIDs instead of their resolvable URLs.",

        # Warnings (W001-W010)
        "W001": "Analyzes software requirements in metadata to see if they lack explicit version constraints.",
        "W002": "Compares the dateModified field against the last updated date of the actual repository.",
        "W003": "Detects if multiple distinct licenses are found in the repository but only a single license is declared in codemeta.json.",
        "W004": "Checks programming language declarations in codemeta.json to see if they lack specific version numbers.",
        "W005": "Checks if the softwareRequirements field contains multiple dependencies combined into a single continuous string.",
        "W006": "Checks if the existing identifier in codemeta.json is a plain name rather than an actual unique identifier (URL).",
        "W007": "Checks if the Identifier field in codemeta.json is empty or completely missing.",
        "W008": "Checks the GivenName field in the metadata file to ensure it is stored as a simple string rather than a parsed list.",
        "W009": "Checks if the developmentStatus in codemeta.json is provided as a URL instead of a descriptive string.",
        "W010": "Checks if the codeRepository URL uses Git remote-style shorthand (e.g., git@github.com:...) instead of a full HTTPS URL.",
    }

    return descriptions.get(pitfall_code, f"Detection process for {pitfall_code}")

def extract_metadata_source(pitfall_result: Dict) -> str:
    """
    Extract the metadata source from a pitfall result.
    Returns the filename part of the source path, or a default value if not present.
    """
    if 'metadata_source_file' in pitfall_result and pitfall_result['metadata_source_file']:
        return pitfall_result['metadata_source_file']

    # Fallback to the old method
    metadata_source = pitfall_result.get('metadata_source', 'metadata files')
    # Extract just the filename from the source path if it's a full path
    if '/' in metadata_source or '\\' in metadata_source:
        metadata_source = metadata_source.split('/')[-1].split('\\')[-1]
    return metadata_source


def extract_metadata_source_filename(source_path: str) -> str:
    """
    Extract the specific metadata file name from a source path.
    This function is reusable for all pitfall detectors that need to identify metadata sources.

    Args:
        source_path: The full source path from SoMEF data

    Returns:
        The filename (e.g., "DESCRIPTION", "codemeta.json") or "metadata files" as fallback
    """
    if not source_path:
        return "metadata files"

    # Define metadata file patterns to look for
    metadata_files = ["codemeta.json", "DESCRIPTION", "composer.json", "package.json",
                      "pom.xml", "pyproject.toml", "requirements.txt", "setup.py"]

    # Check for exact filename matches first
    for meta_file in metadata_files:
        if meta_file in source_path:
            return meta_file

    # If no specific metadata file found, extract filename from path
    if '/' in source_path or '\\' in source_path:
        filename = source_path.split('/')[-1].split('\\')[-1]
        # Check if the extracted filename is a known metadata file
        if filename in metadata_files or any(
                ext in filename.lower() for ext in ['.json', '.xml', '.yml', '.toml', '.txt']):
            return filename

    return "metadata files"


def format_evidence_text(pitfall_code: str, pitfall_result: Dict) -> str:
    """
    Format evidence text based on pitfall type and result data for ALL pitfalls and warnings.
    """
    evidence_base = f"{pitfall_code} detected: "

    # Pitfalls
    if pitfall_code == "P001":
        if "metadata_version" in pitfall_result and "release_version" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            metadata_version = pitfall_result.get('metadata_version') or 'unknown'
            release_version = pitfall_result.get('release_version') or 'unknown'
            return f"{evidence_base}{metadata_source} version '{metadata_version}' does not match release version '{release_version}'"

    elif pitfall_code == "P002":
        if pitfall_result.get("placeholders_found"):
            return f"{evidence_base}LICENSE file contains unreplaced template placeholders"
        return f"{evidence_base}LICENSE file contains template placeholders that were not replaced"

    elif pitfall_code == "P003":
        if "author_value" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            author_value = pitfall_result.get('author_value') or 'unknown'
            return f"{evidence_base}{metadata_source} Multiple authors found in single field: '{author_value}'"

    elif pitfall_code == "P004":
        if "readme_url" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            readme_url = pitfall_result.get('readme_url') or 'unknown URL'
            return f"{evidence_base}{metadata_source} README property points to homepage/wiki instead of README file: {readme_url}"

    elif pitfall_code == "P005":
        if "reference_url" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            reference_url = pitfall_result.get('reference_url') or 'unknown URL'
            return f"{evidence_base}{metadata_source} Reference publication points to software archive instead of paper: {reference_url}"

    elif pitfall_code == "P006":
        if "license_value" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            license_value = pitfall_result.get('license_value') or 'unknown'
            return f"{evidence_base}{metadata_source} License points to local file instead of license name: '{license_value}'"

    elif pitfall_code == "P007":
        metadata_source = extract_metadata_source(pitfall_result)
        return f"{evidence_base}{metadata_source} exists but does not contain referencePublication while codemeta.json references it"

    elif pitfall_code == "P008":
        if "invalid_urls" in pitfall_result:
            invalid_urls = pitfall_result["invalid_urls"]
            if isinstance(invalid_urls, list) and len(invalid_urls) > 0:
                urls = []
                for url_info in invalid_urls:
                    if isinstance(url_info, dict) and "url" in url_info and url_info["url"]:
                        urls.append(str(url_info["url"]))
                    elif isinstance(url_info, str) and url_info:
                        urls.append(url_info)

                if urls:
                    metadata_source = extract_metadata_source(pitfall_result)
                    url_list = ', '.join(urls[:3])
                    return f"{evidence_base}{metadata_source} Software requirements contain invalid URLs: {url_list}{'...' if len(urls) > 3 else ''}"
        return f"{evidence_base}Software requirements contain invalid URLs"

    elif pitfall_code == "P009":
        if "repository_url" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            repository_url = pitfall_result.get('repository_url') or 'unknown URL'
            return f"{evidence_base}{metadata_source} codeRepository points to homepage instead of repository: {repository_url}"

    elif pitfall_code == "P010":
        metadata_source = extract_metadata_source(pitfall_result)
        if metadata_source == "metadata files":
            metadata_source = "LICENSE file"
        return f"{evidence_base}{metadata_source} only contains copyright information without actual license terms"

    elif pitfall_code == "P011":
        if "issue_url" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            issue_url = pitfall_result.get('issue_url') or 'unknown URL'
            return f"{evidence_base}{metadata_source} IssueTracker URL violates expected format: {issue_url}"

    elif pitfall_code == "P012":
        if "download_url" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            download_url = pitfall_result.get('download_url') or 'unknown URL'
            return f"{evidence_base}{metadata_source} downloadURL is outdated or invalid: {download_url}"

    elif pitfall_code == "P013":
        if "license_value" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            license_value = pitfall_result.get('license_value') or 'unknown'
            return f"{evidence_base}{metadata_source} License does not specify version: '{license_value}'"

    elif pitfall_code == "P014":
        if "identifier_value" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            identifier_value = pitfall_result.get('identifier_value') or 'unknown'
            return f"{evidence_base}{metadata_source} Identifier uses bare DOI instead of full URL: '{identifier_value}'"

    elif pitfall_code == "P015":
        if "ci_url" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            status = pitfall_result.get("status_code") or "unknown"
            ci_url = pitfall_result.get('ci_url') or 'unknown URL'
            return f"{evidence_base}{metadata_source} Continuous integration URL returns {status}: {ci_url}"

    elif pitfall_code == "P016":
        if "github_api_url" in pitfall_result:
            github_api_url = pitfall_result.get('github_api_url') or 'unknown URL'
            different_urls = pitfall_result.get("different_urls", [])
            metadata_source = "metadata files"
            if different_urls and isinstance(different_urls, list) and len(different_urls) > 0:
                source_path = different_urls[0].get("source", "")
                metadata_source = extract_metadata_source_filename(source_path)
            elif "source" in pitfall_result:
                metadata_source = extract_metadata_source(pitfall_result)
            return f"{evidence_base}{metadata_source} codeRepository points to different repository: {github_api_url}"

    elif pitfall_code == "P017":
        if "codemeta_version" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            codemeta_version = pitfall_result.get('codemeta_version') or 'unknown'
            
            other_source = "package version"
            mismatches = pitfall_result.get("mismatched_versions", [])
            if mismatches and isinstance(mismatches, list) and len(mismatches) > 0:
                raw_source = mismatches[0].get("source", "")
                other_version_val = mismatches[0].get("version", "unknown")
                other_source = f"version '{other_version_val}' in {extract_metadata_source_filename(raw_source)}"
                
            return f"{evidence_base}{metadata_source} version '{codemeta_version}' does not match {other_source}"

    elif pitfall_code == "P018":
        if "identifier_value" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            identifier_value = pitfall_result.get('identifier_value') or 'unknown'
            return f"{evidence_base}{metadata_source} Identifier uses raw SWHID without resolvable URL: '{identifier_value}'"

    elif pitfall_code == "P019":
        if "inconsistencies" in pitfall_result:
            inconsistency = pitfall_result["inconsistencies"][0]
            source_fewer = inconsistency.get('source_with_fewer', 'unknown')
            count_fewer = inconsistency.get('fewer_count', 0)
            source_more = inconsistency.get('source_with_more', 'unknown')
            count_more = inconsistency.get('more_count', 0)
            return f"{evidence_base}Author count mismatch: {source_fewer} has {count_fewer} while {source_more} has {count_more}"
        return f"{evidence_base}Inconsistent author counts found across metadata files"

    # Warnings
    elif pitfall_code == "W001":
        if "unversioned_requirements" in pitfall_result:
            reqs = pitfall_result["unversioned_requirements"]
            metadata_source = extract_metadata_source(pitfall_result)
            if isinstance(reqs, list) and len(reqs) > 0:
                clean_reqs = [str(req) for req in reqs if req is not None]
                if clean_reqs:
                    req_list = ', '.join(clean_reqs)
                    return f"{evidence_base}{metadata_source} contains software requirements without versions: {req_list}"
        return f"{evidence_base}Software requirements found without version specifications"

    elif pitfall_code == "W002":
        if "codemeta_date_parsed" in pitfall_result and "github_api_date_parsed" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            codemeta_date = pitfall_result.get('codemeta_date_parsed') or 'unknown'
            github_date = pitfall_result.get('github_api_date_parsed') or 'unknown'
            return f"{evidence_base}{metadata_source} dateModified '{codemeta_date}' is outdated compared to repository date '{github_date}'"
        return f"{evidence_base}dateModified in metadata is outdated compared to actual repository last update"

    elif pitfall_code == "W003":
        if "dual_license_source" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            dual_license_source = pitfall_result.get('dual_license_source') or 'unknown'
            return f"{evidence_base}Repository has multiple licenses but {metadata_source} only lists one. Found in: {dual_license_source}"
        return f"{evidence_base}Repository has multiple licenses but metadata only has one listed"

    elif pitfall_code == "W004":
        if "programming_languages_without_version" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            langs = pitfall_result["programming_languages_without_version"]
            if isinstance(langs, list) and len(langs) > 0:
                clean_langs = [str(lang) for lang in langs if lang is not None]
                if clean_langs:
                    return f"{evidence_base}{metadata_source} Programming languages without versions: {', '.join(clean_langs)}"
        return f"{evidence_base}Programming languages in metadata do not have version specifications"

    elif pitfall_code == "W005":
        if "requirement_string" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            requirements_string = pitfall_result.get('requirement_string') or 'unknown'
            return f"{evidence_base}{metadata_source} Multiple requirements written as single string: '{requirements_string}'"

    elif pitfall_code == "W006":
        if "codemeta_identifier" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            identifier = pitfall_result.get('codemeta_identifier') or 'unknown'
            return f"{evidence_base}{metadata_source} Identifier is a name instead of valid unique identifier: '{identifier}'"

    elif pitfall_code == "W007":
        metadata_source = extract_metadata_source(pitfall_result)
        return f"{evidence_base}{metadata_source} identifier field is empty or missing"

    elif pitfall_code == "W008":
        if "author_value" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            author_value = pitfall_result.get('author_value') or 'unknown'
            return f"{evidence_base}{metadata_source} GivenName is a list instead of string: {author_value}"

    elif pitfall_code == "W009":
        if "development_status" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            development_status = pitfall_result.get('development_status') or 'unknown'
            return f"{evidence_base}{metadata_source} developmentStatus is a URL instead of status string: {development_status}"

    elif pitfall_code == "W010":
        if "repository_url" in pitfall_result:
            metadata_source = extract_metadata_source(pitfall_result)
            repository_url = pitfall_result.get('repository_url') or 'unknown URL'
            return f"{evidence_base}{metadata_source} codeRepository uses Git shorthand instead of full URL: '{repository_url}'"

    # Default fallback evidence
    file_name = pitfall_result.get('file_name') or 'unknown file'
    return f"{evidence_base}Issue detected in {file_name}"


def get_pitfall_category(pitfall_code: str) -> str:
    """
    Determine the category for assessesIndicator based on pitfall description.
    Returns 'codemeta', 'metadatafile', or 'license'
    """
    categories = {
        # Pitfalls
        "P001": "metadatafile",  # metadata file version mismatch
        "P002": "license",  # LICENSE file placeholders
        "P003": "metadatafile",  # metadata file multiple authors
        "P004": "codemeta",  # codemeta.json README property
        "P005": "codemeta",  # codemeta.json referencePublication
        "P006": "metadatafile",  # metadata file License pointing to local file
        "P007": "codemeta",  # CITATION.cff vs codemeta.json
        "P008": "metadatafile",  # metadata file softwareRequirement invalid page
        "P009": "metadatafile",  # metadata file coderepository homepage
        "P010": "license",  # LICENSE file copyright only
        "P011": "codemeta",  # codemeta.json IssueTracker
        "P012": "codemeta",  # codemeta.json downloadURL
        "P013": "metadatafile",  # metadata file License version
        "P014": "codemeta",  # codemeta.json bare DOIs
        "P015": "codemeta",  # codemeta.json contIntegration 404
        "P016": "metadatafile",  # metadata file codeRepository different repo
        "P017": "codemeta",  # codemeta.json version mismatch
        "P018": "codemeta",  # codemeta.json raw SWHIDs
        "P019": "metadatafile",  # inconsistent author counts

        # Warnings
        "W001": "metadatafile",  # metadata file requirements
        "W002": "codemeta",  # codemeta.json dateModified
        "W003": "codemeta",  # codemeta.json dual license
        "W004": "codemeta",  # codemeta.json programming languages
        "W005": "metadatafile",  # metadata file softwareRequirements
        "W006": "codemeta",  # codemeta.json Identifier name
        "W007": "codemeta",  # codemeta.json Identifier empty
        "W008": "metadatafile",  # metadata file GivenName list
        "W009": "codemeta",  # codemeta.json developmentStatus
        "W010": "metadatafile",  # metadata file codeRepository shorthand
    }

    return categories.get(pitfall_code, "metadatafile")


def get_suggestion_text(pitfall_code: str, pitfall_result: Dict = None, somef_data: Dict = None) -> str:
    """
    Adds the suggestions depending on the Pitfall/Warning, dynamically populated if data is provided.
    """
    if pitfall_result is None:
        pitfall_result = {}
    if somef_data is None:
        somef_data = {}

    github_api_repo = None
    if "code_repository" in somef_data:
        for entry in somef_data["code_repository"]:
            if entry.get("technique") == "GitHub_API" and "result" in entry and "value" in entry["result"]:
                github_api_repo = entry["result"]["value"]
                break

    if pitfall_code == "P001":
        latest = pitfall_result.get("release_version")
        if latest:
            return f"Ensure the version in your metadata matches the latest official release ({latest}). Keeping these synchronized avoids confusion for users and improves reproducibility."
    elif pitfall_code == "P003":
        author_val = pitfall_result.get("author_value")
        if author_val and isinstance(author_val, str) and ("and" in author_val or "," in author_val):
            import re
            parts = [p.strip() for p in re.split(r'\s+and\s+|,', author_val) if p.strip()]
            if len(parts) > 1:
                return f'You should separate multiple authors into a structured list. For example: {parts}'
    
    elif pitfall_code == "P004":
        good_readme = None
        if "readme_url" in somef_data:
            for entry in somef_data["readme_url"]:
                val = entry.get("result", {}).get("value", "")
                if val and ("blob" in val.lower() or "readme.md" in val.lower() or "raw" in val.lower()):
                    good_readme = val
                    break
        if good_readme:
            return f"Update the README property so it points directly to your actual README file ({good_readme}) instead of your homepage."
    
    elif pitfall_code == "P007":
        codemeta_link = None
        if "reference_publication" in somef_data:
            for entry in somef_data["reference_publication"]:
                if "codemeta.json" in entry.get("source", ""):
                    codemeta_link = entry.get("result", {}).get("value", "")
                    break
        if codemeta_link:
            return f"Add a referencePublication field with the related DOI or citation entry ({codemeta_link}) to your CITATION.cff."

    elif pitfall_code == "P009":
        if github_api_repo:
            return f"You need to update the codeRepository field to point directly to your repository's source code ({github_api_repo}) instead of a homepage."

    elif pitfall_code == "P011":
        issue_url = pitfall_result.get("issue_url")
        if issue_url:
            import re
            match = re.search(r'https?://[^\s,]+', issue_url)
            if match:
                extracted_url = match.group(0)
                return f"You need to correct the issue tracker URL. Consider using the extracted link: {extracted_url}"
            return f"You need to correct the issue tracker URL ({issue_url}) so it follows a valid format, such as https://github.com/user/repo/issues."

    elif pitfall_code == "P012":
        download_url = pitfall_result.get("download_url")
        if download_url:
            return f"You need to update the downloadURL field ({download_url}) to point to your latest release or current distribution source."

    elif pitfall_code == "P014":
        identifier = pitfall_result.get("identifier_value", "")
        if identifier and isinstance(identifier, str):
            import re
            cleaned_id = re.sub(r'^doi:', '', identifier, flags=re.IGNORECASE).replace('https://doi.org/', '')
            if cleaned_id.startswith('10.'):
                return f"You should include the full DOI URL form in your metadata (e.g., https://doi.org/{cleaned_id})"

    elif pitfall_code == "P016":
        if github_api_repo:
            return f"Make sure that the codeRepository URL in your metadata exactly matches the repository hosting your source code ({github_api_repo})."

    elif pitfall_code == "P017":
        if github_api_repo:
            return f"You need to synchronize all version references across metadata and build configuration files. (Repository matches github API: {github_api_repo})"

    elif pitfall_code == "P018":
        identifier = pitfall_result.get("identifier_value", "")
        if identifier and isinstance(identifier, str) and identifier.startswith("swh:"):
            return f"Always use the full resolvable SWHID URL (e.g., https://archive.softwareheritage.org/{identifier})."

    elif pitfall_code == "W002":
        github_date = pitfall_result.get("github_api_date_parsed")
        if github_date:
            return f"The data in the metadata file should be updated to be aligned with the date of the latest release ({github_date})."

    elif pitfall_code == "W003":
        found_license = None
        if "license" in somef_data:
            for entry in somef_data["license"]:
                src = entry.get("source", "")
                if isinstance(src, list):
                    src = src[0] if src else ""
                src_str = str(src).lower()
                tech = entry.get("technique", "")
                is_file_search = ("license" in src_str or tech == "file_exploration")
                if is_file_search:
                    val = entry.get("result", {}).get("value")
                    spdx = entry.get("result", {}).get("spdx_id")
                    name = entry.get("result", {}).get("name")
                    found_license = spdx or name or (val if val and len(str(val)) < 50 else None)
                    if found_license:
                        break
        if found_license:
            return f"Use the LICENSE that is stated in your repository ({found_license}) instead."

    elif pitfall_code == "W004":
        if "programming_languages" in somef_data:
            valid_langs = []
            for entry in somef_data["programming_languages"]:
                res = entry.get("result", {})
                name = res.get("name")
                ver = res.get("version")
                if name and ver:
                    valid_langs.append(f"{name} ({ver})")
            if valid_langs:
                langs_str = ", ".join(valid_langs)
                return f"Specify version numbers for your programming languages like found in other sources: {langs_str}."

    elif pitfall_code == "W005":
        reqs = pitfall_result.get("requirement_string", "")
        if reqs and isinstance(reqs, str):
            proper = "', '".join([r.strip() for r in reqs.replace(';', ',').split(',') if r.strip()])
            if proper:
                return f"Rewrite your dependencies as a proper list (e.g., ['{proper}']), with each item separated and preferably with their versions."

    elif pitfall_code == "W006":
        other_id = pitfall_result.get("other_identifier")
        if other_id:
            return f"You should replace plain name in your identifier field with persistent identifiers such as {other_id} to improve discoverability."

    elif pitfall_code == "W008":
        author_val = pitfall_result.get("author_value", "")
        if author_val:
            import re
            list_content = re.findall(r"\[(.*?)\]", str(author_val))
            if list_content and len(list_content) > 0 and "," in list_content[0]:
                parts = [p.strip().strip("'\"") for p in list_content[0].split(',')]
                if parts:
                    example = "{" + f'"@type": "Person", "givenName": "{parts[0]}", "familyName": "..."' + "}"
                    return f"Ensure givenName is a single string per person. For example: {example}."

    elif pitfall_code == "W010":
        if github_api_repo:
            return f"You should replace the remote-style syntax with a full web-accessible URL (e.g., {github_api_repo})."

    suggestions = {
        # This works as fallback in case the dynamic suggestions does not find the necessary metadata in SoMEF report
        # Pitfalls
        "P001": "Ensure the version in your metadata matches the latest official release. Keeping these synchronized avoids confusion for users and improves reproducibility.",
        "P002": "Update the copyright section with accurate names, organizations, and the current year. Personalizing this section ensures clarity and legal accuracy.",
        "P003": "You should separate multiple authors into a structured list. This allows tools and citation systems to correctly identify and credit each contributor.",
        "P004": "Update the README property so it points directly to your actual README file instead of your homepage. This helps ensure users and automated tools can access your project documentation easily.",
        "P005": "Ensure that the referencePublication field points to the scholarly paper describing the software, not to a software archive or repository entry.",
        "P006": "You need to replace local file paths with recognized SPDX license identifiers, such as MIT or GPL-3.0-only in URL form. This ensures your license can be correctly detected by automated tools.",
        "P007": "Add a referencePublication field with the related DOI or citation entry to your CITATION.cff. This will help link your work to its scholarly references.",
        "P008": "Verify and update any dependency links to ensure they lead to valid and accessible pages.",
        "P009": "You need to update the codeRepository field to point directly to your repository's source code instead of a homepage. Accurate links improve traceability and user access.",
        "P010": "You need to include the complete text of a recognized license such as MIT, Apache 2.0, or GPL. A full license clarifies rights and usage conditions for others",
        "P011": "You need to correct the issue tracker URL so it follows a valid format, such as https://github.com/user/repo/issues. Proper links help users engage with your development process.",
        "P012": "You need to update the downloadURL field to point to your latest release or current distribution source. Outdated links can mislead users or cause failed installations.",
        "P013": "You should declare the specific version of the license using a recognized SPDX identifier. For example, use 'GPL-3.0-only' or 'GPL-2.0-or-later' instead of simply 'GPL'",
        "P014": "You should include the full DOI URL form in your metadata (e.g., https://doi.org/XX.XXXX/zenodo.XXXX)",
        "P015": "You need to update the outdated URLs to point to the current CI platform, or remove the property if no active CI is in place. A good practice would be to periodically test all external links, especially those related to CI or build status.",
        "P016": "Make sure that the codeRepository URL in your metadata exactly matches the repository hosting your source code.",
        "P017": "You need to synchronize all version references across metadata and build configuration files.",
        "P018": "Always use the full resolvable SWHID URL (e.g., https://archive.softwareheritage.org/swh:1:dir:abcd.../). This will ensure that both humans and machines can access the archived software snapshot directly",
        "P019": "Ensure that the number of authors is consistent across all metadata files. Inconsistencies may signal that some contributors are missing in certain files.",

        # Warnings
        "W001": "Add version numbers to your dependencies. This provides stability for users and allows reproducibility across different environments.",
        "W002": "The data in the metadata file should be updated to be aligned with the date of the latest release. Automating this synchronization as part of your release process is highly recommended.",
        "W003": "Make sure you are using the correct licenses. This avoids confusion about terms of use and ensures full transparency.",
        "W004": "Include version numbers for each programming language used. Defining these helps ensure reproducibility and compatibility across systems.",
        "W005": "Rewrite your dependencies as a proper list, with each item separated and preferably with their versions. This makes them easier to parse for metadata systems.",
        "W006": "You should replace plain name in your identifier field with persistent identifiers, such as DOIs or SWHIDs, to improve discoverability and interoperability.",
        "W007": "Add a valid unique identifier to the identifier field in codemeta.json, such as a DOI or SWHID.",
        "W008": "Ensure givenName is a single string per person. This ensures that every author is properly credited and can be extracted automatically",
        "W009": "You need to replace URLs in the developmentStatus field with descriptive text values, such as 'active', 'beta', or 'stable'. This maintains schema compliance and clarity.",
        "W010": "You should replace the remote-style syntax with a full web-accessible URL (e.g., https://github.com/user/repo).",
    }

    return suggestions.get(pitfall_code, f"Review and address the issue described for {pitfall_code}")


def extract_description_info(somef_data: Dict) -> str:
    """
    Extract description information from SoMEF data.
    """
    if "description" in somef_data:
        for entry in somef_data["description"]:
            if "result" in entry and "value" in entry["result"]:
                return entry["result"]["value"]

    return "Software quality assessment for repository metadata"


def convert_sets_to_lists(obj):
    """
    Recursively convert any sets in the data structure to lists for JSON serialization.
    """
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        return {key: convert_sets_to_lists(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_sets_to_lists(item) for item in obj]
    else:
        return obj


def create_pitfall_jsonld(somef_data: Dict, pitfall_results: List[Dict], file_name: str, verbose: bool = False) -> Dict:
    """
    Create a JSON-LD structure for detected pitfalls following the sample format.
    """
    import hashlib
    software_info = extract_software_info_from_somef(somef_data)
    description_info = extract_description_info(somef_data)

    jsonld_output = {
        "@context": "[IN PROCESS]",
        "@type": "SoftwareQualityAssessment",
        "name": f"Quality Assessment for {software_info['name']}",
        "description": description_info,
        "creator": {
            "@type": "schema:Person",
            "name": "Anonymous",
            "email": "example@email.com"
        },
        "dateCreated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "license": {"@id": "https://opensource.org/license/mit"},
        "assessedSoftware": software_info,
        "checkingSoftware": {
            "@type": "schema:SoftwareApplication",
            "name": "RSMetacheck",
            "@id": "https://w3id.org/rsmetacheck",
            "softwareVersion": "0.2.1"
        },
        "checks": []
    }

    for pitfall_result in pitfall_results:
        has_pitfall = pitfall_result.get("has_pitfall", False)
        has_warning = pitfall_result.get("has_warning", False)
        has_issue = has_pitfall or has_warning
        
        if has_issue or verbose:
            pitfall_code = pitfall_result.get("pitfall_code", "Unknown")
            category = get_pitfall_category(pitfall_code)
            
            output_val = "true" if has_issue else "false"
            evidence_val = format_evidence_text(pitfall_code, pitfall_result) if has_issue else f"{pitfall_code} not detected:"
            suggestion_val = get_suggestion_text(pitfall_code, pitfall_result, somef_data) if has_issue else "N/A"

            check_result = {
                "@type": "CheckResult",
                "assessesIndicator": {"@id": f"https://w3id.org/rsmetacheck/catalog/#{pitfall_code}"},
                "process": get_pitfall_description(pitfall_code),
                "status": {"@id": "schema:CompletedActionStatus"},
                "output": output_val,
                "evidence": evidence_val,
                "suggestion": suggestion_val
            }
            
            check_hash = hashlib.sha256(json.dumps(check_result, sort_keys=True).encode("utf-8")).hexdigest()
            check_result["checkId"] = check_hash

            jsonld_output["checks"].append(check_result)

    return jsonld_output


def save_individual_pitfall_jsonld(jsonld_data: Dict, output_dir: Path, file_name: str):
    """
    Save individual JSON-LD file for a repository's pitfalls.
    """
    output_dir.mkdir(exist_ok=True, parents=True)

    base_name = Path(file_name).stem
    output_file = output_dir / f"{base_name}_pitfalls.jsonld"

    try:
        serializable_data = convert_sets_to_lists(jsonld_data)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)

        return str(output_file)
    except Exception as e:
        print(f"Error saving JSON-LD file {output_file}: {e}")
        return None