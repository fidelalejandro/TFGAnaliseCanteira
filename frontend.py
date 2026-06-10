"""
frontend_new.py — RC Celta de Vigo — Sistema de Análisis de Cantera
Diseño: splash con foto + transparencia, sidebar, chat + panel viz lateral.
Ejecutar: python frontend_new.py
"""

import gradio as gr
import plotly.graph_objects as go
import base64, os, json, threading
from backend import chat, run_query, CATALOG, SCHEMA, SEASON

# ── Paleta ────────────────────────────────────────────────────────────────────
CELESTE   = "#6DC8F3"
CELESTE_L = "#D6EFFA"
CELESTE_D = "#1A9FD4"
AZUL      = "#003DA6"
BLANCO    = "#FFFFFF"
TEXTO     = "#0a1628"
TEXTO_SEC = "#374151"
BORDE     = "#BFDBEE"
BG        = "#F0F8FF"
BOT_BG    = "#FFFFFF"

# ── Logo ──────────────────────────────────────────────────────────────────────
def _logo_b64(height="36px") -> str:
    for ext in [".png", ".jpg", ".jpeg", ".svg", ".webp"]:
        path = f"celta_logo{ext}"
        if os.path.exists(path):
            mime = {".png":"image/png",".jpg":"image/jpeg",
                    ".jpeg":"image/jpeg",".svg":"image/svg+xml",
                    ".webp":"image/webp"}.get(ext,"image/png")
            with open(path,"rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f'<img src="data:{mime};base64,{b64}" style="height:{height};width:auto;object-fit:contain;" />'
    # Fallback SVG escudo
    svg = """<svg viewBox="0 0 40 44" xmlns="http://www.w3.org/2000/svg">
      <path d="M20 1L39 9L39 27C39 37 20 43 20 43C20 43 1 37 1 27L1 9Z"
            fill="#003DA6" stroke="#6DC8F3" stroke-width="1.5"/>
      <text x="20" y="30" text-anchor="middle" font-family="Georgia,serif"
            font-size="18" font-weight="bold" fill="#6DC8F3">C</text>
    </svg>"""
    b64 = base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}" style="height:{height};width:auto;" />'

LOGO_LG  = _logo_b64("90px")
LOGO_SM  = _logo_b64("32px")
LOGO_AV  = _logo_b64("22px")   # avatar en burbujas

# ── Foto de portada ───────────────────────────────────────────────────────────
def _splash_bg() -> str:
    """Busca portada_bg.jpg/png en el directorio. Si no, usa URL de Unsplash."""
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        path = f"portada_bg{ext}"
        if os.path.exists(path):
            mime = {".jpg":"image/jpeg",".jpeg":"image/jpeg",
                    ".png":"image/png",".webp":"image/webp"}.get(ext,"image/jpeg")
            with open(path,"rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"data:{mime};base64,{b64}"
    return "https://images.unsplash.com/photo-1529900748604-07564a03e7a6?w=1400&q=85"

SPLASH_BG = _splash_bg()

# ── Helpers SQL ───────────────────────────────────────────────────────────────
def _safe_query(sql):
    try:
        r = run_query(sql)
        if r and "error" not in r[0]:
            return r
    except Exception:
        pass
    return []

def obtener_perfiles():
    rows = _safe_query(
        f"SELECT DISTINCT nombre_perfil FROM {CATALOG}.{SCHEMA}.perfil_referencia_catapult "
        f"WHERE season='{SEASON}' ORDER BY nombre_perfil"
    )
    return [r["nombre_perfil"] for r in rows] if rows else []

def obtener_stats():
    p = _safe_query(f"SELECT COUNT(DISTINCT nombre_perfil) as n FROM {CATALOG}.{SCHEMA}.perfil_referencia_catapult WHERE season='{SEASON}'")
    j = _safe_query(f"SELECT COUNT(DISTINCT athlete_id) as n FROM {CATALOG}.{SCHEMA}.clasificacion_posiciones_catapult WHERE season='{SEASON}'")
    a = _safe_query(f"SELECT COUNT(*) as n FROM {CATALOG}.{SCHEMA}.clasificacion_posiciones_catapult WHERE season='{SEASON}' AND nivel_confianza='alta'")
    return {
        "perfiles":  p[0]["n"] if p else "—",
        "jugadores": j[0]["n"] if j else "—",
        "alta":      a[0]["n"] if a else "—",
    }

# ── Columnas GPS ──────────────────────────────────────────────────────────────
_RADAR_COLS = {
    "total_distance":    "Distancia",
    "HMLD":              "HMLD",
    "max_velocity":      "Vel. Máx.",
    "max_acceleration":  "Acel. Máx.",
    "max_deceleration":  "Decel. Máx.",
    "explosive_efforts": "Explosividad",
    "HSR":               "HSR",
}
_GPS_COLS_INV = {
    "match_total_distance":    "total_distance",
    "match_HMLD":              "HMLD",
    "match_max_velocity":      "max_velocity",
    "match_max_acceleration":  "max_acceleration",
    "match_max_deceleration":  "max_deceleration",
    "match_acc+dcc>3_distance":"acc+dcc>3_distance",
    "match_acc>3_count":       "acc>3_count",
    "match_dcc>3_count":       "dcc>3_count",
    "match_acc+dcc>3_count":   "acc+dcc>3_count",
    "match_explosive_efforts": "explosive_efforts",
    "match_HSR":               "HSR",
}

# ── Gráficas Plotly ───────────────────────────────────────────────────────────
def _fig_layout(fig, title, xlab="", height=380):
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXTO, family="Inter,Arial"), x=0),
        xaxis=dict(title=xlab, title_font=dict(color=TEXTO_SEC, size=11),
                   gridcolor="#E0EEF8", tickfont=dict(color=TEXTO_SEC, size=11)),
        yaxis=dict(tickfont=dict(color=TEXTO, size=11)),
        height=height, plot_bgcolor=BLANCO, paper_bgcolor=BLANCO,
        margin=dict(l=8, r=80, t=50, b=36),
        font=dict(family="Inter,Arial", size=11, color=TEXTO), showlegend=False,
    )
    return fig

def grafica_barras_candidatos(perfil: str):
    if not perfil:
        return go.Figure().update_layout(title="Selecciona un perfil",
                                         paper_bgcolor=BLANCO, plot_bgcolor=BLANCO)
    sim_col = f"sim_ncc_{perfil}"
    datos = _safe_query(
        f"SELECT athlete_name, first_name, last_name, activity_team_name, "
        f"nivel_confianza, {sim_col} "
        f"FROM {CATALOG}.{SCHEMA}.clasificacion_posiciones_catapult "
        f"WHERE posicion_final='{perfil}' AND season='{SEASON}' "
        f"ORDER BY {sim_col} DESC NULLS LAST LIMIT 12"
    )
    if not datos:
        datos = _safe_query(
            f"SELECT c.athlete_name, c.first_name, c.last_name, c.activity_team_name, "
            f"c.nivel_confianza, s.similitud_ponderada AS {sim_col} "
            f"FROM {CATALOG}.{SCHEMA}.clasificacion_posiciones_catapult c "
            f"JOIN {CATALOG}.{SCHEMA}.similitud_catapult s "
            f"ON c.athlete_id=s.athlete_id AND s.nombre_perfil='{perfil}' AND s.season='{SEASON}' "
            f"WHERE c.posicion_final='{perfil}' AND c.season='{SEASON}' "
            f"ORDER BY s.similitud_ponderada DESC NULLS LAST LIMIT 12"
        )
    if not datos:
        return go.Figure().update_layout(title=f"Sin datos para '{perfil}'",
                                         paper_bgcolor=BLANCO, plot_bgcolor=BLANCO)
    nombres   = [f"{d.get('first_name','')} {d.get('last_name','')}".strip()
                 or d.get('athlete_name','') for d in datos]
    equipos   = [d.get('activity_team_name','') for d in datos]
    confianza = [d.get('nivel_confianza','') for d in datos]
    sims      = [float(d.get(sim_col, 0) or 0) for d in datos]
    colores   = [CELESTE_D if c == 'alta' else CELESTE for c in confianza]
    etiquetas = [f"{n}  ·  {e}" for n, e in zip(nombres, equipos)]
    fig = go.Figure(go.Bar(
        x=sims, y=etiquetas, orientation='h',
        marker=dict(color=colores, line=dict(color=BORDE, width=0.4)),
        text=[f"{s:.3f}" for s in sims], textposition='outside',
        textfont=dict(color=TEXTO_SEC, size=10),
        hovertemplate='<b>%{y}</b><br>Similitud: %{x:.3f}<extra></extra>',
    ))
    fig.update_layout(yaxis=dict(autorange='reversed', tickfont=dict(color=TEXTO, size=11)),
                      annotations=[dict(x=1.01, y=1.06, xref='paper', yref='paper',
                          showarrow=False, align='left', font=dict(size=10, color=TEXTO_SEC),
                          text=f'<span style="color:{CELESTE_D}">■</span> Alta  '
                               f'<span style="color:{CELESTE}">■</span> Normal')])
    return _fig_layout(fig, f"Candidatos — <b>{perfil.capitalize()}</b>",
                       xlab="Similitud al perfil", height=max(340, len(datos)*44+70))

def grafica_radar_jugador(nombre: str):
    if not nombre.strip():
        return go.Figure().update_layout(title="Introduce el nombre de un jugador",
                                         paper_bgcolor=BLANCO)
    cols_list = list(_RADAR_COLS.keys())
    cols_avg  = ", ".join([f"AVG({c}) AS avg_{c}" for c in cols_list])
    cols_min  = ", ".join([f"MIN({c}) AS min_{c}" for c in cols_list])
    cols_max  = ", ".join([f"MAX({c}) AS max_{c}" for c in cols_list])
    cols_jug  = ", ".join([f"AVG({c}) AS {c}" for c in cols_list])
    datos_jug = _safe_query(
        f"SELECT athlete_name, {cols_jug} "
        f"FROM dev_silver.slv_catapult.activity_data_kpis "
        f"WHERE (lower(athlete_name) LIKE '%{nombre.lower()}%' "
        f"    OR lower(last_name)    LIKE '%{nombre.lower()}%' "
        f"    OR lower(first_name)   LIKE '%{nombre.lower()}%') "
        f"GROUP BY athlete_name LIMIT 1"
    )
    if not datos_jug:
        return go.Figure().update_layout(title=f"'{nombre}' no encontrado",
                                         paper_bgcolor=BLANCO)
    jug       = datos_jug[0]
    nombre_ok = jug.get("athlete_name", nombre)
    stats_eq  = _safe_query(f"SELECT {cols_avg},{cols_min},{cols_max} FROM dev_silver.slv_catapult.activity_data_kpis")
    stats     = stats_eq[0] if stats_eq else {}
    etiquetas, vals_jug, vals_med = [], [], []
    for col, label in _RADAR_COLS.items():
        v     = float(jug.get(col) or 0)
        v_avg = float(stats.get(f"avg_{col}") or 0)
        v_min = float(stats.get(f"min_{col}") or 0)
        v_max = float(stats.get(f"max_{col}") or 1)
        rng   = v_max - v_min if v_max != v_min else 1
        etiquetas.append(label)
        vals_jug.append(max(0, min(100, round((v - v_min) / rng * 100, 1))))
        vals_med.append(max(0, min(100, round((v_avg - v_min) / rng * 100, 1))))
    etiquetas += [etiquetas[0]]; vals_jug += [vals_jug[0]]; vals_med += [vals_med[0]]
    fig = go.Figure([
        go.Scatterpolar(r=vals_med, theta=etiquetas, name="Media global",
                        fill='toself', fillcolor="rgba(109,200,243,0.08)",
                        line=dict(color=BORDE, width=1.5, dash='dot')),
        go.Scatterpolar(r=vals_jug, theta=etiquetas, name=nombre_ok,
                        fill='toself', fillcolor="rgba(26,159,212,0.18)",
                        line=dict(color=CELESTE_D, width=2),
                        marker=dict(color=CELESTE_D, size=6)),
    ])
    fig.update_layout(
        title=dict(text=f"Radar GPS — <b>{nombre_ok}</b>",
                   font=dict(size=14, color=TEXTO, family="Inter,Arial"), x=0),
        polar=dict(bgcolor=BLANCO,
                   radialaxis=dict(visible=True, range=[0,100],
                                   tickvals=[25,50,75,100],
                                   gridcolor=BORDE, tickfont=dict(color=TEXTO_SEC, size=9)),
                   angularaxis=dict(tickfont=dict(color=TEXTO, size=10), gridcolor=BORDE)),
        showlegend=True,
        legend=dict(font=dict(color=TEXTO_SEC, size=10), bgcolor=BLANCO,
                    bordercolor=BORDE, borderwidth=1),
        paper_bgcolor=BLANCO, height=400,
        margin=dict(l=50, r=50, t=60, b=36),
        font=dict(family="Inter,Arial", size=11, color=TEXTO),
    )
    return fig

def grafica_comparativa(j1: str, j2: str, perfil: str):
    if not j1.strip() or not j2.strip() or not perfil:
        return go.Figure().update_layout(title="Introduce dos jugadores y un perfil",
                                         paper_bgcolor=BLANCO, plot_bgcolor=BLANCO)
    vars_p = _safe_query(
        f"SELECT variable FROM {CATALOG}.{SCHEMA}.relevancia_variables_catapult "
        f"WHERE nombre_perfil='{perfil}' AND season='{SEASON}' ORDER BY rank_relevancia LIMIT 8"
    )
    if not vars_p:
        return go.Figure().update_layout(title=f"Sin variables para '{perfil}'",
                                         paper_bgcolor=BLANCO, plot_bgcolor=BLANCO)
    pares = [(r["variable"], _GPS_COLS_INV[r["variable"]]) for r in vars_p if r["variable"] in _GPS_COLS_INV]
    if not pares:
        return go.Figure().update_layout(title="No se pudieron mapear variables",
                                         paper_bgcolor=BLANCO, plot_bgcolor=BLANCO)
    cols_sql = ", ".join([f"AVG({c}) AS {c}" for _, c in pares])
    def get_m(n):
        rows = _safe_query(
            f"SELECT athlete_name, {cols_sql} "
            f"FROM dev_silver.slv_catapult.activity_data_kpis "
            f"WHERE (lower(athlete_name) LIKE '%{n.lower()}%' "
            f"    OR lower(last_name)    LIKE '%{n.lower()}%' "
            f"    OR lower(first_name)   LIKE '%{n.lower()}%') "
            f"GROUP BY athlete_name LIMIT 1"
        )
        return rows[0] if rows else None
    m1, m2 = get_m(j1), get_m(j2)
    if not m1:
        return go.Figure().update_layout(title=f"Sin datos para '{j1}'",
                                         paper_bgcolor=BLANCO, plot_bgcolor=BLANCO)
    if not m2:
        return go.Figure().update_layout(title=f"Sin datos para '{j2}'",
                                         paper_bgcolor=BLANCO, plot_bgcolor=BLANCO)
    n1 = m1.get("athlete_name", j1); n2 = m2.get("athlete_name", j2)
    ets = [m.replace("match_","").replace("_"," ").title() for m, _ in pares]
    v1  = [float(m1.get(c) or 0) for _, c in pares]
    v2  = [float(m2.get(c) or 0) for _, c in pares]
    v1n, v2n = [], []
    for a, b in zip(v1, v2):
        mx = max(a, b, 1e-9); v1n.append(round(a/mx,4)); v2n.append(round(b/mx,4))
    fig = go.Figure([
        go.Bar(name=n1, x=ets, y=v1n, marker_color=CELESTE_D,
               text=[f"{v:.1f}" for v in v1],
               hovertemplate='<b>%{x}</b><br>Real: %{text}<br>Norm: %{y:.2f}<extra></extra>'),
        go.Bar(name=n2, x=ets, y=v2n, marker_color=CELESTE,
               text=[f"{v:.1f}" for v in v2],
               hovertemplate='<b>%{x}</b><br>Real: %{text}<br>Norm: %{y:.2f}<extra></extra>'),
    ])
    fig.update_layout(
        barmode='group', showlegend=True,
        legend=dict(font=dict(color=TEXTO_SEC, size=11), bgcolor=BLANCO,
                    bordercolor=BORDE, borderwidth=1),
        title=dict(text=f"Comparativa — <b>{n1}</b> vs <b>{n2}</b>",
                   font=dict(size=14, color=TEXTO, family="Inter,Arial"), x=0),
        xaxis=dict(tickfont=dict(color=TEXTO, size=10), gridcolor="#E0EEF8", tickangle=-18),
        yaxis=dict(title="Normalizado (0-1)", range=[0,1.15],
                   title_font=dict(color=TEXTO_SEC, size=11),
                   gridcolor="#E0EEF8", tickfont=dict(color=TEXTO_SEC)),
        plot_bgcolor=BLANCO, paper_bgcolor=BLANCO,
        height=400, margin=dict(l=8, r=16, t=60, b=60),
        font=dict(family="Inter,Arial", size=11, color=TEXTO),
    )
    return fig

def grafica_tabla_clasificacion(perfil: str, equipo: str = "Todos"):
    filtro = "" if equipo == "Todos" else f"AND activity_team_name='{equipo}'"
    sim_col = f"sim_ncc_{perfil}"
    datos = _safe_query(
        f"SELECT athlete_name, first_name, last_name, activity_team_name, "
        f"nivel_confianza, n_partidos, {sim_col} "
        f"FROM {CATALOG}.{SCHEMA}.clasificacion_posiciones_catapult "
        f"WHERE posicion_final='{perfil}' AND season='{SEASON}' {filtro} "
        f"ORDER BY {sim_col} DESC NULLS LAST LIMIT 20"
    )
    if not datos:
        return go.Figure().update_layout(title="Sin datos", paper_bgcolor=BLANCO, plot_bgcolor=BLANCO)
    nombres   = [f"{d.get('first_name','')} {d.get('last_name','')}".strip() or d.get('athlete_name','') for d in datos]
    equipos   = [d.get('activity_team_name','') for d in datos]
    confianza = [d.get('nivel_confianza','').upper() for d in datos]
    partidos  = [str(d.get('n_partidos','')) for d in datos]
    sims      = [f"{float(d.get(sim_col,0) or 0):.3f}" for d in datos]
    col_conf  = [CELESTE_D if c=="ALTA" else CELESTE for c in confianza]
    fig = go.Figure(go.Table(
        columnwidth=[180,140,80,80,60],
        header=dict(values=["<b>Jugador</b>","<b>Equipo</b>","<b>Similitud</b>","<b>Confianza</b>","<b>Partidos</b>"],
                    fill_color=CELESTE_D, font=dict(color=BLANCO, size=12, family="Inter,Arial"),
                    align='left', height=34),
        cells=dict(
            values=[nombres, equipos, sims, confianza, partidos],
            fill_color=[[BG if i%2==0 else BLANCO for i in range(len(datos))],
                        [BG if i%2==0 else BLANCO for i in range(len(datos))],
                        [BG if i%2==0 else BLANCO for i in range(len(datos))],
                        col_conf,
                        [BG if i%2==0 else BLANCO for i in range(len(datos))]],
            font=dict(color=[TEXTO,TEXTO,TEXTO,BLANCO,TEXTO_SEC], size=12, family="Inter,Arial"),
            align='left', height=30,
        ),
    ))
    fig.update_layout(
        title=dict(text=f"Clasificación — <b>{perfil.capitalize()}</b>",
                   font=dict(size=14, color=TEXTO, family="Inter,Arial"), x=0),
        paper_bgcolor=BLANCO, height=max(380, len(datos)*32+90),
        margin=dict(l=0, r=0, t=50, b=8), font=dict(family="Inter,Arial"),
    )
    return fig

def construir_figura(datos_grafica):
    """
    Construye cualquier tipo de figura Plotly a partir del dict devuelto por backend.
    Tipos soportados:
      clasificacion, relevancia, radar, comparativa, tabla,
      boxplot, linea, heatmap, scatter
    """
    if not datos_grafica:
        return None
    try:
        t     = datos_grafica.get("tipo")
        datos = datos_grafica.get("datos", [])
        if not t:
            return None

        # ── CLASIFICACION — barras horizontales ordenadas ─────────────────────
        if t == "clasificacion" and datos:
            pos     = datos_grafica.get("posicion", "")
            sim_col = f"sim_ncc_{pos}"
            # Ordenar por similitud descendente
            datos_ord = sorted(datos,
                key=lambda d: float(d.get(sim_col, d.get('similitud_ponderada', 0)) or 0),
                reverse=True)
            nombres   = [f"{d.get('first_name','')} {d.get('last_name','')}".strip()
                         or d.get('athlete_name','') for d in datos_ord]
            equipos   = [d.get('activity_team_name','') for d in datos_ord]
            confianza = [d.get('nivel_confianza','') for d in datos_ord]
            sims      = [float(d.get(sim_col, d.get('similitud_ponderada', 0)) or 0)
                         for d in datos_ord]
            colores   = [CELESTE_D if c == 'alta' else CELESTE for c in confianza]
            etiquetas = [f"{n}  ·  {e}" for n, e in zip(nombres, equipos)]
            fig = go.Figure(go.Bar(
                x=sims, y=etiquetas, orientation='h',
                marker=dict(color=colores, line=dict(color=BORDE, width=0.4)),
                text=[f"{s:.3f}" for s in sims], textposition='outside',
                textfont=dict(color=TEXTO_SEC, size=10),
                hovertemplate='<b>%{y}</b><br>Similitud: %{x:.3f}<extra></extra>',
            ))
            fig.update_layout(yaxis=dict(autorange='reversed', tickfont=dict(color=TEXTO, size=11)),
                annotations=[dict(x=1.01, y=1.06, xref='paper', yref='paper',
                    showarrow=False, align='left', font=dict(size=10, color=TEXTO_SEC),
                    text=f'<span style="color:{CELESTE_D}">■</span> Alta  '
                         f'<span style="color:{CELESTE}">■</span> Normal')])
            return _fig_layout(fig, f"Candidatos — <b>{pos.capitalize()}</b>",
                               xlab="Similitud al perfil", height=max(320, len(datos_ord)*44+70))

        # ── RELEVANCIA — barras horizontales de variables GPS ─────────────────
        elif t == "relevancia" and datos:
            perfil  = datos_grafica.get("perfil", "")
            nombres = [d.get('variable','').replace('match_','').replace('_',' ').title()
                       for d in datos]
            scores  = [float(d.get('score_relevancia', 0) or 0) for d in datos]
            clasifs = [d.get('clasificacion','') for d in datos]
            cmap    = {'muy_definitorio': CELESTE_D, 'definitorio': CELESTE_D,
                       'moderado': CELESTE, 'no_definitorio': CELESTE_L}
            colores = [cmap.get(c, CELESTE) for c in clasifs]
            fig = go.Figure(go.Bar(
                x=scores, y=nombres, orientation='h',
                marker=dict(color=colores, line=dict(color=BORDE, width=0.4)),
                text=[f"{s:.3f}" for s in scores], textposition='outside',
                textfont=dict(color=TEXTO_SEC, size=10),
                hovertemplate='<b>%{y}</b><br>Score: %{x:.3f}<extra></extra>',
            ))
            fig.update_layout(yaxis=dict(autorange='reversed', tickfont=dict(color=TEXTO, size=11)))
            return _fig_layout(fig, f"Variables GPS — <b>{perfil.capitalize()}</b>",
                               xlab="Score de relevancia", height=max(320, len(datos)*38+70))

        # ── RADAR — perfil GPS de un jugador ──────────────────────────────────
        elif t == "radar":
            nombre = datos_grafica.get("jugador", "")
            return grafica_radar_jugador(nombre)

        # ── COMPARATIVA — barras agrupadas dos jugadores ──────────────────────
        elif t == "comparativa":
            j1     = datos_grafica.get("jugador1", "")
            j2     = datos_grafica.get("jugador2", "")
            perfil = datos_grafica.get("perfil", "")
            return grafica_comparativa(j1, j2, perfil)

        # ── TABLA — tabla completa de clasificación ───────────────────────────
        elif t == "tabla":
            perfil = datos_grafica.get("perfil", "")
            equipo = datos_grafica.get("equipo", "Todos")
            return grafica_tabla_clasificacion(perfil, equipo)

        # ── BOXPLOT — distribución de una métrica GPS por equipo ─────────────
        elif t == "boxplot" and datos:
            metrica = datos_grafica.get("metrica", "")
            label   = metrica.replace('match_','').replace('_',' ').title()
            # datos: lista de {athlete_name, activity_team_name, valor}
            equipos_uniq = list(dict.fromkeys(d.get('equipo','') for d in datos))
            fig = go.Figure()
            for eq in equipos_uniq:
                vals = [float(d.get('valor', 0) or 0) for d in datos if d.get('equipo') == eq]
                fig.add_trace(go.Box(y=vals, name=eq, marker_color=CELESTE_D,
                                     line_color=CELESTE_D, fillcolor=CELESTE_L,
                                     boxpoints='outliers',
                                     hovertemplate=f'<b>{eq}</b><br>%{{y:.2f}}<extra></extra>'))
            return _fig_layout(fig, f"Distribución — <b>{label}</b>",
                               ylab=label, height=400)

        # ── LINEA — evolución temporal de métricas de un jugador ─────────────
        elif t == "linea" and datos:
            jugador = datos_grafica.get("jugador", "")
            metrica = datos_grafica.get("metrica", "")
            label   = metrica.replace('match_','').replace('_',' ').title()
            fechas  = [d.get('fecha', d.get('partido', i)) for i, d in enumerate(datos)]
            vals    = [float(d.get('valor', 0) or 0) for d in datos]
            fig = go.Figure(go.Scatter(
                x=fechas, y=vals, mode='lines+markers',
                line=dict(color=CELESTE_D, width=2),
                marker=dict(color=CELESTE_D, size=6),
                fill='tozeroy', fillcolor=f'rgba(109,200,243,0.12)',
                hovertemplate='<b>%{x}</b><br>' + label + ': %{y:.2f}<extra></extra>',
            ))
            return _fig_layout(fig, f"Evolución — <b>{jugador}</b> · {label}",
                               xlab="Partido", ylab=label, height=380)

        # ── HEATMAP — correlación entre variables GPS ─────────────────────────
        elif t == "heatmap" and datos:
            perfil = datos_grafica.get("perfil", "")
            # datos: lista de {var_x, var_y, correlacion}
            vars_  = list(dict.fromkeys(
                [d.get('var_x','') for d in datos] + [d.get('var_y','') for d in datos]))
            n      = len(vars_)
            matrix = [[0.0]*n for _ in range(n)]
            idx    = {v: i for i, v in enumerate(vars_)}
            for d in datos:
                vx, vy, corr = d.get('var_x',''), d.get('var_y',''), float(d.get('correlacion',0) or 0)
                if vx in idx and vy in idx:
                    matrix[idx[vx]][idx[vy]] = corr
                    matrix[idx[vy]][idx[vx]] = corr
            labels = [v.replace('match_','').replace('_',' ').title() for v in vars_]
            fig = go.Figure(go.Heatmap(
                z=matrix, x=labels, y=labels,
                colorscale=[[0, CELESTE_L],[0.5,'#FFFFFF'],[1, CELESTE_D]],
                zmid=0,
                text=[[f"{matrix[i][j]:.2f}" for j in range(n)] for i in range(n)],
                texttemplate="%{text}",
                hovertemplate='<b>%{x}</b> vs <b>%{y}</b><br>Corr: %{z:.2f}<extra></extra>',
            ))
            fig.update_layout(
                title=dict(text=f"Correlación variables — <b>{perfil.capitalize()}</b>",
                           font=dict(size=14, color=TEXTO, family="Inter,Arial"), x=0),
                xaxis=dict(tickfont=dict(color=TEXTO, size=10), tickangle=-30),
                yaxis=dict(tickfont=dict(color=TEXTO, size=10)),
                height=max(380, n*50+100),
                paper_bgcolor=BLANCO, plot_bgcolor=BLANCO,
                margin=dict(l=10, r=10, t=50, b=80),
                font=dict(family="Inter,Arial", size=11, color=TEXTO),
            )
            return fig

        # ── SCATTER — rank vs similitud de un perfil ────────────────────────
        elif t == "scatter":
            perfil  = datos_grafica.get("perfil", datos_grafica.get("posicion", ""))
            if not perfil:
                return go.Figure().update_layout(title="Especifica un perfil para el scatter",
                                                 paper_bgcolor=BLANCO, plot_bgcolor=BLANCO)
            sim_col = f"sim_ncc_{perfil}"
            # Consultar directamente clasificacion con ranking calculado en Python
            datos_raw = _safe_query(
                f"SELECT athlete_name, first_name, last_name, activity_team_name, "
                f"nivel_confianza, {sim_col} "
                f"FROM {CATALOG}.{SCHEMA}.clasificacion_posiciones_catapult "
                f"WHERE season='{SEASON}' AND {sim_col} IS NOT NULL "
                f"ORDER BY {sim_col} DESC LIMIT 30"
            )
            if not datos_raw:
                return go.Figure().update_layout(title=f"Sin datos para scatter de '{perfil}'",
                                                 paper_bgcolor=BLANCO, plot_bgcolor=BLANCO)
            # Calcular ranking en Python (evita ROW_NUMBER en SQL)
            nombres   = [f"{d.get('first_name','')} {d.get('last_name','')}".strip()
                         or d.get('athlete_name','') for d in datos_raw]
            equipos   = [d.get('activity_team_name','') for d in datos_raw]
            confianza = [d.get('nivel_confianza','') for d in datos_raw]
            sims      = [float(d.get(sim_col, 0) or 0) for d in datos_raw]
            ranks     = list(range(1, len(sims)+1))
            colores   = [CELESTE_D if c == 'alta' else CELESTE for c in confianza]
            fig = go.Figure(go.Scatter(
                x=ranks, y=sims, mode='markers+text',
                text=nombres, textposition='top center',
                textfont=dict(size=9, color=TEXTO_SEC),
                marker=dict(color=colores, size=10,
                            line=dict(color=BLANCO, width=1.5)),
                customdata=list(zip(equipos, confianza)),
                hovertemplate='<b>%{text}</b><br>%{customdata[0]}<br>'
                              'Ranking: %{x}<br>Similitud: %{y:.3f}<extra></extra>',
            ))
            fig.update_layout(
                annotations=[dict(x=1.01, y=1.06, xref='paper', yref='paper',
                    showarrow=False, align='left', font=dict(size=10, color=TEXTO_SEC),
                    text=f'<span style="color:{CELESTE_D}">■</span> Alta  '
                         f'<span style="color:{CELESTE}">■</span> Normal')],
                yaxis=dict(title="Similitud", title_font=dict(color=TEXTO_SEC, size=11),
                           gridcolor="#E0EEF8", tickfont=dict(color=TEXTO_SEC, size=11)),
            )
            return _fig_layout(fig,
                f"Ranking vs Similitud — <b>{perfil.capitalize()}</b>",
                xlab="Ranking", height=460)

    except Exception as e:
        print(f"construir_figura error ({t}): {e}")
    return None

# ── HTML helpers ──────────────────────────────────────────────────────────────
def _mini_bars_html(datos_grafica: dict) -> str:
    """Mini gráfica de barras HTML dentro de la burbuja del chat."""
    if not datos_grafica:
        return ""
    t     = datos_grafica.get("tipo")
    datos = datos_grafica.get("datos", [])
    if not datos:
        return ""
    if t == "clasificacion":
        pos     = datos_grafica.get("posicion", "")
        sim_col = f"sim_ncc_{pos}"
        items   = []
        max_sim = max((float(d.get(sim_col, d.get('similitud_ponderada', 0)) or 0) for d in datos[:5]), default=1)
        for d in datos[:5]:
            nombre = f"{d.get('first_name','')} {d.get('last_name','')}".strip() or d.get('athlete_name','')
            sim    = float(d.get(sim_col, d.get('similitud_ponderada', 0)) or 0)
            pct    = round(sim / max_sim * 100) if max_sim else 0
            conf   = d.get('nivel_confianza','')
            color  = "#1A9FD4" if conf == 'alta' else "#6DC8F3"
            items.append(f"""
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
              <span style="font-size:11px;color:#374151;width:110px;flex-shrink:0;
                           white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{nombre}</span>
              <div style="flex:1;height:5px;background:#BFDBEE;border-radius:3px;">
                <div style="width:{pct}%;height:100%;background:{color};border-radius:3px;"></div>
              </div>
              <span style="font-size:10px;color:#6B7280;width:32px;text-align:right;">{sim:.3f}</span>
            </div>""")
        title = f"Similitud al perfil · {pos.capitalize()}"
    elif t == "relevancia":
        perfil  = datos_grafica.get("perfil", "")
        items   = []
        max_s   = max((float(d.get('score_relevancia', 0) or 0) for d in datos[:5]), default=1)
        for d in datos[:5]:
            var   = d.get('variable','').replace('match_','').replace('_',' ').title()
            score = float(d.get('score_relevancia', 0) or 0)
            pct   = round(score / max_s * 100) if max_s else 0
            items.append(f"""
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
              <span style="font-size:11px;color:#374151;width:110px;flex-shrink:0;
                           white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{var}</span>
              <div style="flex:1;height:5px;background:#BFDBEE;border-radius:3px;">
                <div style="width:{pct}%;height:100%;background:#1A9FD4;border-radius:3px;"></div>
              </div>
              <span style="font-size:10px;color:#6B7280;width:32px;text-align:right;">{score:.3f}</span>
            </div>""")
        title = f"Variables clave · {perfil.capitalize()}"
    else:
        return ""
    return f"""
    <div style="margin-top:10px;background:#F0F8FF;border:1px solid #BFDBEE;
                border-radius:9px;padding:11px;">
      <div style="font-size:10px;color:#93C5E8;text-transform:uppercase;
                  letter-spacing:0.5px;margin-bottom:8px;">{title}</div>
      {''.join(items)}
    </div>"""

# ── Chat logic ────────────────────────────────────────────────────────────────
def _extraer_texto(contenido) -> str:
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list):
        return next((b["text"] if isinstance(b, dict) and b.get("type") == "text"
                     else str(b) for b in contenido), "")
    return str(contenido)

def enviar_mensaje(mensaje, historial, datos_prev):
    if not mensaje.strip():
        return historial, "", datos_prev, gr.update(visible=False)
    historial = list(historial) + [{"role": "user", "content": mensaje}]
    return historial, "", datos_prev, gr.update(visible=True)

def procesar_respuesta(historial, datos_prev):
    if not historial or historial[-1].get("role") != "user":
        return historial, datos_prev, gr.update(visible=False), gr.update(visible=False)
    mensaje = _extraer_texto(historial[-1]["content"])
    if not mensaje.strip():
        return historial, datos_prev, gr.update(visible=False), gr.update(visible=False)

    resultado = {"respuesta": None, "datos": None, "error": None}
    def _run():
        try:
            r, d = chat(mensaje, historial[:-1])
            resultado["respuesta"] = r; resultado["datos"] = d
        except Exception as e:
            resultado["error"] = str(e)
    t = threading.Thread(target=_run, daemon=True)
    t.start(); t.join(timeout=120)

    if t.is_alive():
        respuesta = "⚠️ La consulta tardó demasiado. Inténtalo de nuevo."
        datos_nuevos = None
    elif resultado["error"]:
        respuesta = f"⚠️ Error: {resultado['error']}"
        datos_nuevos = None
    else:
        respuesta    = resultado["respuesta"] or "Sin respuesta."
        datos_nuevos = resultado["datos"]

    # Añadir texto al historial
    historial = list(historial) + [{"role": "assistant", "content": respuesta}]



    # Actualizar panel lateral Plotly
    fig = construir_figura(datos_nuevos) if datos_nuevos else None
    plot_upd = gr.update(value=fig, visible=fig is not None) if fig else gr.update(visible=False)

    return historial, (datos_nuevos or datos_prev), gr.update(visible=False), plot_upd

# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*, *::before, *::after { box-sizing: border-box; }

/* ── Base ── */
body, .gradio-container, .gradio-container > .main, .gradio-container .contain {
    background: #F0F8FF !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    color: #0a1628 !important;
}
.gradio-container { max-width: 100% !important; width: 100% !important; padding: 0 !important; }
footer { display: none !important; }

/* ── Grid principal chat + viz ── */
.app-grid {
    display: grid;
    grid-template-columns: 3fr 2fr;
    gap: 16px;
    padding: 16px;
    align-items: start;
    width: 100%;
    min-height: 0;
}
.app-chat { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.app-viz  { display: flex; flex-direction: column; min-width: 0; }
@media (max-width: 900px) {
    .app-grid { grid-template-columns: 1fr; }
}

/* ── Quitar barras verticales (caret) en burbujas ── */
.chatbot .message,
.chatbot .message *,
.chatbot [data-testid="bot"],
.chatbot [data-testid="bot"] *,
.chatbot [data-testid="user"],
.chatbot [data-testid="user"] * {
    caret-color: transparent !important;
    outline: none !important;
}
.chatbot .message > div[contenteditable],
.chatbot [data-testid] > div[contenteditable] {
    caret-color: transparent !important;
    -webkit-user-modify: read-only !important;
}

/* ── Chatbot contenedor ── */
.chatbot, .chatbot > div {
    background: rgba(255,255,255,0.92) !important;
    backdrop-filter: blur(6px) !important;
    border: 1px solid #BFDBEE !important;
    border-radius: 10px !important;
}
/* Quitar cursor/caret en burbujas */
.chatbot .message, .chatbot .message > div,
.chatbot [data-testid="bot"], .chatbot [data-testid="user"] {
    caret-color: transparent !important;
    cursor: default !important;
}

/* ── Burbuja bot — blanco con borde celeste ── */
.chatbot .message.bot > div,
.chatbot [data-testid="bot"] > div {
    background: #FFFFFF !important;
    color: #0a1628 !important;
    border: 1px solid #BFDBEE !important;
    border-radius: 3px 12px 12px 12px !important;
    padding: 10px 14px !important;
    font-size: 13px !important;
    line-height: 1.65 !important;
    max-width: 88% !important;
    box-shadow: 0 1px 4px rgba(26,159,212,0.06) !important;
}
/* Texto bot — forzar negro sobre blanco */
.chatbot .message.bot > div,
.chatbot .message.bot > div p,
.chatbot .message.bot > div span,
.chatbot .message.bot > div li,
.chatbot .message.bot > div strong,
.chatbot .message.bot > div em,
.chatbot .message.bot > div code {
    color: #0a1628 !important;
}

/* ── Burbuja usuario — celeste ── */
.chatbot .message.user > div,
.chatbot [data-testid="user"] > div {
    background: #6DC8F3 !important;
    color: #0a1628 !important;
    border: none !important;
    border-radius: 12px 3px 12px 12px !important;
    padding: 10px 14px !important;
    font-size: 13px !important;
    line-height: 1.65 !important;
    max-width: 88% !important;
    font-weight: 500 !important;
}
.chatbot .message.user > div,
.chatbot .message.user > div p,
.chatbot .message.user > div span,
.chatbot .message.user > div strong {
    color: #0a1628 !important;
}

/* ── Input ── */
textarea, textarea:focus {
    background: #FFFFFF !important; color: #0a1628 !important;
    border: 1px solid #BFDBEE !important; border-radius: 10px !important;
    outline: none !important; box-shadow: none !important;
    font-family: 'Inter', sans-serif !important; font-size: 13px !important;
    padding: 9px 13px !important;
}
textarea:focus { border-color: #1A9FD4 !important; box-shadow: 0 0 0 3px rgba(26,159,212,0.12) !important; }
textarea::placeholder { color: #9CA3AF !important; }

/* ── Botones ── */
button.primary, button[variant="primary"] {
    background: #1A9FD4 !important; color: #FFFFFF !important;
    border: none !important; border-radius: 9px !important;
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    font-size: 13px !important; padding: 9px 20px !important;
    cursor: pointer !important; transition: background 0.15s, transform 0.1s !important;
}
button.primary:hover { background: #1587B3 !important; transform: translateY(-1px) !important; }
button.secondary, button[variant="secondary"] {
    background: #FFFFFF !important; color: #1A9FD4 !important;
    border: 1.5px solid #1A9FD4 !important; border-radius: 9px !important;
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    font-size: 12px !important; padding: 7px 16px !important; cursor: pointer !important;
    transition: all 0.15s !important;
}
button.secondary:hover { background: #1A9FD4 !important; color: #FFFFFF !important; }

/* ── Ejemplos ── */
.gr-examples, div[class*="examples"] {
    background: rgba(255,255,255,0.92) !important;
    backdrop-filter: blur(6px) !important;
    border: 1px solid #BFDBEE !important;
    border-radius: 10px !important; padding: 12px !important; margin-top: 8px !important;
    box-shadow: 0 2px 12px rgba(26,159,212,0.08) !important;
}
.gr-examples label, div[class*="examples"] > label {
    color: #0a1628 !important; font-size: 11px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.4px !important;
    margin-bottom: 8px !important; display: block !important;
}
/* Ocultar cabecera de tabla vacía */
.gr-examples table thead, div[class*="examples"] table thead { display: none !important; }
/* Celdas de ejemplos */
.gr-examples table td, div[class*="examples"] table td {
    padding: 3px 4px !important;
}
.gr-examples button, div[class*="examples"] button,
.gr-examples table td button, div[class*="examples"] table td button {
    background: #FFFFFF !important; color: #1A9FD4 !important;
    border: 1.5px solid #BFDBEE !important; border-radius: 16px !important;
    font-size: 12px !important; padding: 5px 12px !important;
    cursor: pointer !important; transition: all 0.15s !important;
    font-weight: 500 !important; text-align: left !important;
    white-space: normal !important; width: 100% !important;
    display: block !important; overflow: visible !important;
}
.gr-examples button:hover, div[class*="examples"] button:hover {
    background: #D6EFFA !important; border-color: #1A9FD4 !important;
}

/* ── Tabs ── */
.tab-nav, .tabs > div:first-child {
    background: #1A9FD4 !important; border-radius: 10px 10px 0 0 !important; padding: 0 8px !important;
}
.tab-nav button, .tabs button[role="tab"] {
    background: transparent !important; color: rgba(255,255,255,0.65) !important;
    border: none !important; border-bottom: 3px solid transparent !important;
    font-family: 'Inter', sans-serif !important; font-size: 13px !important;
    font-weight: 600 !important; padding: 12px 18px !important; opacity: 1 !important;
}
.tab-nav button:hover { color: #FFFFFF !important; background: rgba(255,255,255,0.08) !important; }
.tab-nav button.selected, .tab-nav button[aria-selected="true"] {
    color: #FFFFFF !important; border-bottom: 3px solid #FFFFFF !important;
    font-weight: 700 !important;
}
.tabitem { background: #FFFFFF !important; border: 1px solid #BFDBEE !important;
           border-top: none !important; border-radius: 0 0 10px 10px !important; padding: 16px !important; }

/* Typing indicator */
.typing-indicator {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 13px; background: #FFFFFF; border: 1px solid #BFDBEE;
    border-radius: 3px 12px 12px 12px; width: fit-content; margin: 4px 0 6px 2px;
}
.typing-dots { display: flex; gap: 4px; align-items: center; }
.typing-dots span {
    width: 6px; height: 6px; background: #1A9FD4; border-radius: 50%;
    animation: tdot 1.2s infinite ease-in-out;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes tdot { 0%,80%,100% { transform:scale(0.6); opacity:0.4; } 40% { transform:scale(1); opacity:1; } }
.typing-text { font-size: 12px; color: #374151; font-weight: 500; }
"""

BIENVENIDA = (
    "Hola, soy el asistente de análisis de cantera.\n\n"
    "Puedo ayudarte a:\n"
    "- 🔍 Identificar jugadores que encajan en un perfil de posición\n"
    "- 📊 Analizar variables GPS que definen cada perfil\n"
    "- 🆚 Comparar métricas entre jugadores\n"
    "- 📈 Generar gráficas de barras, radar, scatter y más\n\n"
    "¿En qué trabajamos hoy?"
)

# ── Layout ────────────────────────────────────────────────────────────────────
with gr.Blocks(title="RC Celta de Vigo — Análisis de Cantera") as demo:

    datos_state   = gr.State(None)
    panel_visible = gr.State(False)

    # ══════════════════════════════════════════════════════════
    # SPLASH
    # ══════════════════════════════════════════════════════════
    with gr.Column(visible=True) as splash_col:
        gr.HTML(f'''
        <div style="position:relative;min-height:88vh;border-radius:14px;overflow:hidden;">
          <div style="position:absolute;inset:0;
               background:url('{SPLASH_BG}') center/cover no-repeat;"></div>
          <div style="position:absolute;inset:0;background:rgba(240,248,255,0.72);"></div>
          <div style="position:relative;z-index:2;height:100%;display:flex;
                      flex-direction:column;justify-content:flex-end;padding:36px 40px;">
            <div style="margin-bottom:16px;">{LOGO_LG}</div>
            <h1 style="font-size:38px;font-weight:800;color:#0a1628;line-height:1.1;
                        letter-spacing:-0.5px;margin:0 0 10px;">
              Análisis de<br><span style="color:#1A9FD4;">Cantera Inteligente</span>
            </h1>
            <p style="font-size:14px;color:#374151;max-width:420px;line-height:1.7;margin:0 0 28px;">
              Identifica talento, compara perfiles GPS y toma decisiones con datos reales de Catapult.
            </p>
          </div>
        </div>
        ''')
        btn_entrar = gr.Button("Entrar al sistema →", variant="primary")

    # ══════════════════════════════════════════════════════════
    # APP
    # ══════════════════════════════════════════════════════════
    with gr.Column(visible=False) as app_col:

        # Fondo de la app con la misma imagen que el splash
        gr.HTML(f'''
        <div style="position:fixed;inset:0;z-index:0;
             background:url('{SPLASH_BG}') center/cover no-repeat;
             pointer-events:none;"></div>
        <div style="position:fixed;inset:0;z-index:0;
             background:rgba(240,248,255,0.82);pointer-events:none;"></div>
        ''')

        # Topbar
        gr.HTML(f"""
        <div style="position:relative;z-index:1;background:#FFFFFF;
             border-bottom:1px solid #BFDBEE;height:52px;display:flex;
             align-items:center;padding:0 20px;gap:12px;
             border-radius:12px 12px 0 0;box-shadow:0 1px 6px rgba(26,159,212,0.08);">
          {LOGO_SM}
          <div>
            <div style="font-size:14px;font-weight:600;color:#0a1628;">Asistente de Cantera</div>
            <div style="font-size:11px;color:#93C5E8;">Catapult GPS · Claude Haiku</div>
          </div>
          <div style="flex:1;"></div>
          <button onclick="if(confirm('¿Cerrar la aplicación?')){{fetch('/close');setTimeout(()=>window.close(),400)}}"
                  style="background:#FFFFFF;color:#374151;border:1.5px solid #BFDBEE;
                         border-radius:8px;padding:5px 14px;font-size:12px;font-weight:600;
                         cursor:pointer;font-family:Inter,sans-serif;transition:all 0.15s;"
                  onmouseover="this.style.background='#FEE2E2';this.style.borderColor='#FCA5A5';this.style.color='#DC2626'"
                  onmouseout="this.style.background='#FFFFFF';this.style.borderColor='#BFDBEE';this.style.color='#374151'">
            ✕ Salir
          </button>
        </div>
        """)

        # Contenido principal: chat + panel viz en grid CSS
        gr.HTML("""<div class="app-grid" style="position:relative;z-index:1;">
          <div class="app-chat" id="app-chat-col">""")

        chatbot = gr.Chatbot(
            label="", height=460, show_label=False,
            value=[{"role": "assistant", "content": BIENVENIDA}],
        )
        with gr.Row(visible=False) as loading_row:
            gr.HTML("""
            <div class="typing-indicator">
              <div class="typing-dots"><span></span><span></span><span></span></div>
              <span class="typing-text">Procesando consulta…</span>
            </div>""")
        with gr.Row(equal_height=True):
            txt_input = gr.Textbox(
                placeholder="Escribe tu consulta…",
                show_label=False, scale=9, container=False, autofocus=True,
            )
            btn_send = gr.Button("Enviar ➤", variant="primary", scale=1, min_width=90)

        gr.HTML("""</div><div class="app-viz" id="app-viz-col">
          <div style="background:#FFFFFF;border:1px solid #BFDBEE;border-radius:10px 10px 0 0;
               height:44px;display:flex;align-items:center;padding:0 14px;">
            <span style="font-size:13px;font-weight:600;color:#0a1628;">Visualización</span>
          </div>""")

        plot_panel = gr.Plot(show_label=False, visible=False)

        gr.HTML("""</div></div>
        <script>
        function fixCarets() {
            document.querySelectorAll('.chatbot *').forEach(el => {
                el.style.caretColor = 'transparent';
                if (el.getAttribute('contenteditable') === 'true') {
                    el.setAttribute('contenteditable', 'plaintext-only');
                }
            });
        }
        const chatObs = new MutationObserver(fixCarets);
        setTimeout(() => {
            const chatbot = document.querySelector('.chatbot');
            if (chatbot) {
                chatObs.observe(chatbot, { childList: true, subtree: true, attributes: true });
            }
            fixCarets();
        }, 500);
        </script>""")




    # ── Funciones splash ──────────────────────────────────────
    def mostrar_app():
        return gr.update(visible=False), gr.update(visible=True)

    def cargar_stats():
        s = obtener_stats()
        p = obtener_perfiles()
        choices = p if p else []
        return str(s["perfiles"]), str(s["jugadores"]), str(s["alta"])



    btn_entrar.click(fn=mostrar_app, outputs=[splash_col, app_col])



    # ── Eventos chat ──────────────────────────────────────────
    (btn_send.click(
        fn=enviar_mensaje,
        inputs=[txt_input, chatbot, datos_state],
        outputs=[chatbot, txt_input, datos_state, loading_row],
        queue=False,
    ).then(
        fn=procesar_respuesta,
        inputs=[chatbot, datos_state],
        outputs=[chatbot, datos_state, loading_row, plot_panel],
        concurrency_limit=1,
    ))
    (txt_input.submit(
        fn=enviar_mensaje,
        inputs=[txt_input, chatbot, datos_state],
        outputs=[chatbot, txt_input, datos_state, loading_row],
        queue=False,
    ).then(
        fn=procesar_respuesta,
        inputs=[chatbot, datos_state],
        outputs=[chatbot, datos_state, loading_row, plot_panel],
        concurrency_limit=1,
    ))

if __name__ == "__main__":
    print("RC Celta de Vigo — Sistema de Análisis de Cantera")
    print("Accede en: http://localhost:7860")

    try:
        demo.queue(max_size=5, default_concurrency_limit=3).launch(
            server_name="0.0.0.0", server_port=7860,
            show_error=True, css=CSS,
            prevent_thread_lock=True,
        )

        @demo.app.get("/close")
        def close_app():
            import threading
            threading.Timer(0.3, lambda: os._exit(0)).start()
            return {"status": "closing"}

        demo.block_thread()

    except KeyboardInterrupt:
        print("\nDetenido.")
    except KeyboardInterrupt:
        print("\nDetenido.")
