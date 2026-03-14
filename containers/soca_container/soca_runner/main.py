from .rabbitmq import publish_job
from .models import SocaResponse
import os, json, shutil
from soca_runner.config import BASE_DIR, TARGET, TYPE
from .cruds import soca_fetch
def main():
    

    
    print("** Soca runner started **")
    
    os.makedirs(os.path.join(BASE_DIR,"outputs","soca",TARGET), exist_ok=True)
    
    try:
        #service 
        print("**\nFetching repos...\n")

        response_fetch = soca_fetch(BASE_DIR, TARGET, TYPE)
        
        if response_fetch.status["status"]=="error":
            print(f"Soca Fetch Error: {response_fetch.status}")
            raise
            
        
        # truncado carpeta del target por metadatos anticuados guardados
        metadata_dir = os.path.join(BASE_DIR, "outputs", "soca", TARGET,"metadata")
        if os.path.exists(metadata_dir):
            shutil.rmtree(metadata_dir)
            
        # publicando jobs de repos por cada uno
        for repo in response_fetch.repos:
            print(f"\n{repo} sent to worker")
            
            publish_job(TARGET, "extract_metadata", repo)
            
        return SocaResponse(status="success", target= TARGET, response=response_fetch.repos, err= None)

        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__=="__main__":
    main()