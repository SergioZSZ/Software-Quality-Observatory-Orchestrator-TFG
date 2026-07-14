import json
from pathlib import Path


# # temporal paths for testing
# INPUT_PATH = Path(
#     r"C:\Users\jzaba\Documents\GitHub\SQOO_TFG\containers\outputs\resqui\sergio-soca-incremental\SergioZSZ_Software-Quality-Observatory-Orchestrator-TFG\resqui_summary.json"
# )

# CONF_PATH = Path(
#     r"C:\Users\jzaba\Documents\GitHub\SQOO_TFG\containers\resqui_container\resqui_runner\configurations\complete.json"
# )

# OUTPUT_PATH_REPORT_MD = Path(
#     r"C:\Users\jzaba\Documents\GitHub\SQOO_TFG\containers\outputs\resqui\sergio-soca-incremental\SergioZSZ_Software-Quality-Observatory-Orchestrator-TFG\resqui_report.md"
# )


# extracts information from the summary JSON file and returns it as a dictionary
def info_extract(summary_path: str | Path):
    summary_path = Path(summary_path)
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary file not found: {summary_path}")

    with open(summary_path, "r", encoding="utf-8") as f:
        summary_data = json.load(f)

    #print("Summary Data:", json.dumps(summary_data, indent=4, ensure_ascii=False))
    return summary_data


# extracts information from the configuration JSON file and returns it as a dictionary
def configuration_extract(configuration_path: str | Path):
    configuration_path = Path(configuration_path)
    if not configuration_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {configuration_path}")

    with open(configuration_path, "r", encoding="utf-8") as f:
        configuration_data = json.load(f)

    #print("Configuration Data:", json.dumps(configuration_data, indent=4, ensure_ascii=False))
    return configuration_data


# extract the relevant information from the summary data
def estructure_extract(summary_data: dict):
    report_data = {
        "context": summary_data.get("@context"),
        "type": summary_data.get("@type"),
        "assessedSoftware": summary_data.get("assessedSoftware"),
        "author": summary_data.get("author"),
        "checks": summary_data.get("checks"),
        "dateCreated": summary_data.get("dateCreated"),
        "license": summary_data.get("license"),
    }

    # print(f"__________________________________________________\n Context: {report_data['context']}\n__________________________________________________")
    # print(f"__________________________________________________\n Type: {report_data['type']}\n__________________________________________________")
    # print(f"__________________________________________________\n Assessed Software: {report_data['assessedSoftware']}\n__________________________________________________")
    # print(f"__________________________________________________\n Author: {report_data['author']}\n__________________________________________________")
    # print(f"__________________________________________________\n Checks: {report_data['checks']}\n__________________________________________________")
    # print(f"__________________________________________________\n Date Created: {report_data['dateCreated']}\n__________________________________________________")
    # print(f"__________________________________________________\n License: {report_data['license']}\n__________________________________________________")

    return report_data


# extract the assessed software information
def assessedSoftware_extract(assessedSoftware: dict):
    if assessedSoftware is None:
        assessedSoftware = {}

    assessed_software_data = {
        "type": assessedSoftware.get("@type"),
        "name": assessedSoftware.get("name"),
        "softwareVersion": assessedSoftware.get("softwareVersion"),
        "url": assessedSoftware.get("url"),
    }

    return assessed_software_data


# normalizes plugin names because configuration and summary can use different names
def plugin_name_normalize(plugin_name: str):
    plugin_name = str(plugin_name or "").strip()

    plugin_aliases = {
        "rsfc": "RSFC",
        "gitleaks": "GitLeaks",
        "gitleak": "GitLeaks",
        "howfairis": "HowFairIs",
        "cffconvert": "CFFConvert",
        "openssfscorecard": "OpenSSF Scorecard",
        "openssf scorecard": "OpenSSF Scorecard",
        "scorecard": "OpenSSF Scorecard",
        "superlinter": "SuperLinter",
        "super-linter": "SuperLinter",
    }

    key = plugin_name.lower().replace(" ", "")
    return plugin_aliases.get(key, plugin_name)


# extracts RESQUI plugins from the configuration file
def configured_plugins_extract(configuration_data: dict):
    configured_plugins = []

    indicators = configuration_data.get("indicators", [])

    for indicator in indicators:
        plugin = indicator.get("plugin")
        plugin = plugin_name_normalize(plugin)

        # RSFC is not included because this report is only for RESQUI plugins
        if plugin == "RSFC":
            continue

        if plugin and plugin not in configured_plugins:
            configured_plugins.append(plugin)

    # print(f"__________________________________________________\n Configured RESQUI Plugins: {configured_plugins}\n__________________________________________________")

    return configured_plugins


# extracts the plugin name from a check
def check_plugin_extract(check: dict):
    checkingSoftware = check.get("checkingSoftware") or {}
    plugin_name = checkingSoftware.get("name")

    return plugin_name_normalize(plugin_name)


# extracts the plugin name with version from a check
def check_plugin_version_extract(check: dict):
    checkingSoftware = check.get("checkingSoftware") or {}

    plugin_name = plugin_name_normalize(checkingSoftware.get("name"))
    plugin_version = checkingSoftware.get("version")

    if plugin_version:
        return f"{plugin_name} {plugin_version}"

    return plugin_name


# extracts the indicator id from a check
def check_indicator_id_extract(check: dict):
    assessesIndicator = check.get("assessesIndicator") or {}
    indicator_id = assessesIndicator.get("@id")

    if indicator_id is None:
        return "N/A"

    return indicator_id


# extracts a readable indicator name from the indicator id
def check_indicator_name_extract(check: dict):
    indicator_id = check_indicator_id_extract(check)

    if indicator_id == "N/A":
        return "N/A"

    return indicator_id.rstrip("/").split("/")[-1]


# classifies the output of a check
def check_output_status_extract(output):
    output = str(output or "").strip().lower()

    passed_outputs = ["true", "valid", "secure", "passed", "pass"]
    failed_outputs = ["false", "invalid", "insecure", "failed", "fail"]
    error_outputs = ["error", "errored"]

    if output in passed_outputs:
        return "passed"

    if output in failed_outputs:
        return "failed"

    if output in error_outputs:
        return "error"

    return "unknown"


# counts the summary results
def summary_counts_extract(checks: list):
    summary_counts = {
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "unknown": 0,
        "total": len(checks),
    }

    for check in checks:
        output = check.get("output")
        status = check_output_status_extract(output)

        if status == "passed":
            summary_counts["passed"] += 1
        elif status == "failed":
            summary_counts["failed"] += 1
        elif status == "error":
            summary_counts["errors"] += 1
        else:
            summary_counts["unknown"] += 1

    return summary_counts


# groups checks by plugin
def checks_by_plugin_extract(checks: list):
    checks_by_plugin = {}

    for check in checks:
        plugin = check_plugin_extract(check)

        if plugin not in checks_by_plugin:
            checks_by_plugin[plugin] = []

        checks_by_plugin[plugin].append(check)

    return checks_by_plugin


# formats values to avoid breaking markdown tables
def markdown_value_format(value):
    if value is None:
        return "N/A"

    if isinstance(value, list):
        value = "<br>".join(str(item) for item in value)

    value = str(value)
    value = value.replace("\n", "<br>")
    value = value.replace("|", "\\|")

    return value

# formats evidence for summary tables
def markdown_evidence_summary_format(evidence):
    if evidence is None:
        return "N/A"

    if isinstance(evidence, list):
        if len(evidence) == 0:
            return "N/A"

        # if there are many evidence items, only a summary is shown in the table
        if len(evidence) > 5:
            return f"{len(evidence)} evidence items detected. See detailed section."

        return markdown_value_format("<br>".join(str(item) for item in evidence))

    return markdown_value_format(evidence)

# creates the general information section
def general_information_create(report_data: dict, assessed_software_data: dict):
    author = report_data.get("author") or {}
    author_name = author.get("name", "Unknown author")

    general_information = f"""
## General Information

- **Software:** {assessed_software_data.get("name", "Unknown software")}
- **Repository:** {assessed_software_data.get("url", "Unknown repository")}
- **Version:** {assessed_software_data.get("softwareVersion", "Unknown version")}
- **Software type:** {assessed_software_data.get("type", "Unknown type")}
- **Assessment type:** {report_data.get("type", "Unknown assessment type")}
- **Generated by:** {author_name}
- **License:** {report_data.get("license", "Unknown license")}
- **Assessment date:** {report_data.get("dateCreated", "Unknown date")}
"""

    return general_information


# creates the summary section
def summary_create(checks: list, configured_plugins: list, checks_by_plugin: dict):
    summary_counts = summary_counts_extract(checks)

    plugins_with_results = []

    for plugin in configured_plugins:
        if plugin in checks_by_plugin:
            plugins_with_results.append(plugin)

    summary = f"""
## Summary

- **Passed**: {summary_counts["passed"]}
- **Failed**: {summary_counts["failed"]}
- **Errors**: {summary_counts["errors"]}
- **Unknown**: {summary_counts["unknown"]}
- **Total checks**: {summary_counts["total"]}
- **Configured RESQUI plugins**: {", ".join(configured_plugins) if configured_plugins else "None"}
- **Plugins with results**: {", ".join(plugins_with_results) if plugins_with_results else "None"}
"""

    return summary


# creates the configured plugins table
def configured_plugins_table_create(configured_plugins: list, checks_by_plugin: dict):
    configured_plugins_table = """
## Configured RESQUI Plugins

| Plugin | Results in this assessment | Checks |
| --- | --- | --- |
"""

    for plugin in configured_plugins:
        plugin_checks = checks_by_plugin.get(plugin, [])
        results = "yes" if len(plugin_checks) > 0 else "no"

        configured_plugins_table += f"| {plugin} | {results} | {len(plugin_checks)} |\n"

    configured_plugins_table += "\n"

    return configured_plugins_table


# creates the results table by plugin
# creates the results table by plugin
def results_table_by_plugin_create(configured_plugins: list, checks_by_plugin: dict):
    results_table = """
## Results Table by Plugin
"""

    for plugin in configured_plugins:
        plugin_checks = checks_by_plugin.get(plugin, [])

        # if the plugin is configured but there are no results, no section is created
        if len(plugin_checks) == 0:
            continue

        plugin_summary = summary_counts_extract(plugin_checks)

        results_table += f"""
### {plugin}

- **Passed**: {plugin_summary["passed"]}
- **Failed**: {plugin_summary["failed"]}
- **Errors**: {plugin_summary["errors"]}
- **Unknown**: {plugin_summary["unknown"]}
- **Total checks**: {plugin_summary["total"]}

| Indicator | Short Description | Output | Evidence |
| --- | --- | --- | --- |
"""

        for check in plugin_checks:
            indicator_id = check_indicator_id_extract(check)
            indicator_name = check_indicator_name_extract(check)
            process = check.get("process")
            output = check.get("output")
            evidence = check.get("evidence")

            if indicator_id != "N/A":
                indicator_cell = f"[{indicator_name}]({indicator_id})"
            else:
                indicator_cell = indicator_name

            results_table += (
                f"| {markdown_value_format(indicator_cell)} | "
                f"{markdown_value_format(process)} | "
                f"{markdown_value_format(output)} | "
                f"{markdown_evidence_summary_format(evidence)} |\n"
            )

        results_table += "\n"

    return results_table


# creates the final markdown report
def create_report(
    report_data: dict,
    assessed_software_data: dict,
    configured_plugins: list,
    configured_indicators: list,
    output_path: str | Path,
):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    checks = report_data.get("checks") or []
    checks_by_plugin = checks_by_plugin_extract(checks)

    software_name = assessed_software_data.get("name", "Unknown software")

    report = f"""# RESQUI Quality & Security Assessment for {software_name}

An automated RESQUI assessment summary report, combining the configured quality and security plugins.
"""

    report += general_information_create(report_data, assessed_software_data)
    report += summary_create(checks, configured_plugins, checks_by_plugin)
    report += configured_plugins_table_create(configured_plugins, checks_by_plugin)
    report += results_table_by_plugin_create(configured_plugins, checks_by_plugin)
    report += detailed_results_by_indicator_create(configured_indicators, checks)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    # print(f"__________________________________________________\n RESQUI report generated: {output_path}\n__________________________________________________")

# extracts configured RESQUI indicators from the configuration file
def configured_indicators_extract(configuration_data: dict):
    configured_indicators = []

    indicators = configuration_data.get("indicators", [])

    for indicator in indicators:
        plugin = indicator.get("plugin")
        plugin = plugin_name_normalize(plugin)

        # RSFC is not included because this report is only for RESQUI plugins
        if plugin == "RSFC":
            continue

        configured_indicator = {
            "name": indicator.get("name"),
            "plugin": plugin,
            "id": indicator.get("@id"),
        }

        configured_indicators.append(configured_indicator)

    # print(f"__________________________________________________\n Configured RESQUI Indicators: {configured_indicators}\n__________________________________________________")

    return configured_indicators


# creates a markdown anchor id
def markdown_anchor_create(text: str):
    text = str(text or "").lower()
    text = text.replace("https://", "")
    text = text.replace("http://", "")

    anchor = ""

    for character in text:
        if character.isalnum():
            anchor += character
        else:
            anchor += "-"

    while "--" in anchor:
        anchor = anchor.replace("--", "-")

    return anchor.strip("-")


# formats evidence for detailed markdown sections
def markdown_evidence_format(evidence):
    if evidence is None:
        return "N/A"

    if isinstance(evidence, list):
        if len(evidence) == 0:
            return "N/A"

        evidence_text = ""
        for item in evidence:
            evidence_text += f"\n\t- {item}"

        return evidence_text

    return str(evidence)


# creates a dictionary to search checks by indicator id
def checks_by_indicator_extract(checks: list):
    checks_by_indicator = {}

    for check in checks:
        indicator_id = check_indicator_id_extract(check)

        if indicator_id not in checks_by_indicator:
            checks_by_indicator[indicator_id] = []

        checks_by_indicator[indicator_id].append(check)

    return checks_by_indicator


# creates the detailed results by indicator section
def detailed_results_by_indicator_create(configured_indicators: list, checks: list):
    checks_by_indicator = checks_by_indicator_extract(checks)
    detailed_results_by_plugin = {}

    detailed_results = """
## Detailed Results by Indicator
"""

    for configured_indicator in configured_indicators:
        indicator_name = configured_indicator.get("name")
        indicator_id = configured_indicator.get("id")
        configured_plugin = configured_indicator.get("plugin")

        indicator_checks = checks_by_indicator.get(indicator_id, [])

        # if the indicator is configured but there are no results, no section is created
        if len(indicator_checks) == 0:
            continue

        if configured_plugin not in detailed_results_by_plugin:
            detailed_results_by_plugin[configured_plugin] = []

        detailed_results_by_plugin[configured_plugin].append(
            {
                "name": indicator_name,
                "id": indicator_id,
                "checks": indicator_checks,
            }
        )

    for plugin, plugin_indicators in detailed_results_by_plugin.items():
        detailed_results += f"""
### {plugin}
"""

        for indicator in plugin_indicators:
            indicator_name = indicator.get("name")
            indicator_id = indicator.get("id")

            for check in indicator.get("checks", []):
                plugin_with_version = check_plugin_version_extract(check)
                output = check.get("output")
                process = check.get("process")
                evidence = check.get("evidence")

                anchor_id = markdown_anchor_create(
                    f"{plugin}-{indicator_name}-{indicator_id}"
                )

                detailed_results += f"""
<a id="{anchor_id}"></a>
#### {indicator_name}

- **Execution plugin:** {plugin_with_version}
- **Indicator ID:** {indicator_id}
- **Result:** {output}
- **Process:** {process}
- **Evidence:** {markdown_evidence_format(evidence)}
- **Suggestions:** N/A
"""

    detailed_results += "\n"

    return detailed_results
# generates a RESQUI markdown report
def resqui_report_generation(
    input_path: str | Path,
    conf_path: str | Path,
    output_report_path: str | Path,
):
    input_path = Path(input_path)
    conf_path = Path(conf_path)
    output_report_path = Path(output_report_path)

    try:
        summary_data = info_extract(input_path)
        configuration_data = configuration_extract(conf_path)

        estructure_data = estructure_extract(summary_data)
        assessed_software_data = assessedSoftware_extract(
            summary_data.get("assessedSoftware")
        )

        configured_plugins = configured_plugins_extract(configuration_data)
        configured_indicators = configured_indicators_extract(configuration_data)

        create_report(
            report_data=estructure_data,
            assessed_software_data=assessed_software_data,
            configured_plugins=configured_plugins,
            configured_indicators=configured_indicators,
            output_path=output_report_path,
        )

    except FileNotFoundError as e:
        print(e)



def main():
    resqui_report_generation(
        input_path=INPUT_PATH,
        conf_path=CONF_PATH,
        output_report_path=OUTPUT_PATH_REPORT_MD,
    )

if __name__ == "__main__":
    main()
