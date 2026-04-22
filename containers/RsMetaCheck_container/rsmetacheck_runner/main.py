import json, os, shutil
from datetime import datetime
from .config import BASE_DIR, INPUT, TOKEN
from .cruds import rsmetacheck_runner


def timestamp(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def save_failed_assessment(target: str, repo_url: str, detail: dict) -> None:
    repo_name = repo_url.rstrip("/").split("/")[-1]
    failed_repo_dir = os.path.join(BASE_DIR, "outputs", "rsmetacheck", target, repo_name)
    os.makedirs(failed_repo_dir, exist_ok=True)

    failed_job_file = os.path.join(failed_repo_dir, "failed_assessment.json")
    with open(failed_job_file, "w", encoding="utf-8") as f:
        json.dump({"detail": detail}, f, indent=2)




def main(input_data: dict) -> None:
    repos = input_data["repos_url"]
    repos_count = len(repos)
    target = input_data["target"]

    target_dir = os.path.join(BASE_DIR, "outputs", "rsmetacheck", target)

    # limpieza de anteriores test 
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    os.makedirs(target_dir, exist_ok=True)

    timestamp(f"[RSMT] execution started for target '{target}' with {repos_count} repos")

    completed = 0

    for repo_url in repos:
        repo_name = repo_url.rstrip("/").split("/")[-1]
        timestamp(f"[RSMT] Processing repo '{repo_name}'")

        try:
            response = rsmetacheck_runner(BASE_DIR, target, repo_url, TOKEN)

            if response.status["status"] == "success":
                completed += 1
                timestamp(f"[RSMT] Progress: {completed}/{repos_count} repos processed")
                continue
            
            save_failed_assessment(target, repo_url, response.status)
            timestamp(f"[RSMT] Repo '{repo_name}' failed")

        except Exception as e:
            error_detail = {
                "status": "error",
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
            }
            save_failed_assessment(target, repo_url, error_detail)
            timestamp(f"[RSMT] Repo '{repo_name}' failed with exception: {e}")

    timestamp(f"[RSMT] Sequential execution finished for target '{target}'")


if __name__ == "__main__":
    input_data = json.loads(INPUT)
    main(input_data)
