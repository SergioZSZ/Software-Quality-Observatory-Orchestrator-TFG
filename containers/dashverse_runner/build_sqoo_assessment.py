"""Build a single SQOO assessment from RSFC and RESQUI outputs."""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ARCHIVED_SOFTWARE_HERITAGE = (
    "https://w3id.org/everse/i/indicators/archived_in_software_heritage"
)
ARCHIVED_SCHOLARLY_REPOSITORY = (
    "https://w3id.org/everse/i/indicators/archived_in_scholarly_repository"
)

PASS_OUTPUTS = {"true", "valid", "pass", "passed"}
RESQUI_AUTHOR = {"@type": "Person", "name": "Quality Pipeline"}
RESQUI_LICENSE = "CC0-1.0"


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as file:
        return json.load(file)


def load_optional_json(path: str | Path) -> dict[str, Any] | None:
    input_path = Path(path)
    if not input_path.exists():
        return None
    return load_json(input_path)


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    output_path = Path(path)
    remove_existing_assessment_outputs(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def remove_existing_assessment_outputs(output_path: str | Path) -> None:
    target_path = Path(output_path)
    stale_paths = {target_path}

    if target_path.parent.parent.name == "sqoo_assessments":
        stale_paths.add(target_path.parent.parent / target_path.name)

    for stale_path in stale_paths:
        if stale_path.exists() and stale_path.is_file():
            stale_path.unlink()


def output_path_for_assessment(
    output_dir: str | Path,
    assessment: dict[str, Any],
    project: str | None = None,
) -> Path:
    org, repo = _repository_parts(assessment)
    base_dir = Path(output_dir)
    if project:
        base_dir = base_dir / _safe_filename_part(project)
    return base_dir / f"{_safe_filename_part(org)}_{_safe_filename_part(repo)}_assessment.json"


def build_assessment(
    rsfc_assessment: dict[str, Any],
    resqui_summary: dict[str, Any],
    rsfc_indicators: dict[str, Any],
) -> dict[str, Any]:
    assessment = copy.deepcopy(resqui_summary)
    resqui_checks = copy.deepcopy(resqui_summary.get("checks") or [])
    rsfc_checks = _select_rsfc_checks(
        rsfc_assessment.get("checks") or [],
        rsfc_indicators.get("indicators") or [],
    )
    assessment["checks"] = resqui_checks + rsfc_checks
    return assessment


def build_assessment_from_available(
    rsfc_assessment: dict[str, Any] | None,
    resqui_summary: dict[str, Any] | None,
    rsfc_indicators: dict[str, Any],
) -> dict[str, Any] | None:
    if resqui_summary and rsfc_assessment:
        return build_assessment(rsfc_assessment, resqui_summary, rsfc_indicators)

    if resqui_summary:
        return copy.deepcopy(resqui_summary)

    if rsfc_assessment:
        return _build_resqui_style_assessment_from_rsfc(
            rsfc_assessment,
            _select_rsfc_checks(
                rsfc_assessment.get("checks") or [],
                rsfc_indicators.get("indicators") or [],
            ),
        )

    return None


def _build_resqui_style_assessment_from_rsfc(
    rsfc_assessment: dict[str, Any],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    assessed_software = copy.deepcopy(rsfc_assessment.get("assessedSoftware") or {})
    if assessed_software:
        assessed_software["@type"] = "SoftwareApplication"

    return {
        "@context": rsfc_assessment.get("@context", "https://w3id.org/everse/rsqa/0.0.1/"),
        "@type": rsfc_assessment.get("@type", "SoftwareQualityAssessment"),
        "assessedSoftware": assessed_software,
        "author": copy.deepcopy(rsfc_assessment.get("author") or RESQUI_AUTHOR),
        "checks": checks,
        "dateCreated": rsfc_assessment.get("dateCreated"),
        "license": _normalize_assessment_license(rsfc_assessment.get("license")),
    }


def _select_rsfc_checks(
    rsfc_checks: list[dict[str, Any]], configured_indicators: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []

    for indicator in configured_indicators:
        indicator_id = indicator.get("@id")
        processes = indicator.get("checks") or []
        matches = _matching_checks(rsfc_checks, indicator_id, processes)

        if not matches:
            continue

        if str(indicator.get("operator", "")).upper() == "OR":
            selected.append(_normalize_rsfc_check(_merge_or_check(indicator_id, matches)))
        else:
            selected.extend(_normalize_rsfc_check(check) for check in matches)

        if indicator_id == ARCHIVED_SOFTWARE_HERITAGE:
            selected.append(_derive_scholarly_repository_check(selected[-1]))

    return selected


def _matching_checks(
    checks: list[dict[str, Any]], indicator_id: str | None, processes: list[str]
) -> list[dict[str, Any]]:
    process_set = set(processes)
    return [
        check
        for check in checks
        if check.get("assessesIndicator", {}).get("@id") == indicator_id
        and check.get("process") in process_set
    ]


def _merge_or_check(indicator_id: str | None, checks: list[dict[str, Any]]) -> dict[str, Any]:
    merged = copy.deepcopy(checks[0])
    merged["assessesIndicator"] = {"@id": indicator_id}
    merged["process"] = " OR ".join(check.get("process", "") for check in checks)
    merged["output"] = "true" if any(_check_passed(check) for check in checks) else "false"
    merged["evidence"] = (
        "N/A"
        if _check_passed(merged)
        else " OR ".join(str(check.get("evidence", "N/A")) for check in checks)
    )
    merged.pop("test_id", None)
    merged.pop("test_name", None)
    merged.pop("suggestions", None)
    return merged


def _normalize_rsfc_check(check: dict[str, Any]) -> dict[str, Any]:
    return {
        "@type": check.get("@type", "CheckResult"),
        "assessesIndicator": copy.deepcopy(check.get("assessesIndicator") or {}),
        "checkingSoftware": _normalize_checking_software(
            check.get("checkingSoftware") or {}
        ),
        "process": check.get("process", ""),
        "status": copy.deepcopy(check.get("status") or {}),
        "output": check.get("output", ""),
        "evidence": check.get("evidence", "N/A"),
    }


def _normalize_checking_software(checking_software: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": checking_software.get("name", "RSFC"),
        "version": checking_software.get("version")
        or checking_software.get("softwareVersion", "unknown"),
    }


def _normalize_assessment_license(license_value: Any) -> str:
    if isinstance(license_value, str):
        return license_value
    if isinstance(license_value, dict):
        license_id = str(license_value.get("@id") or "").rstrip("/")
        if license_id == "https://creativecommons.org/publicdomain/zero/1.0":
            return RESQUI_LICENSE
        return str(license_value.get("name") or license_value.get("@id") or RESQUI_LICENSE)
    return RESQUI_LICENSE


def _derive_scholarly_repository_check(check: dict[str, Any]) -> dict[str, Any]:
    derived = copy.deepcopy(check)
    derived["assessesIndicator"] = {"@id": ARCHIVED_SCHOLARLY_REPOSITORY}
    return derived


def _check_passed(check: dict[str, Any]) -> bool:
    output = str(check.get("output", "")).strip().lower()
    status = str(check.get("status", {}).get("@id", "")).lower()
    return output in PASS_OUTPUTS or "pass" in status


def _repository_parts(assessment: dict[str, Any]) -> tuple[str, str]:
    software = assessment.get("assessedSoftware") or {}
    url = str(software.get("url") or "").strip()
    path_parts = [
        part for part in urlparse(url).path.strip("/").split("/") if part
    ]

    if len(path_parts) >= 2:
        org = path_parts[-2]
        repo = path_parts[-1]
        return org, repo.removesuffix(".git")

    name = str(software.get("name") or "unknown_repository").strip()
    return "unknown", name.removesuffix(".git")


def _safe_filename_part(value: str) -> str:
    safe_value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return safe_value.strip("._-") or "unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a single SQOO assessment from RSFC and RESQUI JSON outputs."
    )
    parser.add_argument("--rsfc", required=True, help="Path to rsfc_assessment.json")
    parser.add_argument("--resqui", required=True, help="Path to resqui_summary.json")
    parser.add_argument(
        "--rsfc-indicators",
        required=True,
        help="Path to dashverse_runner/rsfc_indicators.json",
    )
    parser.add_argument(
        "--project",
        help="Project folder name to create below --output-dir",
    )
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument("--output", help="Exact output assessment path")
    output_group.add_argument(
        "--output-dir",
        help="Directory where org_repository_assessment.json will be written",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    assessment = build_assessment_from_available(
        rsfc_assessment=load_optional_json(args.rsfc),
        resqui_summary=load_optional_json(args.resqui),
        rsfc_indicators=load_json(args.rsfc_indicators),
    )
    if assessment is None:
        if args.output:
            write_json(
                args.output,
                {
                    "skip": True,
                    "reason": "No RSFC or RESQUI assessment found.",
                },
            )
        print("No RSFC or RESQUI assessment found. Skipping repository.", flush=True)
        return

    output_path = args.output or output_path_for_assessment(
        args.output_dir,
        assessment,
        project=args.project,
    )
    write_json(output_path, assessment)


if __name__ == "__main__":
    main()
