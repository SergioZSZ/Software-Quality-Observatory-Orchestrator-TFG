import os
from soca_runner.config import BASE_DIR
from .cruds import soca_portal
def genportal():
    

    
    print("** Soca portal gen started **")
    
    try:
        #service 
        target = os.getenv("TARGET")

        response_fetch = soca_portal(BASE_DIR, target)
        
        if response_fetch.status["status"]=="error":
            print(f"Soca Portal Error: {response_fetch.status}")
            raise
            

        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__=="__main__":
    genportal()
