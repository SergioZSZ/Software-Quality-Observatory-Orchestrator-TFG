from .rabbitmq import publish_job
from .models import SocaResponse
import os, json, shutil, argparse
from soca_runner.config import BASE_DIR, TARGET, TYPE
from .cruds import soca_fetch

def main(repos_file=None, target_name=None):
    

    
    print("** Soca runner started **")
    
    target = target_name if target_name else TARGET
    target_dir = os.path.join(BASE_DIR, "outputs", "soca", target)

    # truncado carpeta del target por metadatos anticuados guardados y portal
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    os.makedirs(target_dir, exist_ok=True)
    
    try:
        
        # primero comprobar si va a se custom
        if repos_file:
            print("**\nUsing custom repos.txt...\n")
            #copiamos repos.txt en el dir creado
            shutil.copy(repos_file, os.path.join(target_dir, "repos.txt"))

            with open(repos_file, "r") as f:
                repos = [line.strip() for line in f if line.strip()]
            
            
        #si no fetch del target 
        else:
            print("**\nFetching repos...\n")

            response_fetch = soca_fetch(BASE_DIR, target, TYPE)
            
            if response_fetch.status["status"]=="error":
                print(f"Soca Fetch Error: {response_fetch.status}")
                raise
            
            repos = response_fetch.repos

            
        # publicando jobs de repos por cada uno
        for repo in repos:
            print(f"\n{repo} sent to worker")
            
            publish_job(target, "extract_metadata", repo)
            
        return SocaResponse(status="success", target= target, response=repos, err= None)

        
    except Exception as e:
        print(f"Error: {e}")
        raise




if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repos",
        help="manual repos.txt dir",
        default=None
    )

    parser.add_argument(
        "--name",
        help="name of the output dir (outputs/soca/)",
        default=None
    )

    args = parser.parse_args()

    main(args.repos, args.name)