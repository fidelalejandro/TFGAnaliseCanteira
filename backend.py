"""
backend.py — RC Celta de Vigo — Sistema de Análisis de Cantera
Lógica de negocio: conexión SQL, herramientas LangChain, agente Claude.
"""

from dotenv import load_dotenv
import os
import json
import requests

# .env en la misma carpeta que backend.py
_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_DIR, "tfg_celta.env"))

DATABRICKS_HOST  = os.getenv("DATABRICKS_HOST", "").replace("https://", "")
DATABRICKS_PATH  = os.getenv("DATABRICKS_HTTP_PATH")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
ANTHROPIC_KEY    = os.getenv("ANTHROPIC_API_KEY")
CLUSTER_ID       = "0812-085217-6lzjs94c"
SEASON           = "25-26"
CATALOG          = "dev_silver"
SCHEMA           = "slv_perfilado_jugadores"

# ── Conexión SQL ──────────────────────────────────────────────────────────────

from databricks import sql as dbsql

def run_query(query: str) -> list:
    try:
        with dbsql.connect(
            server_hostname=DATABRICKS_HOST,
            http_path=DATABRICKS_PATH,
            access_token=DATABRICKS_TOKEN,
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                cols = [d[0] for d in cursor.description]
                return [dict(zip(cols, row)) for row in cursor.fetchall()]
    except Exception as e:
        return [{"error": str(e)}]

# ── Herramientas LangChain ────────────────────────────────────────────────────

from langchain_core.tools import tool

@tool
def sql_query(query: str) -> str:
    """
    Ejecuta una query SQL contra las tablas silver de Databricks y devuelve el resultado.

    Tablas en dev_silver.slv_perfilado_jugadores:
    - clasificacion_posiciones_catapult: jugadores clasificados por posicion.
      Cols: athlete_id, athlete_name, first_name, last_name, position,
      activity_team_name, activity_team_id, n_partidos, posicion_final,
      nivel_confianza, ncc_knn_coinciden, posicion_ncc, posicion_knn,
      vecinos_knn, season, sim_ncc_<posicion>, prob_ncc_<posicion>, votos_knn_<posicion>
    - perfil_referencia_catapult: perfiles creados.
      Cols: nombre_perfil, tipo_perfil, n_jugadores_ref, ids_jugadores_ref, season, fecha_calculo
    - relevancia_variables_catapult: relevancia de variables por perfil.
      Cols: rank_relevancia, variable, z_vs_contexto, score_relevancia, clasificacion, direccion, cv_intragrupo, nombre_perfil, season
    - similitud_catapult: similitud entre jugadores.
      Cols: athlete_id, athlete_name, similitud_ponderada, distancia_ponderada, rank, rank_coseno, diff_rank, nombre_perfil, season
    - cohesion_perfil_referencia_catapult: cohesion interna de perfiles.
      Cols: variable, media_grupo, std_intragrupo, cv_intragrupo, nombre_perfil, season

    Equipos (activity_team_id): 1=RC Celta, 2=Celta B, 3=Juvenil A, 4=Juvenil B, 5=Cadete A, 6=Cadete B/C
    Temporada activa: 25-26
    """
    resultado = run_query(query)
    if not resultado:
        return "La consulta no devolvio resultados."
    if "error" in resultado[0]:
        return f"Error en la query: {resultado[0]['error']}"
    return json.dumps(resultado, ensure_ascii=False, default=str, indent=2)


@tool
def buscar_jugador_catapult(nombre: str) -> str:
    """
    Busca un jugador en Catapult por nombre o apellido.
    Devuelve athlete_id, equipo y posicion.
    """
    query = f"""
        SELECT DISTINCT athlete_id, athlete_name, first_name, last_name,
               position, activity_team_name
        FROM dev_silver.slv_catapult.activity_data_kpis
        WHERE activity_team_name IN (
            'RC Celta de Vigo','Celta B','Celta Vigo Juvenil A',
            'Celta de Vigo Juv B','Celta de Vigo Cad A','Celta de Vigo Cad B'
        )
        AND (
            lower(athlete_name) LIKE '%{nombre.lower()}%'
            OR lower(last_name)  LIKE '%{nombre.lower()}%'
            OR lower(first_name) LIKE '%{nombre.lower()}%'
        )
        LIMIT 5
    """
    resultado = run_query(query)
    if not resultado or "error" in resultado[0]:
        return f"No encontre ningun jugador con el nombre '{nombre}'."
    return json.dumps(resultado, ensure_ascii=False, default=str, indent=2)



# ── Agente ────────────────────────────────────────────────────────────────────

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    api_key=ANTHROPIC_KEY,
    max_tokens=1000,
)

tools = [sql_query, buscar_jugador_catapult]

SYSTEM_PROMPT = """Eres el asistente de analisis de cantera del RC Celta de Vigo.
Ayudas al cuerpo tecnico a identificar jugadores de cantera que encajan en perfiles
de posicion del primer equipo y del Celta B.

Tienes acceso a datos reales de rendimiento fisico GPS (Catapult) mediante SQL.

Instrucciones generales:
- Usa SIEMPRE las herramientas para consultar datos antes de responder
- Se conciso y directo, como un analista deportivo
- Incluye siempre nombre, equipo y nivel de confianza al mostrar jugadores
- Temporada activa: 25-26
- Maximo 3-4 parrafos por respuesta

Perfiles disponibles (usar estos nombres exactos en SQL y en bloques grafica):
  carrilero, central, mediocentro, delantero_centro, mediapunta,
  extremo, ilaix_moriba, bryan_zaragoza

Instrucciones para graficas:
El sistema genera graficas automaticamente. Cuando tu respuesta incluya datos
relevantes, añade AL FINAL un bloque <grafica> con el tipo correcto.
Formato exacto (JSON en una sola linea, sin espacios extra):

Candidatos por posicion:
<grafica>{"tipo":"clasificacion","posicion":"carrilero"}</grafica>

Variables GPS de un perfil:
<grafica>{"tipo":"relevancia","perfil":"carrilero"}</grafica>

Radar GPS de un jugador:
<grafica>{"tipo":"radar","jugador":"Ilaix Moriba"}</grafica>

Comparativa entre dos jugadores:
<grafica>{"tipo":"comparativa","jugador1":"Moriba","jugador2":"Gavira","perfil":"carrilero"}</grafica>

Tabla completa de clasificacion:
<grafica>{"tipo":"tabla","perfil":"central","equipo":"Todos"}</grafica>

Scatter ranking vs similitud de un perfil:
<grafica>{"tipo":"scatter","perfil":"extremo"}</grafica>

Reglas:
- Solo incluye el bloque si tienes datos reales de esa consulta
- Usa exactamente los tipos: clasificacion, relevancia, radar, comparativa, tabla, scatter
- NO menciones que no puedes generar graficas, el sistema las genera automaticamente
- Usa los nombres de perfil exactos sin espacios (delantero_centro, ilaix_moriba, bryan_zaragoza)
"""

agent = create_react_agent(llm, tools)



def _extraer_datos_grafica(mensaje: str) -> dict | None:
    """Fallback: extrae datos para grafica por palabras clave si Claude no incluyó bloque."""
    import re as _re
    msg = mensaje.lower()
    posiciones = ['carrilero', 'central', 'mediocentro', 'delantero_centro',
                  'mediapunta', 'extremo', 'ilaix_moriba', 'bryan_zaragoza']

    # Radar
    if any(p in msg for p in ['radar', 'grafico polar']):
        m = _re.search(r'radar (?:de |gps de )?([a-záéíóúñ ]+)', msg)
        if m:
            return {"tipo": "radar", "jugador": m.group(1).strip().title()}

    # Comparativa
    if any(p in msg for p in ['compara', 'comparativa', ' vs ', 'versus']):
        m = _re.search(r'compara(?:r)?(?: a)? ([a-záéíóúñ]+)(?: (?:con|vs|y) ([a-záéíóúñ]+))?', msg)
        if m:
            j1 = m.group(1).strip().title() if m.group(1) else ""
            j2 = m.group(2).strip().title() if m.group(2) else ""
            perfil = next((p for p in posiciones if p in msg), "")
            if j1 and j2 and perfil:
                return {"tipo": "comparativa", "jugador1": j1, "jugador2": j2, "perfil": perfil}

    # Tabla
    if any(p in msg for p in ['tabla', 'clasificacion completa']):
        perfil = next((p for p in posiciones if p in msg), "")
        if perfil:
            return {"tipo": "tabla", "perfil": perfil, "equipo": "Todos"}

    for pos in posiciones:
        if pos in msg:
            # Relevancia
            if any(p in msg for p in ['variable', 'metrica', 'define', 'importante', 'gps']):
                try:
                    datos = run_query(
                        f"SELECT variable, score_relevancia, clasificacion, z_vs_contexto "
                        f"FROM {CATALOG}.{SCHEMA}.relevancia_variables_catapult "
                        f"WHERE nombre_perfil='{pos}' AND season='{SEASON}' "
                        f"ORDER BY rank_relevancia LIMIT 10"
                    )
                    if datos and "error" not in datos[0]:
                        return {"tipo": "relevancia", "perfil": pos, "datos": datos}
                except Exception:
                    pass
            # Clasificacion
            try:
                equipos_map = {
                    'celta b':   'Celta B',
                    'juvenil a': 'Celta Vigo Juvenil A',
                    'juvenil b': 'Celta de Vigo Juvenil B',
                    'cadete a':  'Celta de Vigo Cadete A',
                    'cadete b':  'Celta de Vigo Cadete B/C',
                }
                equipo = next((v for k, v in equipos_map.items() if k in msg), None)
                filtro = f"AND activity_team_name='{equipo}'" if equipo else ""
                conf   = "AND nivel_confianza='alta'" if 'alta confianza' in msg else ""
                datos  = run_query(
                    f"SELECT athlete_name, first_name, last_name, "
                    f"activity_team_name, nivel_confianza, sim_ncc_{pos} "
                    f"FROM {CATALOG}.{SCHEMA}.clasificacion_posiciones_catapult "
                    f"WHERE posicion_final='{pos}' AND season='{SEASON}' {filtro} {conf} "
                    f"ORDER BY sim_ncc_{pos} DESC LIMIT 10"
                )
                if datos and "error" not in datos[0]:
                    return {"tipo": "clasificacion", "posicion": pos, "datos": datos}
            except Exception:
                pass

    return None


def _construir_datos_grafica(instruccion: dict) -> dict | None:
    """Convierte la instruccion de Claude en datos para construir_figura del frontend."""
    tipo = instruccion.get("tipo")
    if tipo == "clasificacion":
        pos = instruccion.get("posicion", "")
        return _extraer_datos_grafica(pos) if pos else None
    elif tipo == "relevancia":
        perfil = instruccion.get("perfil", "")
        return _extraer_datos_grafica(f"variables gps {perfil}") if perfil else None
    elif tipo in ("radar", "comparativa", "tabla", "scatter", "boxplot", "linea", "heatmap"):
        # Para estos tipos el frontend usa los params del dict directamente
        return instruccion
    return None

def chat(mensaje: str, historial: list) -> tuple:
    """
    Procesa un mensaje y devuelve (respuesta, datos_grafica).
    datos_grafica es None si no hay grafica que mostrar.
    """
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    for h in historial[-12:]:
        if isinstance(h, dict):
            if h.get("role") == "user" and h.get("content"):
                messages.append(HumanMessage(content=h["content"]))
            elif h.get("role") == "assistant" and h.get("content"):
                messages.append(AIMessage(content=h["content"]))

    messages.append(HumanMessage(content=mensaje))

    try:
        resultado     = agent.invoke({"messages": messages})
        respuesta_raw = resultado["messages"][-1].content

        # Extraer bloque <grafica> si Claude lo incluyó
        import re as _re
        match = _re.search(r"<grafica>(.*?)</grafica>", respuesta_raw, _re.DOTALL)
        if match:
            bloque = match.group(1).strip()
            print(f"[GRAFICA] Bloque detectado: {bloque}")
            try:
                instruccion = json.loads(bloque)
                print(f"[GRAFICA] Instruccion parseada: {instruccion}")
                datos = _construir_datos_grafica(instruccion)
                print(f"[GRAFICA] Datos construidos: tipo={instruccion.get('tipo')}, datos={bool(datos)}")
                respuesta = respuesta_raw.replace(match.group(0), "").strip()
            except Exception as ex:
                print(f"[GRAFICA] Error parseando bloque: {ex}")
                datos     = _extraer_datos_grafica(mensaje)
                respuesta = respuesta_raw.replace(match.group(0), "").strip()
        else:
            print(f"[GRAFICA] No se encontró bloque <grafica> en la respuesta")
            datos     = _extraer_datos_grafica(mensaje)
            respuesta = respuesta_raw

        # Limpiar bloques <grafica> del historial para Claude
        for h in messages:
            if hasattr(h, 'content') and isinstance(h.content, str):
                h.content = _re.sub(r"<grafica>.*?</grafica>", "", h.content, flags=_re.DOTALL).strip()

        return respuesta, datos
    except Exception as e:
        return f"Error: {str(e)}", None

