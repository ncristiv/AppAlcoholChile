"""
Calculadora de Alcohol en Sangre - Chile
- Hora automática Santiago de Chile (America/Santiago)
- Registro de consumo pasado y futuro
- Hora objetivo para manejar
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Santiago")

st.set_page_config(
    page_title="Calculadora BAC Chile 🇨🇱",
    page_icon="🍻",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@300;400;600;700;900&family=Lato:wght@300;400;700&display=swap');

html, body, [class*="css"] { font-family: 'Lato', sans-serif; }
h1, h2, h3 { font-family: 'Raleway', sans-serif !important; }

.main-title {
    font-family: 'Raleway', sans-serif;
    font-size: 2.6rem; font-weight: 900;
    color: #C0392B; letter-spacing: -1px; line-height: 1.1;
}
.subtitle { color: #7f8c8d; font-size: 1rem; margin-top: -0.4rem; }

.status-safe {
    background: linear-gradient(135deg, #0f3460, #16213e);
    border-left: 4px solid #27ae60; padding: 1rem 1.5rem;
    border-radius: 8px; color: #2ecc71;
    font-family: 'Raleway', sans-serif; font-weight: 700; font-size: 1.05rem;
}
.status-warning {
    background: linear-gradient(135deg, #3d1c00, #1a0a00);
    border-left: 4px solid #f39c12; padding: 1rem 1.5rem;
    border-radius: 8px; color: #f39c12;
    font-family: 'Raleway', sans-serif; font-weight: 700; font-size: 1.05rem;
}
.status-danger {
    background: linear-gradient(135deg, #2c0000, #1a0000);
    border-left: 4px solid #e74c3c; padding: 1rem 1.5rem;
    border-radius: 8px; color: #e74c3c;
    font-family: 'Raleway', sans-serif; font-weight: 700; font-size: 1.05rem;
}
.status-future {
    background: linear-gradient(135deg, #0a1f3d, #0d1b2a);
    border-left: 4px solid #3498db; padding: 1rem 1.5rem;
    border-radius: 8px; color: #5dade2;
    font-family: 'Raleway', sans-serif; font-weight: 700; font-size: 1.05rem;
}
.section-header {
    font-family: 'Raleway', sans-serif; font-size: 1.05rem;
    font-weight: 700; color: #C0392B; text-transform: uppercase;
    letter-spacing: 2px; margin: 1.5rem 0 0.8rem 0;
    border-bottom: 2px solid rgba(192,57,43,0.3); padding-bottom: 0.4rem;
}
.section-header-blue {
    font-family: 'Raleway', sans-serif; font-size: 1.05rem;
    font-weight: 700; color: #3498db; text-transform: uppercase;
    letter-spacing: 2px; margin: 1.5rem 0 0.8rem 0;
    border-bottom: 2px solid rgba(52,152,219,0.3); padding-bottom: 0.4rem;
}
.disclaimer {
    background: rgba(231,76,60,0.1);
    border: 1px solid rgba(231,76,60,0.3);
    border-radius: 8px; padding: 1rem;
    font-size: 0.82rem; color: #e74c3c; margin-top: 1rem;
}
div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a0a00 0%, #0d0d0d 100%);
    border-right: 1px solid rgba(192,57,43,0.2);
}
.tag-pasado {
    background: rgba(192,57,43,0.15); color: #e74c3c;
    border-radius: 4px; padding: 1px 7px; font-size: 0.75rem;
    font-weight: 700; letter-spacing: 1px;
}
.tag-futuro {
    background: rgba(52,152,219,0.15); color: #3498db;
    border-radius: 4px; padding: 1px 7px; font-size: 0.75rem;
    font-weight: 700; letter-spacing: 1px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATOS
# ─────────────────────────────────────────────
TRAGOS = {
    "🍺 Cerveza latita (355ml, 5°)":        {"ml": 355,  "grad": 5.0},
    "🍺 Cerveza botella (330ml, 5°)":       {"ml": 330,  "grad": 5.0},
    "🍺 Schop (500ml, 5°)":                 {"ml": 500,  "grad": 5.0},
    "🍹 Pisco Sour (120ml, 14°)":           {"ml": 120,  "grad": 14.0},
    "🥃 Pisco con Coca-Cola (250ml, 10°)":  {"ml": 250,  "grad": 10.0},
    "🍹 Chilcano (250ml, 10°)":             {"ml": 250,  "grad": 10.0},
    "🥃 Whisky en las rocas (90ml, 40°)":   {"ml": 90,   "grad": 40.0},
    "🥃 Whisky con soda (250ml, 14°)":      {"ml": 250,  "grad": 14.0},
    "🍸 Mojito Cubano (300ml, 8.5°)":       {"ml": 300,  "grad": 8.5},
    "🥂 Tequila shot (45ml, 38°)":          {"ml": 45,   "grad": 38.0},
    "🍹 Margarita (150ml, 16°)":            {"ml": 150,  "grad": 16.0},
    "🍷 Vino tinto (150ml, 13°)":           {"ml": 150,  "grad": 13.0},
    "🥂 Espumante / Champaña (150ml, 11°)": {"ml": 150,  "grad": 11.5},
    "🍸 Aperol Spritz (200ml, 8°)":         {"ml": 200,  "grad": 8.0},
}
TRAGOS_LISTA = list(TRAGOS.keys())

COMIDA = {
    "🚫 Nada (estómago vacío)":             1.0,
    "🥗 Snacks livianos (maní, crudités)":  0.85,
    "🥘 Entradas / finger food (cóctel)":   0.70,
    "🍖 Cena completa (entrada + fondo)":   0.55,
    "🍽️ Cena abundante + pan + postre":     0.45,
}

LIMITE_CONDUCIR = 0.30
LIMITE_EBRIEDAD = 0.50

# ─────────────────────────────────────────────
# Funciones
# ─────────────────────────────────────────────

def gramos_etanol(ml, grad):
    return ml * (grad / 100.0) * 0.789

def factor_widmark(peso_kg, altura_cm, edad, sexo):
    if sexo == "Masculino":
        tbw = 2.447 - (0.09516 * edad) + (0.1074 * altura_cm) + (0.3362 * peso_kg)
        r = tbw / peso_kg
        r = max(0.55, min(r, 0.85))
    else:
        tbw = -2.097 + (0.1069 * altura_cm) + (0.2466 * peso_kg)
        r = tbw / peso_kg
        r = max(0.45, min(r, 0.75))
    return r

def bac_de_evento(gramos, factor_comida, peso_kg, r, horas_desde_consumo):
    """Solo aplica para tragos ya consumidos (horas >= 0)."""
    beta = 0.15
    t_absorcion = 0.5 + 0.5 * (1.0 - factor_comida)
    gramos_absorbidos = gramos * factor_comida
    bac_pico = gramos_absorbidos / (r * peso_kg)
    t_elim = max(0.0, horas_desde_consumo - t_absorcion)
    return max(0.0, bac_pico - beta * t_elim)

def bac_en_momento(eventos, factor_comida, peso_kg, r, dt_consulta):
    """
    Calcula BAC en dt_consulta considerando:
    - Eventos pasados: ya absorbidos y en eliminación
    - Eventos futuros (dt > dt_consulta): aún no consumidos → 0 contribución
    """
    total = 0.0
    for ev in eventos:
        if ev["dt"] <= dt_consulta:
            horas = (dt_consulta - ev["dt"]).total_seconds() / 3600.0
            total += bac_de_evento(ev["gramos"], factor_comida, peso_kg, r, horas)
        # Si ev["dt"] > dt_consulta → no contribuye aún
    return round(total, 3)

def tiempo_para_limite(bac, limite):
    if bac <= limite:
        return 0.0
    return (bac - limite) / 0.15

def curva_bac(eventos, factor_comida, peso_kg, r, dt_actual, ventana_h=18):
    if not eventos:
        return pd.DataFrame()
    dt_inicio = min(ev["dt"] for ev in eventos)
    dt_fin = max(ev["dt"] for ev in eventos) + timedelta(hours=ventana_h)
    puntos = []
    dt = dt_inicio
    while dt <= dt_fin:
        b = bac_en_momento(eventos, factor_comida, peso_kg, r, dt)
        puntos.append({"tiempo": dt, "bac": b})
        dt += timedelta(minutes=10)
    return pd.DataFrame(puntos)

# ─────────────────────────────────────────────
# Estado de sesión
# ─────────────────────────────────────────────
if "filas" not in st.session_state:
    st.session_state.filas = [{"id": 0}]
if "next_id" not in st.session_state:
    st.session_state.next_id = 1

def agregar_fila():
    st.session_state.filas.append({"id": st.session_state.next_id})
    st.session_state.next_id += 1

def eliminar_fila(fid):
    st.session_state.filas = [f for f in st.session_state.filas if f["id"] != fid]

# ─────────────────────────────────────────────
# Hora actual Santiago
# ─────────────────────────────────────────────
ahora = datetime.now(TZ).replace(tzinfo=None)  # naive para operar con timedelta
hoy   = ahora.date()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="main-title">🍻 Calculadora BAC Chile</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Estimación de alcohol en sangre · Ley de Tránsito Art. 196, Ley 18.290 · 🇨🇱 Hora de Santiago</div>',
            unsafe_allow_html=True)
st.markdown("---")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 👤 Datos Personales")
    sexo   = st.radio("Sexo biológico", ["Masculino", "Femenino"])
    peso   = st.number_input("Peso (kg)",    40.0, 200.0, 75.0, 0.5)
    altura = st.number_input("Altura (cm)", 140.0, 220.0, 170.0, 1.0)
    edad   = st.number_input("Edad (años)",    18,    90,   30,   1)

    st.markdown("---")
    st.markdown("## 🍽️ Comida consumida")
    comida_sel    = st.selectbox("¿Qué has comido?", list(COMIDA.keys()), index=2)
    factor_comida = COMIDA[comida_sel]

    st.markdown("---")
    st.markdown("## ⏰ Hora actual")
    st.info(f"🕐 **{ahora.strftime('%H:%M')}** hrs\n\n📍 Santiago de Chile")
    st.caption("Hora tomada automáticamente del sistema (America/Santiago).")

    st.markdown("---")
    st.markdown("## 🚗 ¿A qué hora quieres manejar?")
    if "hora_manejo" not in st.session_state:
        st.session_state["hora_manejo"] = ahora.replace(hour=min(ahora.hour + 3, 23), minute=0).time()
    hora_manejo_input = st.time_input(
        "Hora objetivo para manejar",
        key="hora_manejo"
    )
    dt_manejo = datetime.combine(hoy, hora_manejo_input)
    if dt_manejo <= ahora:
        dt_manejo += timedelta(days=1)
    horas_hasta_manejo = (dt_manejo - ahora).total_seconds() / 3600.0
    st.caption(f"Faltan **{horas_hasta_manejo:.1f} horas** para las {dt_manejo.strftime('%H:%M')}.")

    r = factor_widmark(peso, altura, edad, sexo)
    st.markdown("---")
    st.caption(f"Factor Widmark (r): **{r:.3f}**")
    st.caption("Tasa eliminación: **0.15 g/L/hora**")

# ─────────────────────────────────────────────
# TABLA DE CONSUMO
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🍹 Registro de Consumo</div>', unsafe_allow_html=True)
st.markdown(
    "Registra tragos **pasados** (ya consumidos) y **futuros** (lo que planeas tomar). "
    "Los futuros se muestran en azul y afectan el BAC proyectado."
)

# Encabezados
hc1, hc2, hc3, hc4, hc5 = st.columns([4, 1, 2, 1, 1])
hc1.markdown("<small style='color:#888'>**Trago**</small>", unsafe_allow_html=True)
hc2.markdown("<small style='color:#888'>**Cant.**</small>", unsafe_allow_html=True)
hc3.markdown("<small style='color:#888'>**Hora de consumo**</small>", unsafe_allow_html=True)
hc4.markdown("<small style='color:#888'>**Tipo**</small>", unsafe_allow_html=True)
hc5.markdown("<small style='color:#888'>**✕**</small>", unsafe_allow_html=True)

eventos_consumo = []

for fila in st.session_state.filas:
    fid = fila["id"]
    c1, c2, c3, c4, c5 = st.columns([4, 1, 2, 1, 1])

    with c1:
        trago_sel = st.selectbox(
            "Trago", TRAGOS_LISTA,
            key=f"trago_{fid}",
            label_visibility="collapsed"
        )
    with c2:
        cantidad = st.number_input(
            "Cant", min_value=1, max_value=20, value=1, step=1,
            key=f"cant_{fid}",
            label_visibility="collapsed"
        )
    with c3:
        hora_trago = st.time_input(
            "Hora", value=ahora.replace(minute=0).time(),
            key=f"hora_{fid}",
            label_visibility="collapsed"
        )
    with c4:
        # Determinar automáticamente si es pasado o futuro
        dt_trago = datetime.combine(hoy, hora_trago)
        # Si la hora está más de 8h en el futuro, probablemente es "mañana"
        # pero dentro de la misma noche de fiesta se considera hoy
        if dt_trago > ahora + timedelta(hours=12):
            dt_trago -= timedelta(days=1)
        es_futuro = dt_trago > ahora
        if es_futuro:
            st.markdown("<div style='padding-top:0.45rem'><span class='tag-futuro'>FUTURO</span></div>",
                        unsafe_allow_html=True)
        else:
            st.markdown("<div style='padding-top:0.45rem'><span class='tag-pasado'>YA TOMADO</span></div>",
                        unsafe_allow_html=True)
    with c5:
        st.markdown("<div style='padding-top:0.2rem'>", unsafe_allow_html=True)
        if len(st.session_state.filas) > 1:
            if st.button("✕", key=f"del_{fid}", help="Eliminar fila"):
                eliminar_fila(fid)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Info del trago
    t_info = TRAGOS[trago_sel]
    g_unit = gramos_etanol(t_info["ml"], t_info["grad"])
    color_info = "#5dade2" if es_futuro else "#777"
    st.markdown(
        f"<small style='color:{color_info};margin-left:4px'>"
        f"{t_info['ml']}ml · {t_info['grad']}° · "
        f"{g_unit:.1f}g etanol c/u · **{g_unit * cantidad:.1f}g total**"
        f"{'  🔮 planificado' if es_futuro else ''}"
        f"</small>",
        unsafe_allow_html=True
    )

    eventos_consumo.append({
        "nombre": trago_sel,
        "cantidad": cantidad,
        "dt": dt_trago,
        "gramos": g_unit * cantidad,
        "es_futuro": es_futuro,
    })

# Botón agregar
st.markdown("<br>", unsafe_allow_html=True)
col_add, col_calc = st.columns([1, 3])
with col_add:
    st.button("➕ Agregar trago", on_click=agregar_fila, use_container_width=True)
with col_calc:
    st.button("🔍 CALCULAR", use_container_width=True, type="primary")

# ─────────────────────────────────────────────
# CÁLCULOS
# ─────────────────────────────────────────────
gramos_total   = sum(ev["gramos"] for ev in eventos_consumo)
gramos_pasado  = sum(ev["gramos"] for ev in eventos_consumo if not ev["es_futuro"])
gramos_futuro  = sum(ev["gramos"] for ev in eventos_consumo if ev["es_futuro"])

bac_ahora      = bac_en_momento(eventos_consumo, factor_comida, peso, r, ahora)
bac_al_manejar = bac_en_momento(eventos_consumo, factor_comida, peso, r, dt_manejo)

# Hora más temprana en que se puede manejar (BAC < 0.30)
# Buscamos iterando minuto a minuto desde ahora
def hora_ok_para_manejar(eventos, factor_comida, peso, r, desde):
    dt = desde
    for _ in range(24 * 60):  # máximo 24h
        if bac_en_momento(eventos, factor_comida, peso, r, dt) < LIMITE_CONDUCIR:
            return dt
        dt += timedelta(minutes=1)
    return None

dt_ok = hora_ok_para_manejar(eventos_consumo, factor_comida, peso, r, ahora)

# ─────────────────────────────────────────────
# RESULTADOS
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">📊 Resultados</div>', unsafe_allow_html=True)

# Sidebar resumen
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🧮 Resumen")
    st.caption(f"Etanol consumido: **{gramos_pasado:.1f} g**")
    if gramos_futuro > 0:
        st.caption(f"Etanol planificado: **{gramos_futuro:.1f} g**")
    st.caption(f"BAC ahora: **{bac_ahora:.3f} g/L**")
    st.caption(f"BAC a las {dt_manejo.strftime('%H:%M')}: **{bac_al_manejar:.3f} g/L**")

# Métricas principales
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🩸 BAC Ahora (g/L)", f"{bac_ahora:.3f}",
              delta=f"Límite: {LIMITE_CONDUCIR} g/L",
              delta_color="inverse" if bac_ahora > LIMITE_CONDUCIR else "normal")
with col2:
    st.metric(f"🚗 BAC a las {dt_manejo.strftime('%H:%M')} (g/L)",
              f"{bac_al_manejar:.3f}",
              delta="✅ Apto" if bac_al_manejar < LIMITE_CONDUCIR else "🚫 No apto",
              delta_color="normal" if bac_al_manejar < LIMITE_CONDUCIR else "inverse")
with col3:
    st.metric("🍸 Etanol ya consumido", f"{gramos_pasado:.1f} g")
with col4:
    if gramos_futuro > 0:
        st.metric("🔮 Etanol planificado", f"{gramos_futuro:.1f} g")
    else:
        st.metric("🍹 Tragos registrados", f"{len(eventos_consumo)}")

# ── Estado actual ──
st.markdown("<br>", unsafe_allow_html=True)
if bac_ahora == 0.0:
    st.markdown('<div class="status-safe">✅ BAC actual: 0.000 g/L — Sin alcohol. Puedes conducir.</div>',
                unsafe_allow_html=True)
elif bac_ahora < LIMITE_CONDUCIR:
    st.markdown(f'<div class="status-safe">✅ BAC actual {bac_ahora:.3f} g/L — Bajo el límite. Apto para conducir ahora.</div>',
                unsafe_allow_html=True)
elif bac_ahora < LIMITE_EBRIEDAD:
    st.markdown(f'<div class="status-warning">⚠️ BAC actual {bac_ahora:.3f} g/L — INFRACCIÓN GRAVE. Prohibido conducir ahora.</div>',
                unsafe_allow_html=True)
else:
    st.markdown(f'<div class="status-danger">🚫 BAC actual {bac_ahora:.3f} g/L — ESTADO DE EBRIEDAD. DELITO conducir.</div>',
                unsafe_allow_html=True)

# ── Estado al momento de manejar ──
st.markdown("<br>", unsafe_allow_html=True)
if bac_al_manejar < LIMITE_CONDUCIR:
    st.markdown(
        f'<div class="status-safe">🚗 A las {dt_manejo.strftime("%H:%M")} tu BAC será ~{bac_al_manejar:.3f} g/L — '
        f'✅ Podrás manejar.</div>',
        unsafe_allow_html=True)
elif bac_al_manejar < LIMITE_EBRIEDAD:
    st.markdown(
        f'<div class="status-warning">🚗 A las {dt_manejo.strftime("%H:%M")} tu BAC será ~{bac_al_manejar:.3f} g/L — '
        f'⚠️ Seguirás en infracción. '
        f'{"Podrás manejar a las " + dt_ok.strftime("%H:%M") if dt_ok else "No podrás manejar en las próximas 24h"}.</div>',
        unsafe_allow_html=True)
else:
    st.markdown(
        f'<div class="status-danger">🚗 A las {dt_manejo.strftime("%H:%M")} tu BAC será ~{bac_al_manejar:.3f} g/L — '
        f'🚫 En estado de ebriedad. '
        f'{"Podrás manejar a las " + dt_ok.strftime("%H:%M") if dt_ok else "No podrás manejar en las próximas 24h"}.</div>',
        unsafe_allow_html=True)

# ── Gráfico ─────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">📈 Curva de BAC en el Tiempo</div>',
            unsafe_allow_html=True)

df = curva_bac(eventos_consumo, factor_comida, peso, r, ahora, ventana_h=16)

if not df.empty and gramos_total > 0:
    # Convertir tiempos a string para compatibilidad con Plotly
    ahora_str    = ahora.strftime("%Y-%m-%d %H:%M:%S")
    manejo_str   = dt_manejo.strftime("%Y-%m-%d %H:%M:%S")
    df["tiempo_str"] = df["tiempo"].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))
    df_pasado = df[df["tiempo"] <= ahora].copy()
    df_futuro = df[df["tiempo"] >= ahora].copy()

    y_max = max(df["bac"].max() * 1.25, LIMITE_EBRIEDAD + 0.1)
    fig = go.Figure()

    # Zonas
    fig.add_hrect(y0=LIMITE_EBRIEDAD, y1=y_max,
                  fillcolor="rgba(231,76,60,0.15)", line_width=0,
                  annotation_text="Ebriedad ≥0.50 g/L",
                  annotation_font_color="#e74c3c",
                  annotation_position="top right")
    fig.add_hrect(y0=LIMITE_CONDUCIR, y1=LIMITE_EBRIEDAD,
                  fillcolor="rgba(243,156,18,0.12)", line_width=0,
                  annotation_text="Infracción 0.30–0.50 g/L",
                  annotation_font_color="#f39c12",
                  annotation_position="top right")
    fig.add_hrect(y0=0, y1=LIMITE_CONDUCIR,
                  fillcolor="rgba(39,174,96,0.07)", line_width=0)

    # Líneas límite horizontales (sin anotaciones para evitar bug Plotly)
    fig.add_shape(type="line", x0=0, x1=1, xref="paper",
                  y0=LIMITE_CONDUCIR, y1=LIMITE_CONDUCIR,
                  line=dict(color="#f39c12", width=1.5, dash="dash"))
    fig.add_shape(type="line", x0=0, x1=1, xref="paper",
                  y0=LIMITE_EBRIEDAD, y1=LIMITE_EBRIEDAD,
                  line=dict(color="#e74c3c", width=1.5, dash="dash"))

    if not df_pasado.empty:
        fig.add_trace(go.Scatter(
            x=df_pasado["tiempo_str"], y=df_pasado["bac"],
            mode="lines", name="BAC (consumido)",
            line=dict(color="#C0392B", width=3),
            fill="tozeroy", fillcolor="rgba(192,57,43,0.12)"
        ))
    if not df_futuro.empty:
        fig.add_trace(go.Scatter(
            x=df_futuro["tiempo_str"], y=df_futuro["bac"],
            mode="lines", name="BAC (proyectado)",
            line=dict(color="#3498db", width=2.5, dash="dot"),
            fill="tozeroy", fillcolor="rgba(52,152,219,0.08)"
        ))

    # Línea vertical "Ahora" como Scatter
    fig.add_trace(go.Scatter(
        x=[ahora_str, ahora_str], y=[0, y_max],
        mode="lines", name="Ahora",
        line=dict(color="rgba(255,255,255,0.4)", width=1.5),
        showlegend=False,
        hoverinfo="skip"
    ))
    # Etiqueta "Ahora"
    fig.add_trace(go.Scatter(
        x=[ahora_str], y=[y_max * 0.95],
        mode="text", text=["Ahora"],
        textfont=dict(color="white", size=11),
        showlegend=False, hoverinfo="skip"
    ))

    # Punto ahora
    fig.add_trace(go.Scatter(
        x=[ahora_str], y=[bac_ahora],
        mode="markers", name=f"Ahora ({bac_ahora:.3f} g/L)",
        marker=dict(color="#f1c40f", size=13, symbol="diamond",
                    line=dict(color="white", width=2)),
    ))

    # Línea vertical "Hora de manejo" como Scatter
    fig.add_trace(go.Scatter(
        x=[manejo_str, manejo_str], y=[0, y_max],
        mode="lines", name=f"Manejar {dt_manejo.strftime('%H:%M')}",
        line=dict(color="rgba(52,152,219,0.6)", width=1.5, dash="dash"),
        showlegend=False,
        hoverinfo="skip"
    ))
    fig.add_trace(go.Scatter(
        x=[manejo_str], y=[y_max * 0.88],
        mode="text", text=[f"🚗 {dt_manejo.strftime('%H:%M')}"],
        textfont=dict(color="#3498db", size=11),
        showlegend=False, hoverinfo="skip"
    ))

    # Punto hora de manejo
    color_manejo = "#27ae60" if bac_al_manejar < LIMITE_CONDUCIR else "#e74c3c"
    fig.add_trace(go.Scatter(
        x=[manejo_str], y=[bac_al_manejar],
        mode="markers", name=f"Al manejar ({bac_al_manejar:.3f} g/L)",
        marker=dict(color=color_manejo, size=13, symbol="star",
                    line=dict(color="white", width=2)),
    ))

    # Punto OK para manejar
    if dt_ok and dt_ok > ahora:
        ok_str = dt_ok.strftime("%Y-%m-%d %H:%M:%S")
        fig.add_trace(go.Scatter(
            x=[ok_str], y=[LIMITE_CONDUCIR],
            mode="markers+text", name=f"OK manejar ({dt_ok.strftime('%H:%M')})",
            marker=dict(color="#27ae60", size=11, symbol="triangle-up",
                        line=dict(color="white", width=2)),
            text=[f"  ✅ {dt_ok.strftime('%H:%M')}"],
            textposition="top right",
            textfont=dict(color="#27ae60", size=11)
        ))

    # Marcas verticales de tragos como Scatter
    for ev in eventos_consumo:
        ev_str = ev["dt"].strftime("%Y-%m-%d %H:%M:%S")
        color_marca = "rgba(52,152,219,0.25)" if ev["es_futuro"] else "rgba(192,57,43,0.25)"
        fig.add_trace(go.Scatter(
            x=[ev_str, ev_str], y=[0, y_max],
            mode="lines",
            line=dict(color=color_marca, width=1, dash="dot"),
            showlegend=False, hoverinfo="skip"
        ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15,15,30,0.95)",
        plot_bgcolor="rgba(15,15,30,0.95)",
        title=dict(text="Evolución del BAC · Línea punteada azul = proyección futura",
                   font=dict(family="Raleway", size=15, color="white")),
        xaxis=dict(tickformat="%H:%M", gridcolor="rgba(255,255,255,0.05)",
                   color="white", title="Hora (Santiago)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", color="white",
                   title="BAC (g/L)", ticksuffix=" g/L", range=[0, y_max]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, font=dict(color="white")),
        hovermode="x unified", height=440,
        margin=dict(t=70, b=40, l=60, r=30)
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Info legal ───────────────────────────────
with st.expander("⚖️ Marco Legal Chileno — Ley 18.290 Art. 196"):
    st.markdown("""
| BAC (g/L) | Situación Legal |
|---|---|
| < 0.30 | ✅ Legal, sin sanción |
| 0.30 – < 0.50 | ⚠️ **Infracción grave**: multa + suspensión licencia 1 año |
| ≥ 0.50 | 🚫 **Estado de ebriedad**: delito, cárcel hasta 5 años, cancelación definitiva licencia |

> Chile mide en **g/L**. Tasa de eliminación promedio: **0.15 g/L/hora**.
    """)

st.markdown("""
<div class="disclaimer">
⚠️ <b>AVISO:</b> Valores estimados con el modelo de Widmark. El BAC real varía según
metabolismo individual, medicamentos e hidratación.
<b>Ante cualquier duda, no manejes.</b> Usa taxi, Uber o designa un conductor.
Esta herramienta no reemplaza un alcoholímetro certificado.
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center;color:#555;font-size:0.75rem'>
Calculadora BAC Chile · Modelo de Widmark · Solo uso informativo · 🇨🇱 America/Santiago<br>
<b>¿Tomaste? No manejes. 🚗❌🍺</b>
</div>
""", unsafe_allow_html=True)
