
## 4. Requisitos(Requirements)
#### Requisitos generales
   - Docker/Docker Desktop (29.0.1)
   - Docker compose (v2.40.3-desktop.1)
   - Estar loggeado en Docker/Docker Desktop

#### Instalaciones necesarias para desplegar DashVERSE:
Si se usa Windows, DashVERSE se despliega desde Ubuntu en WSL. Ansible no funciona como control node nativo en Windows y conviene que `kubectl`, `make port-forward` y `make setup-dashboards` se ejecuten en el mismo entorno para que no haya problemas con `localhost`.

Antes de empezar en Windows hay que tener Docker Desktop instalado, abierto y con la integracion WSL activada para Ubuntu.

   - make 
      - Linux/WSL:   ``sudo apt install make``

   - Terraform/OpenTofu 
      - Linux/WSL:    ``sudo snap install opentofu --classic`` 

   - Minikube
      - Linux/WSL:
        ```bash
        curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
        sudo install minikube-linux-amd64 /usr/local/bin/minikube
        rm minikube-linux-amd64
        minikube version
        ```
      
   - Helm      
      - Linux/WSL:    ``sudo snap install helm --classic``

   - Kubectl
      - Linux/WSL:    instalarlo dentro de WSL y comprobar que `which kubectl` apunta al binario de linux
   
   - Ansible
      - Linux/WSL:
        ```bash
        sudo apt update
        sudo apt install -y python3 python3-pip
        python3 -m pip install --user ansible
        ansible --version
        ```



#### Herramientas usadadas en el proyecto:
- SOCA 0.0.3: 
https://github.com/oeg-upm/soca/releases/tag/0.0.3

- RSFC 0.1.5: 
https://github.com/oeg-upm/rsfc/releases/tag/v0.1.5

- SOMEF 0.10.3:
https://github.com/KnowledgeCaptureAndDiscovery/somef/releases/tag/0.10.3

- DASHVERSE 0.2.0: 
https://github.com/EVERSE-ResearchSoftware/DashVERSE/releases/tag/v0.2.0

- sw-metadata-bot 0.4.2:
https://github.com/SoftwareUnderstanding/sw-metadata-bot/releases/tag/v0.4.2

- RsMetaCheck 0.2.1:
https://github.com/SoftwareUnderstanding/RsMetaCheck/releases/tag/0.2.1
      
