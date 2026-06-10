# RC Celta de Vigo — Sistema de Análisis de Cantera

Asistente inteligente para identificar y analizar jugadores de cantera mediante datos GPS Catapult y Machine Learning.

---

## Requisitos

- Python 3.10 o superior
- Conexión a internet (acceso al cluster Databricks del Celta)
- Archivo `tfg_celta.env` con las credenciales (incluido en la carpeta)

---

## Instalación

Solo la primera vez:

```bash
pip install gradio langchain langchain-anthropic langgraph databricks-sql-connector plotly python-dotenv requests
```

---

## Arrancar la aplicación

```bash
cd celta_cantera_app
python frontend_new.py
```

Abrir en el navegador: **http://localhost:7860**

---

## Uso

### Pantalla de inicio
Al abrir la aplicación aparece la pantalla de inicio. Pulsa **"Entrar al sistema →"** para acceder al asistente.

### Chat
Escribe cualquier consulta en lenguaje natural. Ejemplos:

| Consulta | Qué muestra |
|---|---|
| `¿Qué perfiles están disponibles?` | Lista de perfiles GPS definidos |
| `¿Qué jugadores encajan como central?` | Candidatos ordenados por similitud |
| `Variables GPS del perfil mediocentro` | Métricas que definen el perfil |
| `Radar de Ilaix Moriba` | Gráfica polar GPS del jugador |
| `¿En qué perfil encaja mejor Hugo Perez?` | Clasificación del jugador |
| `Compara a Gavira con Moriba en carrilero` | Comparativa de métricas GPS |
| `Tabla completa de delantero_centro` | Clasificación con todos los jugadores |
| `Scatter de candidatos a extremo` | Dispersión ranking vs similitud |

### Panel de visualización
Las gráficas aparecen automáticamente en el panel derecho después de cada consulta relevante.

---

## Perfiles disponibles

| Perfil | Jugadores de referencia |
|---|---|
| `carrilero` | Álvaro Núñez, Mingueza, Ristic, Carreira, Javi Rueda |
| `central` | J. Rodriguez, Mingueza, Starfelt, Yoel Lago, Manu Fernandez, Aidoo, C. Dominguez |
| `mediocentro` | Moriba, M. Roman, Sotelo, Beltrán, Vecino, D. Rodriguez, O. Marcos, Antañon |
| `delantero_centro` | B. Iglesias, Aspas, Jutgla, P. Duran |
| `mediapunta` | Fer Lopez, Oscar Marcos, Iago Aspas |
| `extremo` | Swedberg, Zaragoza, El-Abdellaoui, H. Alvarez, Fer Lopez |
| `ilaix_moriba` | Perfil individual — Ilaix Moriba |
| `bryan_zaragoza` | Perfil individual — Bryan Zaragoza |

---

## Estructura de archivos

```
celta_cantera_app/
├── backend.py          — Lógica: conexión Databricks, agente Claude, tools SQL
├── frontend_new.py     — Interfaz: Gradio, visualizaciones interactivas
├── tfg_celta.env       — Credenciales (no compartir)
├── celta_logo.png      — Logo del Celta
├── portada_bg.jpg      — Foto de portada
├── cantera_1.jpg       — Fotos de cantera (opcionales)
├── cantera_2.jpg
├── cantera_3.jpg
└── README.md
```

---

## Arquitectura técnica

```
Usuario (chat)
    │
    ▼
Gradio (frontend_new.py)
    │
    ▼
LangChain + Claude Haiku (backend.py)
    │  ├── sql_query()           → consultas a tablas silver
    │  └── buscar_jugador()      → búsqueda por nombre
    │
    ▼
Databricks Unity Catalog (Azure)
    ├── dev_silver.slv_catapult.competitive_profile
    ├── dev_silver.slv_catapult.activity_data_kpis
    └── dev_silver.slv_perfilado_jugadores.*
```

---

## Datos

- **Fuente:** Catapult GPS — datos reales de partidos del RC Celta de Vigo y cantera
- **Temporada activa:** 25-26
- **Tablas principales:**
  - `clasificacion_posiciones_catapult` — jugadores clasificados por posición
  - `similitud_catapult` — similitud ponderada contra perfiles
  - `relevancia_variables_catapult` — variables GPS más definitorias
  - `perfil_referencia_catapult` — centroides de perfiles


