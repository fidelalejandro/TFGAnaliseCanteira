# RC Celta de Vigo — Sistema de Análisis de Cantera  Herramienta de apoyo al análisis de jugadores de cantera del RC Celta de Vigo basada en datos GPS Catapult, algoritmos de *matching*, visualización interactiva y explicación mediante inteligencia artificial generativa.  El sistema permite consultar jugadores, comparar perfiles físicos, generar rankings de similitud y obtener respuestas en lenguaje natural a partir de datos previamente procesados en Databricks.  ---  ## Funcionalidades principales  - Consulta de jugadores y métricas GPS. - Búsqueda de jugadores por nombre o posición. - Consulta de perfiles físicos disponibles. - Identificación de jugadores similares a un perfil de referencia. - Comparación entre jugadores. - Consulta de variables GPS más relevantes para cada perfil. - Clasificación funcional de jugadores según perfiles definidos. - Generación automática de visualizaciones interactivas. - Respuestas en lenguaje natural mediante Claude Haiku.  ---  ## Requisitos  Antes de ejecutar la aplicación es necesario disponer de:  - Python 3.10 o superior. - Git. - Conexión a Internet. - Acceso al clúster de Databricks utilizado por el proyecto. - Clave de API de Anthropic para el uso de Claude. - Archivo `tfg_celta.env` con las credenciales necesarias.  > **Importante:** el archivo `tfg_celta.env` contiene credenciales sensibles y no debe subirse al repositorio.  ---  ## Instalación  Clonar el repositorio:  bash
git clone https://github.com/fidelalejandro/TFG_Analise_Canteira.git
cd TFG_Analise_Canteira
 Crear y activar un entorno virtual: bash
python3 -m venv venv
source venv/bin/activate
 En Windows: bash
python -m venv venv
venv\Scripts\activate
 Instalar las dependencias del proyecto: bash
pip install -r requirements.txt
 ---  ## Configuración de credenciales  La aplicación utiliza un archivo de entorno llamado `tfg_celta.env`.  Este archivo debe situarse en la raíz del proyecto y contener las siguientes variables: env
DATABRICKS_HOST=...
DATABRICKS_HTTP_PATH=...
DATABRICKS_TOKEN=...
ANTHROPIC_API_KEY=...
 Estas credenciales deben solicitarse al administrador del proyecto.  ---  ## Ejecución de la aplicación  Desde la raíz del proyecto, ejecutar: bash
python3 frontend_new.py
 En Windows también se puede ejecutar: bash
python frontend_new.py
 Por defecto, la aplicación estará disponible en: text
http://localhost:7860
 Al abrir la aplicación en el navegador aparecerá una pantalla de bienvenida. Para acceder al asistente, pulsar el botón: text
Entrar al sistema →
 ---  ## Uso de la herramienta  La herramienta funciona mediante una interfaz conversacional. El usuario puede escribir preguntas en lenguaje natural y el sistema recupera datos desde Databricks, genera una respuesta textual y, cuando procede, muestra una visualización interactiva.  Ejemplos de consultas:  | Consulta | Resultado esperado | |---|---| | `¿Qué perfiles están disponibles?` | Lista de perfiles GPS definidos | | `¿Qué jugadores encajan como central?` | Ranking de candidatos ordenados por similitud | | `Variables GPS del perfil mediocentro` | Métricas más relevantes del perfil | | `Radar de Ilaix Moriba` | Gráfico radar con el perfil GPS del jugador | | `¿En qué perfil encaja mejor Hugo Pérez?` | Clasificación funcional del jugador | | `Compara a Gavira con Moriba` | Comparativa de métricas GPS | | `Tabla completa de delantero centro` | Clasificación completa de ese perfil | | `Scatter de candidatos a extremo` | Gráfico de dispersión con ranking y similitud |  ---  ## Panel de visualización  Las visualizaciones aparecen automáticamente en el panel derecho de la interfaz cuando la consulta requiere una representación gráfica.  Entre los tipos de visualización soportados se incluyen:  - Gráficos de barras. - Gráficos radar. - Tablas completas. - Rankings de similitud. - Comparativas entre jugadores. - Gráficos de dispersión.  Las gráficas se generan con Plotly a partir de los datos recuperados por el sistema.  ---  ## Perfiles disponibles  | Perfil | Jugadores de referencia | |---|---| | `carrilero` | Álvaro Núñez, Mingueza, Ristic, Carreira, Javi Rueda | | `central` | J. Rodríguez, Mingueza, Starfelt, Yoel Lago, Manu Fernández, Aidoo, C. Domínguez | | `mediocentro` | Moriba, M. Román, Sotelo, Beltrán, Vecino, D. Rodríguez, O. Marcos, Antañón | | `delantero_centro` | B. Iglesias, Aspas, Jutglà, P. Durán | | `mediapunta` | Fer López, Óscar Marcos, Iago Aspas | | `extremo` | Swedberg, Zaragoza, El-Abdellaoui, H. Álvarez, Fer López | | `ilaix_moriba` | Perfil individual — Ilaix Moriba | | `bryan_zaragoza` | Perfil individual — Bryan Zaragoza |  ---  ## Estructura de archivos text
TFG_Analise_Canteira/
├── backend.py              # Lógica principal: Databricks, Claude, herramientas SQL
├── frontend_new.py         # Interfaz Gradio y visualizaciones Plotly
├── requirements.txt        # Dependencias del proyecto
├── tfg_celta.env           # Credenciales locales, no incluir en Git
├── celta_logo.png          # Logotipo utilizado en la interfaz
├── portada_bg.jpg          # Imagen de portada
├── cantera_1.jpg           # Imágenes ilustrativas opcionales
├── cantera_2.jpg
├── cantera_3.jpg
└── README.md
 ---  ## Arquitectura técnica text
Usuario
  │
  ▼
Gradio — frontend_new.py
  │
  ▼
Backend Python — backend.py
  │
  ├── Herramientas SQL
  ├── Búsqueda de jugadores
  ├── Preparación de datos para visualización
  │
  ▼
LangChain / LangGraph
  │
  ▼
Claude Haiku
  │
  ▼
Respuesta en lenguaje natural
 La capa de datos se basa en Databricks Unity Catalog: text
Databricks Unity Catalog
├── dev_silver.slv_catapult
└── dev_silver.slv_perfilado_jugadores
 ---  ## Datos  La aplicación trabaja sobre datos previamente procesados en Databricks. Los datos originales proceden de registros GPS Catapult y de procesos analíticos desarrollados durante el proyecto.  Entre las tablas principales empleadas por el sistema se incluyen:  - Tablas de métricas GPS agregadas. - Tablas de perfiles de referencia. - Tablas de relevancia de variables. - Tablas de similitud entre jugadores y perfiles. - Tablas de clasificación funcional.  > Los datos reales de jugadores pertenecen al RC Celta de Vigo y no se incluyen en el repositorio.  ---  ## Tecnologías utilizadas  - Python - Databricks - Databricks SQL Connector - Gradio - Plotly - LangChain - LangGraph - Anthropic Claude Haiku - python-dotenv  ---  ## Seguridad  Este repositorio no debe contener:  - Credenciales reales. - Tokens de Databricks. - Claves de API de Anthropic. - Datos físicos reales de jugadores. - Archivos `.env` con configuración sensible.  El archivo `tfg_celta.env` debe mantenerse siempre fuera del control de versiones.  ---  ## Aviso  Este proyecto fue desarrollado en el contexto de un Trabajo Fin de Grado. El código se publica únicamente con fines de evaluación académica.  Los datos deportivos utilizados por el sistema son propiedad del RC Celta de Vigo y no forman parte del repositorio.
:::
