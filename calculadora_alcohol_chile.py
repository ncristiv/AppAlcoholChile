"""
Calculadora de Alcohol en Sangre - Chile
Interfaz dinámica: agregar/eliminar filas de consumo
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
.section-header {
    font-family: 'Raleway', sans-serif; font-size: 1.05rem;
    font-weight: 700; color: #C0392B; text-transform: uppercase;
    letter-spacing: 2px; margin: 1.5rem 0 0.8rem 0;
    border-bottom: 2px solid rgba(192,57,43,0.3); padding-bottom: 0.4rem;
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
.row-container {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 0.6rem 0.8rem;
    margin-bottom: 0.5rem;
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
    beta = 0.15
    t_absorcion = 0.5 + 0.5 * (1.0 - factor_comida)
    gramos_absorbidos = gramos * factor_comida
    bac_pico = gramos_absorbidos / (r * peso_kg)
    t_elim = max(0.0, horas_desde_consumo - t_absorcion)
    return max(0.0, bac_pico - beta * t_elim)

def bac_total_fn(eventos, factor_comida, peso_kg, r, dt_actual):
    total = 0.0
    for ev in eventos:
        horas = max(0.0, (dt_actual - ev["dt"]).total_seconds() / 3600.0)
        total += bac_de_evento(ev["gramos"], factor_comida, peso_kg, r, horas)
    return round(total, 3)

def tiempo_para_limite(bac, limite):
    if bac <= limite:
        return 0.0
    return (bac - limite) / 0.15

def curva_bac(eventos, factor_comida, peso_kg, r, dt_actual, ventana_h=14):
    if not eventos:
        return pd.DataFrame()
    dt_inicio = min(ev["dt"] for ev in eventos)
    puntos = []
    for min_offset in range(0, ventana_h * 60 + 1, 10):
        dt = dt_inicio + timedelta(minutes=min_offset)
        b = bac_total_fn(eventos, factor_comida, peso_kg, r, dt)
        puntos.append({"tiempo": dt, "bac": b})
    return pd.DataFrame(puntos)

# ─────────────────────────────────────────────
# Estado de sesión: lista de filas de consumo
# ─────────────────────────────────────────────
if "filas" not in st.session_state:
    st.session_state.filas = [{"id": 0}]
if "next_id" not in st.session_state:
    st.session_state.next_id = 1

def agregar_fila():
    st.session_state.filas.append({"id": st.session_state.next_id})
    st.session_state.next_id += 1

def eliminar_fila(fila_id):
    st.session_state.filas = [f for f in st.session_state.filas if f["id"] != fila_id]

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="main-title">🍻 Calculadora BAC Chile</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Estimación de alcohol en sangre · Ley de Tránsito Art. 196, Ley 18.290</div>',
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
    comida_sel  = st.selectbox("¿Qué has comido?", list(COMIDA.keys()), index=2)
    factor_comida = COMIDA[comida_sel]

    st.markdown("---")
    st.markdown("## ⏰ Hora actual")
    # Hora actual fija al cargar la página (no editable)
    ahora = datetime.now()
    dt_actual = ahora
    st.info(f"🕐 **{ahora.strftime('%H:%M')}** hrs")
    st.caption("La hora actual se toma automáticamente del sistema.")

    r = factor_widmark(peso, altura, edad, sexo)
    st.markdown("---")
    st.caption(f"Factor Widmark (r): **{r:.3f}**")
    st.caption("Tasa eliminación: **0.15 g/L/hora**")

hoy = dt_actual.date()

# ─────────────────────────────────────────────
# TABLA DE CONSUMO DINÁMICA
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🍹 Registro de Consumo</div>', unsafe_allow_html=True)

# Encabezados
hc1, hc2, hc3, hc4 = st.columns([4, 1, 2, 1])
hc1.markdown("<small style='color:#888'>**Trago**</small>", unsafe_allow_html=True)
hc2.markdown("<small style='color:#888'>**Cantidad**</small>", unsafe_allow_html=True)
hc3.markdown("<small style='color:#888'>**Hora de consumo**</small>", unsafe_allow_html=True)
hc4.markdown("<small style='color:#888'>**Eliminar**</small>", unsafe_allow_html=True)

eventos_consumo = []

for fila in st.session_state.filas:
    fid = fila["id"]
    with st.container():
        c1, c2, c3, c4 = st.columns([4, 1, 2, 1])

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
                "Hora", value=ahora.replace(hour=20, minute=0).time(),
                key=f"hora_{fid}",
                label_visibility="collapsed"
            )
        with c4:
            st.markdown("<div style='padding-top:0.3rem'>", unsafe_allow_html=True)
            if len(st.session_state.filas) > 1:
                if st.button("✕", key=f"del_{fid}", help="Eliminar esta fila"):
                    eliminar_fila(fid)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # Info del trago seleccionado
        t_info = TRAGOS[trago_sel]
        g_unit = gramos_etanol(t_info["ml"], t_info["grad"])
        st.markdown(
            f"<small style='color:#777;margin-left:4px'>"
            f"{t_info['ml']}ml · {t_info['grad']}° · "
            f"{g_unit:.1f}g etanol c/u · "
            f"**{g_unit * cantidad:.1f}g total**</small>",
            unsafe_allow_html=True
        )

        # Registrar evento
        dt_trago = datetime.combine(hoy, hora_trago)
        if dt_trago > dt_actual:
            dt_trago -= timedelta(days=1)
        eventos_consumo.append({
            "nombre": trago_sel,
            "cantidad": cantidad,
            "dt": dt_trago,
            "gramos": g_unit * cantidad,
        })

# Botón agregar fila
st.markdown("<br>", unsafe_allow_html=True)
col_add, col_calc = st.columns([1, 3])
with col_add:
    st.button("➕ Agregar trago", on_click=agregar_fila, use_container_width=True)
with col_calc:
    calcular = st.button("🔍 CALCULAR MI NIVEL DE ALCOHOL", use_container_width=True,
                         type="primary")

# ─────────────────────────────────────────────
# RESULTADOS
# ─────────────────────────────────────────────
gramos_total = sum(ev["gramos"] for ev in eventos_consumo)

st.markdown("---")
st.markdown('<div class="section-header">📊 Resultados</div>', unsafe_allow_html=True)

bac_act = bac_total_fn(eventos_consumo, factor_comida, peso, r, dt_actual)
horas_conducir = tiempo_para_limite(bac_act, LIMITE_CONDUCIR)
horas_ebriedad = tiempo_para_limite(bac_act, LIMITE_EBRIEDAD)
dt_ok_conducir = dt_actual + timedelta(hours=horas_conducir)
dt_ok_ebriedad = dt_actual + timedelta(hours=horas_ebriedad)

# Verificación en sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🧮 Resumen")
    bac_pico_ref = (gramos_total * factor_comida) / (r * peso) if gramos_total > 0 else 0
    st.caption(f"Gramos totales etanol: **{gramos_total:.1f} g**")
    st.caption(f"BAC pico estimado: **{bac_pico_ref:.3f} g/L**")
    st.caption(f"BAC actual: **{bac_act:.3f} g/L**")

# Métricas
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🩸 BAC Actual (g/L)", f"{bac_act:.3f}",
              delta=f"Límite manejar: {LIMITE_CONDUCIR} g/L",
              delta_color="inverse" if bac_act > LIMITE_CONDUCIR else "normal")
with col2:
    st.metric("🍸 Gramos de alcohol", f"{gramos_total:.1f} g",
              delta=f"{sum(ev['cantidad'] for ev in eventos_consumo)} tragos")
with col3:
    if horas_conducir == 0:
        st.metric("🚗 Para manejar", "¡Ya puedes!", delta="Bajo el límite ✅")
    else:
        h, m = int(horas_conducir), int((horas_conducir % 1) * 60)
        st.metric("🚗 Para manejar", f"{h}h {m:02d}m",
                  delta=f"OK a las {dt_ok_conducir.strftime('%H:%M')}")
with col4:
    if horas_ebriedad == 0:
        st.metric("⚖️ Ebriedad legal", "No aplica", delta="No en estado de ebriedad")
    else:
        h2, m2 = int(horas_ebriedad), int((horas_ebriedad % 1) * 60)
        st.metric("⚖️ Fuera de ebriedad", f"{h2}h {m2:02d}m",
                  delta=f"OK a las {dt_ok_ebriedad.strftime('%H:%M')}")

st.markdown("<br>", unsafe_allow_html=True)
if bac_act == 0.0:
    st.markdown('<div class="status-safe">✅ Sin alcohol en sangre — Puedes conducir con normalidad.</div>',
                unsafe_allow_html=True)
elif bac_act < LIMITE_CONDUCIR:
    st.markdown(f'<div class="status-safe">✅ BAC {bac_act:.3f} g/L — Bajo el límite legal. Apto para conducir.</div>',
                unsafe_allow_html=True)
elif bac_act < LIMITE_EBRIEDAD:
    st.markdown(
        f'<div class="status-warning">⚠️ BAC {bac_act:.3f} g/L — INFRACCIÓN GRAVE (0.30–0.50 g/L). '
        f'Prohibido conducir. Podrías manejar aprox. a las {dt_ok_conducir.strftime("%H:%M")}.</div>',
        unsafe_allow_html=True)
else:
    st.markdown(
        f'<div class="status-danger">🚫 BAC {bac_act:.3f} g/L — ESTADO DE EBRIEDAD. DELITO. '
        f'Podrías manejar aprox. a las {dt_ok_conducir.strftime("%H:%M")}.</div>',
        unsafe_allow_html=True)

# ── Gráfico ─────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">📈 Curva de BAC en el Tiempo</div>',
            unsafe_allow_html=True)

df = curva_bac(eventos_consumo, factor_comida, peso, r, dt_actual, ventana_h=14)

if not df.empty and gramos_total > 0:
    y_max = max(df["bac"].max() * 1.25, LIMITE_EBRIEDAD + 0.1)
    fig = go.Figure()

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

    fig.add_hline(y=LIMITE_CONDUCIR, line_dash="dash",
                  line_color="#f39c12", line_width=1.5)
    fig.add_hline(y=LIMITE_EBRIEDAD, line_dash="dash",
                  line_color="#e74c3c", line_width=1.5)

    fig.add_trace(go.Scatter(
        x=df["tiempo"], y=df["bac"],
        mode="lines", name="Tu BAC",
        line=dict(color="#C0392B", width=3),
        fill="tozeroy", fillcolor="rgba(192,57,43,0.12)"
    ))
    fig.add_trace(go.Scatter(
        x=[dt_actual], y=[bac_act],
        mode="markers+text", name="Ahora",
        marker=dict(color="#f1c40f", size=14, symbol="diamond",
                    line=dict(color="white", width=2)),
        text=[f"  {bac_act:.3f} g/L"],
        textposition="top right",
        textfont=dict(color="white", size=11)
    ))

    # Líneas verticales por trago
    for ev in eventos_consumo:
        fig.add_vline(x=ev["dt"], line_dash="dot",
                      line_color="rgba(255,255,255,0.15)", line_width=1,
                      annotation_text=f"  {ev['nombre'][:15]}",
                      annotation_font_color="rgba(255,255,255,0.4)",
                      annotation_position="top left")

    if horas_conducir > 0:
        fig.add_trace(go.Scatter(
            x=[dt_ok_conducir], y=[LIMITE_CONDUCIR],
            mode="markers+text", name="OK para manejar",
            marker=dict(color="#27ae60", size=13, symbol="star",
                        line=dict(color="white", width=2)),
            text=[f"  🚗 {dt_ok_conducir.strftime('%H:%M')}"],
            textposition="top right",
            textfont=dict(color="#27ae60", size=11)
        ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15,15,30,0.95)",
        plot_bgcolor="rgba(15,15,30,0.95)",
        title=dict(text="Evolución del BAC",
                   font=dict(family="Raleway", size=16, color="white")),
        xaxis=dict(tickformat="%H:%M", gridcolor="rgba(255,255,255,0.05)",
                   color="white", title="Hora"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", color="white",
                   title="BAC (g/L)", ticksuffix=" g/L", range=[0, y_max]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, font=dict(color="white")),
        hovermode="x unified", height=420,
        margin=dict(t=60, b=40, l=60, r=30)
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
Calculadora BAC Chile · Modelo de Widmark · Solo uso informativo<br>
<b>¿Tomaste? No manejes. 🚗❌🍺</b>
</div>
""", unsafe_allow_html=True)
