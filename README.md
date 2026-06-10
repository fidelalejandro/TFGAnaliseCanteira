# RC Celta de Vigo — Sistema de Análisis de Cantera

Herramienta de apoyo al análisis de jugadores de cantera del RC Celta de Vigo basada en datos GPS Catapult, algoritmos de *matching*, visualización interactiva y explicación mediante inteligencia artificial generativa.

El sistema permite consultar jugadores, comparar perfiles físicos, generar rankings de similitud y obtener respuestas en lenguaje natural a partir de datos previamente procesados en Databricks.

---

## Funcionalidades principales

- Consulta de jugadores y métricas GPS.
- Búsqueda de jugadores por nombre o posición.
- Consulta de perfiles físicos disponibles.
- Identificación de jugadores similares a un perfil de referencia.
- Comparación entre jugadores.
- Consulta de variables GPS más relevantes para cada perfil.
- Clasificación funcional de jugadores según perfiles definidos.
- Generación automática de visualizaciones interactivas.
- Respuestas en lenguaje natural mediante Claude Haiku.

---

## Requisitos

Antes de ejecutar la aplicación es necesario disponer de:

- Python 3.10 o superior.
- Git.
- Conexión a Internet.
- Acceso al clúster de Databricks utilizado por el proyecto.
- Clave de API de Anthropic para el uso de Claude.
- Archivo `tfg_celta.env` con las credenciales necesarias.

> **Importante:** el archivo `tfg_celta.env` contiene credenciales sensibles y no debe subirse al repositorio.

---

## Instalación

Clonar el repositorio:

```bash
git clone https://github.com/fidelalejandro/TFG_Analise_Canteira.git
cd TFG_Analise_Canteira
