from .database import SessionLocal
from .rabbitmq.client import publish_job
from .database import Job

import json,os



def main(input: dict):

    db = SessionLocal()
    
    # procesamiento repos llegados
    repos =input["repos_url"]
    jobs = []

    for repo_url in repos:
        
        
        name = repo_url.rstrip("/").split("/")[-1]
        target = repo_url.rstrip("/").split("/")[-2]
        job_id = target + "_" + name


        job = Job(
            id=job_id,
            target=target,
            repo_url=repo_url,
            status="queued"
        )

        jobs.append(job)
        
    db.add_all(jobs)
    db.commit()
    
    # publicacion de jobs
    for job in jobs:
        publish_job(job.id, job.repo_url, job.target)
        

    






if __name__ == "__main__":
    input = json.loads(os.getenv("INPUT"))
    main(input)
    