[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18879858.svg)](https://doi.org/10.5281/zenodo.18879858)[![Project Status: Active ](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)[![GitHub release](https://img.shields.io/github/v/release/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG?include_prereleases)](https://github.com/SergioZSZ/Software-Quality-Observatory-Orchestrator-TFG/releases)![RSFC_Coverage](https://img.shields.io/badge/rsfc-coverage_83%25-green)

**🚧🚧 STILL IN PROCRESS 🚧🚧**
# TFG – Orquestación automatizada de evaluación de software y generación de catálogo

## 1. Objetivo del proyecto

El objetivo del TFG es diseñar e implementar un sistema reproducible que:

1. Extraiga automáticamente repositorios de GitHub
2. Genere metadatos estructurados del software
3. Evalúe la calidad del software mediante indicadores automáticos
4. Evalúe la calidad de los metadatos del software y suba Issues automáticas a GitHub
5. Prepare la información para su integración en dashboards (DashVERSE) y catálogos (SOCA)
6. Permita orquestar todo el proceso mediante workflows automatizados

El sistema se basa en la integración y orquestación de herramientas existentes dentro de una arquitectura desacoplada y reproducible.




## 2. Arquitectura del sistema
---
| Componente       | Rol                                    |
| ---------------- | -------------------------------------- |
| n8n              | Orquestación                           |
| soca_container   | extracción metadatos-repos y jobs soca |
| rsfc_container   | creación de jobs rsfc                  |
| rabbitmq         | message broker                         |
| worker_rsfc      | procesamiento jobs indicadores         |
| worker_soca      | procesamiento jobs metadatos           |
| rate_limiter_rsfc| limitador tokens githubAPI worker_rsfc |
| DashVerse        | observatorio de evaluación             |
| sw-metadata-bot  | Generación de issues sobre metadatos   |





![Diagrama de flujo](images/flujo_SQOO.png)




Cada herramienta se ejecuta en su propio entorno aislado, garantizando:

- Reproducibilidad
- Portabilidad
- Independencia del sistema operativo
- Aislamiento de dependencias
- Escalabilidad
