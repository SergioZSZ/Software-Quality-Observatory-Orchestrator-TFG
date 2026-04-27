# Pasos seguidos con `sw-metadata-bot`


1. Se descargo el repositorio del bot y se coloco en:

```text
integrations/sw-metadata-bot-0.4.1
```

Mandato orientativo:

`git clone https://github.com/SoftwareUnderstanding/sw-metadata-bot.git integrations/sw-metadata-bot-0.4.1`

2. Se preparo el entorno del proyecto con uv desde la carpeta del bot.

Mandatos:

`cd integrations/sw-metadata-bot-0.4.1`  
`uv sync`




5. En un shell, se exporto la variable esperada por el bot a partir del valor `GITHUB_TOKEN` guardado en `containers/.env` desde la raiz del proyecto `/`:


- linux: 
`export GITHUB_API_TOKEN=$(grep '^GITHUB_TOKEN=' ./containers/.env | cut -d '=' -f2-)`

- Windows: 
```powershell
$env:GITHUB_API_TOKEN = (Select-String '^GITHUB_TOKEN=' .\containers\.env).Line.Split('=', 2)[1]
```


6. El siguiente paso es ejecutar la verificacion de autenticacion del bot: 

`uv run sw-metadata-bot verify-tokens`

Mandatos posibles:

`cd integrations/sw-metadata-bot-0.4.1`  
`.venv/Scripts shell`  
`sw-metadata-bot verify-tokens`

7. crear en `/assets` de sw-metadata-bot un config.json con este formato

````bash
{
  "repositories": [
    "https://github.com/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG"
  ],
  "issues": {
    "custom_message": "This issue was created automatically after running metadata quality checks. Several warnings or pitfalls were detected and may be worth reviewing.",
    "opt_outs": []
  },
  "outputs": {
    "root_dir": "assets",
    "run_name": "example_run",
    "snapshot_tag_format": "%Y%m%d"
  }
}
````


8. Empezar análisis con 

  `uv run sw-metadata-bot run-analysis --config-file assets/config.json`