import argparse
import os
from pathlib import Path
from rsmetacheck.run_somef import run_somef_batch, run_somef_single, ensure_somef_configured
from rsmetacheck.run_analyzer import run_analysis


def cli():
    parser = argparse.ArgumentParser(description="Detect metadata pitfalls in software repositories using SoMEF.")
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="One or more: GitHub/GitLab URLs, JSON files containing repositories, OR existing SoMEF output files when using --skip-somef."
    )
    parser.add_argument(
        "--skip-somef",
        action="store_true",
        help="Skip SoMEF execution and analyze existing SoMEF output files directly. --input should point to SoMEF JSON files."
    )
    parser.add_argument(
        "--pitfalls-output",
        default=os.path.join(os.getcwd(), "pitfalls_outputs"),
        help="Directory to store pitfall JSON-LD files (default: ./pitfalls_outputs)."
    )
    parser.add_argument(
        "--somef-output",
        default=os.path.join(os.getcwd(), "somef_outputs"),
        help="Directory to store SoMEF output files (default: ./somef_outputs)."
    )
    parser.add_argument(
        "--analysis-output",
        default=os.path.join(os.getcwd(), "analysis_results.json"),
        help="File path for summary results (default: ./analysis_results.json)."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="SoMEF confidence threshold (default: 0.8). Only used when running SoMEF."
    )
    parser.add_argument(
        "-b", "--branch",
        help="Branch of the repository to analyze. Overrides the default branch. Only used when running SoMEF."
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include both detected AND undetected pitfalls in the output JSON-LD."
    )

    args = parser.parse_args()

    if args.skip_somef:
        print(f"Skipping SoMEF execution. Analyzing {len(args.input)} existing SoMEF output files...")

        somef_json_paths = []
        for json_path in args.input:
            if not os.path.exists(json_path):
                print(f"Warning: File not found, skipping: {json_path}")
                continue
            somef_json_paths.append(Path(json_path))

        if not somef_json_paths:
            print("Error: No valid SoMEF output files found.")
            return

        print(f"Analyzing {len(somef_json_paths)} SoMEF output files...")
        run_analysis(somef_json_paths, args.pitfalls_output, args.analysis_output, verbose=args.verbose)

    else:
        ensure_somef_configured()

        threshold = args.threshold
        somef_output_dir = args.somef_output

        print(f"Detected {len(args.input)} input(s):")

        for input_item in args.input:
            if input_item.startswith("http://") or input_item.startswith("https://"):
                print(f"Processing repository URL: {input_item}")
                run_somef_single(input_item, somef_output_dir, threshold, branch=args.branch)
            elif os.path.exists(input_item):
                print(f"Processing repositories from file: {input_item}")
                run_somef_batch(input_item, somef_output_dir, threshold, branch=args.branch)
            else:
                print(f"Warning: Skipping invalid input (not a URL or existing file): {input_item}")

        print(f"\nRunning analysis on outputs in {somef_output_dir}...")
        run_analysis(somef_output_dir, args.pitfalls_output, args.analysis_output, verbose=args.verbose)


if __name__ == "__main__":
    cli()