import requests
import time 
import os, json

def main():
    
    
    url_prod = "http://localhost:5678/webhook-test/run"
    url_des = "http://localhost:5678/webhook/run"

    target = input("Introduce el usuario u organización: ").strip()
    type = input("Introduce el tipo (user/org): ").strip().lower()

    if type not in ["user", "org"]:
        while type not in ["user","org"]:
            
            print("Error: tipo debe ser 'user' o 'org'")
            target = input("Introduce el usuario u organización: ").strip()
            type = input("Introduce el tipo (user/org): ").strip().lower()
            

    send = {
        "input": target,
        "type": type
    }


    try:
        start = time.perf_counter() 
        
        response = requests.post(url_prod, json=send)
        
        end = time.perf_counter() 
        
        total = end-start
        
    except Exception as e:
        print("Error enviando datos:", e)
    
    data = response.json()
    

    current_dir = os.path.dirname(os.path.abspath(__file__))
    filename = f"{target}_result.json"
    filepath = os.path.join(current_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"\nJSON guardado en: {filepath}")
    print(f"\nTiempo total de ejecución: {total:.2f} segundos")
        
if __name__ == "__main__":
    main()