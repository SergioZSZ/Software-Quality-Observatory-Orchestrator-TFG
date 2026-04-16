from .rabbitmq.client import publish_job
import json,os, shutil
from .config import BASE_DIR, INPUT



def main(input: dict):
    
    repos =input["repos_url"]
    repos_count = len(repos)
    
    repo_url = repos[0]
    target = input.get("target")

    
    # truncado de indicadores obsoletos inicial
    target_dir = os.path.join(BASE_DIR, "outputs", "rsfc",target)

    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    os.makedirs(target_dir, exist_ok=True)

    #procesamiento de repos (jobs)
    for repo_url in repos:
        
        
        name = repo_url.rstrip("/").split("/")[-1]
        target = input.get("target")
        job_id = target + "_" + name

        publish_job(job_id, repo_url, target, repos_count)

 
    
        
        

    






if __name__ == "__main__":
    input = json.loads(INPUT)
    main(input)
    