- quitados apis por execute commands de docker (en vez de endpoints se ejecuta el main de cada container)
- modificado workflows a 2, uno para rsfc y otro para soca
- modificdo github harvester linea 211 subido timeout a 60
- aumentado max retries a 5 de worker rsfc por problemas de red

- creado imagenes de soca y rsfc heavy, para que docker compose vaya mas rapido (modificando docker y docker compose con ellas)
- modificado .githubatributes para que los .sh sean siempre `lf`
- añadida nueva cola de eventos rsfc_events para trigger de workflow dashverse
- añadido nueva función `publish_event(target: str)` en rsfc para el envío de event a rsfc_events
con el target y sus repositorios
- subido a 7 retries los problemas de red y cambiado backoff lineal a exponencial
- generado workflow dashverse en n8n
