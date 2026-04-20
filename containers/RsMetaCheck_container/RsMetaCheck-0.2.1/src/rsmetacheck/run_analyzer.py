from pathlib import Path
from typing import Union, Iterable
from rsmetacheck.detect_pitfalls_main import main


def run_analysis(somef_input: Union[str, Path, Iterable[Path]], pitfalls_dir: Union[str, Path], analysis_file: Union[str, Path], verbose: bool = False):
    """
    Run metadata analysis using existing code.

    Args:
        somef_input: Either a directory path (str/Path) containing SoMEF JSONs,
                     or an iterable of Path objects pointing to specific SoMEF JSON files
        pitfalls_dir: Directory to save pitfall JSON-LD files
        analysis_file: Path to save summary results JSON
        verbose: bool indicating if both detected and undetected checks should be logged.
    """
    print(f"\nRunning analysis...")

    if isinstance(somef_input, (str, Path)):
        somef_path = Path(somef_input)
        if somef_path.is_dir():
            print(f"Using directory: {somef_input}")
            main(input_dir=somef_input, pitfalls_dir=pitfalls_dir, analysis_output=analysis_file, verbose=verbose)
        else:
            print(f"Error: {somef_input} is not a valid directory")
    else:
        json_files = list(somef_input)
        print(f"Using {len(json_files)} specified JSON files")
        main(somef_json_paths=json_files, pitfalls_dir=pitfalls_dir, analysis_output=analysis_file, verbose=verbose)