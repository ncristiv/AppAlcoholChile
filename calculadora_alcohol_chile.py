"""
Calculadora de Alcohol en Sangre - Chile
=========================================
Estima el BAC (Blood Alcohol Content) y el tiempo para estar bajo el límite legal chileno.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

# ─────────────────────────────────────────────
# Configuración de página
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Calculadora BAC Chile 🇨🇱",
    page_icon="🍻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Estilos CSS personalizados
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@300;400;600;700;900&family=Lato:wght@300;400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Lato', sans-serif;
}

h1, h2, h3 {
    font-family: 'Raleway', sans-serif !important;
}

.main-title {
    font-family: 'Raleway', sans-serif;
    font-size: 2.8rem;
    font-weight: 900;
    color: #C0392B;
    letter-spacing: -1px;
    line-height: 1.1;
}

.subtitle {
    font-family: 'Lato', sans-serif;
    color: #7f8c8d;
    font-size: 1.05rem;
    margin-top: -0.5rem;
}

.metric-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.metric-value {
    font-family: 'Raleway', sans-serif;
    font-size: 3rem;
    font-weight: 900;
    line-height: 1;
    margin: 0.3rem 0;
}

.metric-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #95a5a6;
}

.status-safe {
    background: linear-gradient(135deg, #0f3460, #16213e);
    border-left: 4px solid #27ae60;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    color: #2ecc71;
    font-family: 'Raleway', sans-serif;
    font-weight: 700;
    font-size: 1.1rem;
}

.status-warning {
    background: linear-gradient(135deg, #3d1c00, #1a0a00);
    border-left: 4px solid #f39c12;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    color: #f39c12;
    font-family: 'Raleway', sans-serif;
    font-weight: 700;
    font-size: 1.1rem;
}

.status-danger {
    background: linear-gradient(135deg, #2c0000, #1a0000);
    border-left: 4px solid #e74c3c;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    color: #e74c3c;
    font-family: 'Raleway', sans-serif;
    font-weight: 700;
    font-size: 1.1rem;
}

.drink-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 0.8rem 1rem;
    margin: 0.4rem 0;
}

.disclaimer {
    background: rgba(231,76,60,0.1);
    border: 1px solid rgba(231,76,60,0.3);
    border-radius: 8px;
    padding: 1rem;
    font-size: 0.82rem;
    color: #e74c3c;
    margin-top: 1rem;
}

.section-header {
    font-family: 'Raleway', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #C0392B;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 1.5rem 0 0.8rem 0;
    border-bottom: 2px solid rgba(192,57,43,0.3);
    padding-bottom: 0.4rem;
}

div[data-testid="stMetricValue"] {
    font-family: 'Raleway', sans-serif !important;
    font-weight: 900 !important;
}

.stButton>button {
    background: linear-gradient(135deg, #C0392B, #922B21);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Raleway', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    padding: 0.6rem 2rem;
    letter-spacing: 1px;
    transition: all 0.2s ease;
    width: 100%;
}

.stButton>button:hover {
    background: linear-gradient(135deg, #E74C3C, #C0392B);
    box-shadow: 0 4px 15px rgba(192,57,43,0.4);
    transform: translateY(-1px);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a0a00 0%, #0d0d0d 100%);
    border-right: 1px solid rgba(192,57,43,0.2);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATOS: Tragos chilenos típicos de matrimonio
# ─────────────────────────────────────────────
TRAGOS = {
    "🍺 Cerveza (latita 355ml)": {
        "ml": 355,
        "graduacion": 5.0,
        "descripcion": "Cerveza estándar, latita 355ml",
        "icono": "🍺"
    },
    "🍺 Cerveza (botella 330ml)": {
        "ml": 330,
        "graduacion": 5.0,
        "descripcion": "Cerveza botella pequeña",
        "icono": "🍺"
    },
    "🍺 Schop (500ml)": {
        "ml": 500,
        "graduacion": 5.0,
        "descripcion": "Schop grande de cerveza",
        "icono": "🍺"
    },
    "🍹 Pisco Sour (120ml copa)": {
        "ml": 120,
        "graduacion": 14.0,
        "descripcion": "Pisco sour chileno: 50ml pisco 35°, 40ml limón, 20ml azúcar, hielo",
        "icono": "🍹"
    },
    "🥃 Pisco con Coca-Cola (250ml)": {
        "ml": 250,
        "graduacion": 10.0,
        "descripcion": "Vaso con ~60ml pisco + Coca-Cola",
        "icono": "🥃"
    },
    "🥃 Whisky en las rocas (90ml)": {
        "ml": 90,
        "graduacion": 40.0,
        "descripcion": "Trago doble de whisky 40° con hielo",
        "icono": "🥃"
    },
    "🥃 Whisky con soda (250ml)": {
        "ml": 250,
        "graduacion": 14.0,
        "descripcion": "Highball: ~60ml whisky + soda water",
        "icono": "🥃"
    },
    "🍸 Mojito Cubano (300ml)": {
        "ml": 300,
        "graduacion": 8.5,
        "descripcion": "Ron blanco, limón, menta, azúcar, soda. ~60ml ron",
        "icono": "🍸"
    },
    "🥂 Tequila shot (45ml)": {
        "ml": 45,
        "graduacion": 38.0,
        "descripcion": "Shot estándar de tequila 38°",
        "icono": "🥂"
    },
    "🍹 Margarita (150ml)": {
        "ml": 150,
        "graduacion": 16.0,
        "descripcion": "Margarita: 50ml tequila, triple sec, limón",
        "icono": "🍹"
    },
    "🍷 Vino tinto (150ml copa)": {
        "ml": 150,
        "graduacion": 13.0,
        "descripcion": "Copa estándar de vino tinto chileno",
        "icono": "🍷"
    },
    "🥂 Champaña / Espumante (150ml)": {
        "ml": 150,
        "graduacion": 11.5,
        "descripcion": "Copa de brindis, espumante chileno",
        "icono": "🥂"
    },
    "🍹 Chilcano (250ml)": {
        "ml": 250,
        "graduacion": 10.0,
        "descripcion": "Pisco + ginger ale + limón. ~60ml pisco",
        "icono": "🍹"
    },
    "🍸 Aperol Spritz (200ml)": {
        "ml": 200,
        "graduacion": 8.0,
        "descripcion": "Aperol + prosecco + soda",
        "icono": "🍸"
    },
}

# Efecto de comida en la absorción del alcohol
COMIDA = {
    "🚫 Nada (estómago vacío)": 1.0,
    "🥗 Snacks livianos (crudités, maní)": 0.85,
    "🥘 Comida de cóctel (entradas, finger food)": 0.70,
    "🍖 Cena completa (primer plato + fondo)": 0.55,
    "🍽️ Cena abundante + pan + postre": 0.45,
}

# ─────────────────────────────────────────────
# Límites legales Chile (Ley de Tránsito)
# ─────────────────────────────────────────────
# Art. 196 Ley 18.290:
LIMITE_CONDUCIR = 0.30    # g/L → desde 0.3 hasta <0.5 es infracción grave (multa)
LIMITE_EBRIEDAD = 0.50    # g/L → ≥0.5 es estado de ebriedad (delito)

# ─────────────────────────────────────────────
# Funciones de cálculo
# ─────────────────────────────────────────────

def calcular_agua_corporal(peso_kg: float, altura_cm: float, edad: int, sexo: str) -> float:
    """
    Calcula el agua corporal total (TBW) en litros usando la fórmula de Watson.
    Esta es la base del factor de distribución de Widmark.
    """
    if sexo == "Masculino":
        tbw = 2.447 - (0.09516 * edad) + (0.1074 * altura_cm) + (0.3362 * peso_kg)
    else:
        tbw = -2.097 + (0.1069 * altura_cm) + (0.2466 * peso_kg)
    return max(tbw, 1.0)  # mínimo 1L para evitar división por cero


def calcular_factor_widmark(peso_kg: float, altura_cm: float, edad: int, sexo: str) -> float:
    """
    Factor 'r' de Widmark (fracción del peso corporal que es agua).
    Varía según composición corporal.
    Valores típicos: hombres ~0.68, mujeres ~0.55
    """
    tbw = calcular_agua_corporal(peso_kg, altura_cm, edad, sexo)
    r = (tbw * 0.8) / peso_kg  # 0.8 ajusta TBW a agua donde se distribuye alcohol
    # Clamping a rangos fisiológicos razonables
    if sexo == "Masculino":
        r = max(0.55, min(r, 0.85))
    else:
        r = max(0.45, min(r, 0.75))
    return r


def gramos_alcohol_trago(trago_nombre: str, cantidad: int) -> float:
    """Calcula gramos de etanol para N unidades de un trago."""
    t = TRAGOS[trago_nombre]
    # Fórmula: ml × (graduacion/100) × 0.789 (densidad etanol)
    gramos_por_unidad = t["ml"] * (t["graduacion"] / 100) * 0.789
    return gramos_por_unidad * cantidad


def calcular_bac_en_momento(
    gramos_totales: float,
    peso_kg: float,
    r: float,
    factor_comida: float,
    horas_desde_ultimo_trago: float,
    horas_desde_primer_trago: float
) -> float:
    """
    Calcula el BAC actual usando la ecuación de Widmark modificada.

    BAC = (A × factor_absorcion) / (r × peso_kg) - (β × t_eliminacion)

    donde:
    - A = gramos de alcohol totales
    - r = factor de distribución de Widmark
    - β = tasa de eliminación hepática (~0.015 g/dL/hora ≈ 0.15 g/L/hora)
    - t = horas desde que el alcohol fue absorbido completamente
    """
    # Tasa de eliminación: 0.10 a 0.20 g/L/hora; promedio 0.15
    beta = 0.15  # g/L por hora

    # Ajuste de absorción por comida (factor_comida reduce el pico)
    gramos_absorbidos = gramos_totales * factor_comida

    # BAC pico (en g/L — Chile usa g/L, también expresado como g/dL × 10)
    bac_pico = (gramos_absorbidos / (r * peso_kg)) * 100  # ×100: g/kg → g/L aproximado

    # Tiempo de absorción: ~30-60 min según comida; estimamos 45min base
    t_absorcion = 0.75 * (1 + (1 - factor_comida))  # más comida = más lento

    # Tiempo efectivo de eliminación desde que comenzó la absorción
    t_elim = max(0.0, horas_desde_primer_trago - t_absorcion)

    bac_actual = max(0.0, bac_pico - (beta * t_elim))
    return round(bac_actual, 3)


def tiempo_para_limite(bac_actual: float, limite: float) -> float:
    """Horas necesarias para bajar de bac_actual al límite dado."""
    beta = 0.15
    if bac_actual <= limite:
        return 0.0
    return (bac_actual - limite) / beta


def generar_curva_bac(
    gramos_totales: float,
    peso_kg: float,
    r: float,
    factor_comida: float,
    hora_inicio: datetime,
    ventana_horas: int = 12
) -> pd.DataFrame:
    """Genera la curva de BAC a lo largo del tiempo."""
    beta = 0.15
    t_absorcion = 0.75 * (1 + (1 - factor_comida))

    gramos_absorbidos = gramos_totales * factor_comida
    bac_pico = (gramos_absorbidos / (r * peso_kg)) * 100

    puntos = []
    for min_offset in range(0, ventana_horas * 60 + 1, 15):
        h = min_offset / 60
        t_elim = max(0.0, h - t_absorcion)
        bac = max(0.0, bac_pico - (beta * t_elim))
        puntos.append({
            "tiempo": hora_inicio + timedelta(minutes=min_offset),
            "bac": round(bac, 3),
            "horas": h
        })

    return pd.DataFrame(puntos)


def nivel_alerta(bac: float) -> tuple:
    """Retorna (color, emoji, descripción) según el nivel de BAC."""
    if bac == 0:
        return "#27ae60", "✅", "Sin alcohol detectable"
    elif bac < 0.30:
        return "#27ae60", "✅", "Bajo el límite legal — APTO para conducir"
    elif bac < 0.50:
        return "#f39c12", "⚠️", "Infracción grave (0.3–0.5 g/L) — PROHIBIDO conducir"
    elif bac < 1.0:
        return "#e74c3c", "🚫", "Estado de ebriedad — DELITO conducir"
    else:
        return "#8e44ad", "☠️", "Intoxicación severa — EMERGENCIA MÉDICA"


# ─────────────────────────────────────────────
# INTERFAZ
# ─────────────────────────────────────────────

# Header
col_title, col_flag = st.columns([5, 1])
with col_title:
    st.markdown('<div class="main-title">🍻 Calculadora BAC Chile</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Estimación de alcohol en sangre según Ley de Tránsito chilena (Art. 196, Ley 18.290)</div>', unsafe_allow_html=True)
with col_flag:
    st.markdown("<br>", unsafe_allow_html=True)

st.markdown("---")

# ─── SIDEBAR: Datos personales ───────────────
with st.sidebar:
    st.markdown("## 👤 Datos Personales")
    st.markdown("*Necesarios para calibrar el cálculo*")

    sexo = st.radio("Sexo biológico", ["Masculino", "Femenino"],
                    help="El metabolismo del alcohol varía según sexo biológico")

    peso = st.number_input("Peso (kg)", min_value=40.0, max_value=200.0,
                           value=75.0, step=0.5)

    altura = st.number_input("Altura (cm)", min_value=140.0, max_value=220.0,
                             value=170.0, step=1.0)

    edad = st.number_input("Edad (años)", min_value=18, max_value=90,
                           value=30, step=1)

    st.markdown("---")
    st.markdown("## 🍽️ Consumo de Comida")
    comida_seleccion = st.selectbox(
        "¿Qué has comido?",
        list(COMIDA.keys()),
        index=2
    )
    factor_comida = COMIDA[comida_seleccion]

    st.markdown("---")
    st.markdown("## ⏰ Tiempo de Consumo")
    hora_inicio = st.time_input("Hora del primer trago", value=datetime.now().replace(hour=20, minute=0))
    hora_actual = st.time_input("Hora actual", value=datetime.now().replace(hour=22, minute=0))

    # Calcular horas transcurridas
    hoy = datetime.today().date()
    dt_inicio = datetime.combine(hoy, hora_inicio)
    dt_actual = datetime.combine(hoy, hora_actual)
    if dt_actual < dt_inicio:
        dt_actual += timedelta(days=1)
    horas_transcurridas = (dt_actual - dt_inicio).total_seconds() / 3600

    st.metric("⏱️ Tiempo transcurrido", f"{horas_transcurridas:.1f} horas")

    # Factor Widmark calculado
    r = calcular_factor_widmark(peso, altura, edad, sexo)
    st.markdown(f"<small style='color:#666'>Factor Widmark calculado: **{r:.3f}**</small>",
                unsafe_allow_html=True)


# ─── MAIN: Selección de tragos ───────────────
st.markdown('<div class="section-header">🍹 Tragos Consumidos</div>', unsafe_allow_html=True)
st.markdown("Ingresa cuántas unidades tomaste de cada trago durante el evento:")

# Organizar tragos en 2 columnas
tragos_keys = list(TRAGOS.keys())
mitad = math.ceil(len(tragos_keys) / 2)
col_tragos1, col_tragos2 = st.columns(2)

conteo_tragos = {}

with col_tragos1:
    for trago in tragos_keys[:mitad]:
        t = TRAGOS[trago]
        g_alcohol = t["ml"] * (t["graduacion"] / 100) * 0.789
        n = st.number_input(
            f"{trago}",
            min_value=0,
            max_value=20,
            value=0,
            step=1,
            help=f"{t['descripcion']} | {t['ml']}ml · {t['graduacion']}° | ~{g_alcohol:.1f}g alcohol",
            key=f"trago_{trago}"
        )
        conteo_tragos[trago] = n

with col_tragos2:
    for trago in tragos_keys[mitad:]:
        t = TRAGOS[trago]
        g_alcohol = t["ml"] * (t["graduacion"] / 100) * 0.789
        n = st.number_input(
            f"{trago}",
            min_value=0,
            max_value=20,
            value=0,
            step=1,
            help=f"{t['descripcion']} | {t['ml']}ml · {t['graduacion']}° | ~{g_alcohol:.1f}g alcohol",
            key=f"trago_{trago}"
        )
        conteo_tragos[trago] = n


# ─── CALCULAR ────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
calcular = st.button("🔍 CALCULAR MI NIVEL DE ALCOHOL", use_container_width=True)

if calcular or True:  # Siempre mostrar resultados al cambiar valores
    # Total gramos de alcohol
    gramos_total = sum(
        gramos_alcohol_trago(trago, cant)
        for trago, cant in conteo_tragos.items()
    )

    total_tragos = sum(conteo_tragos.values())

    if gramos_total == 0:
        st.info("💡 Ingresa los tragos consumidos para ver el cálculo.")
    else:
        st.markdown("---")
        st.markdown('<div class="section-header">📊 Resultados</div>', unsafe_allow_html=True)

        # Calcular BAC actual
        bac_actual = calcular_bac_en_momento(
            gramos_total, peso, r, factor_comida,
            horas_transcurridas, horas_transcurridas
        )

        # Horas para cada límite
        horas_para_conducir = tiempo_para_limite(bac_actual, LIMITE_CONDUCIR)
        horas_para_legal = tiempo_para_limite(bac_actual, LIMITE_EBRIEDAD)

        hora_ok_conducir = dt_actual + timedelta(hours=horas_para_conducir)
        hora_ok_ebriedad = dt_actual + timedelta(hours=horas_para_legal)

        color_bac, emoji_bac, desc_bac = nivel_alerta(bac_actual)

        # ── Métricas principales ──
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)

        with col_m1:
            st.metric(
                label="🍺 BAC Actual (g/L)",
                value=f"{bac_actual:.3f}",
                delta=f"Límite conducir: {LIMITE_CONDUCIR} g/L",
                delta_color="inverse" if bac_actual > LIMITE_CONDUCIR else "normal"
            )

        with col_m2:
            st.metric(
                label="🍸 Gramos de alcohol",
                value=f"{gramos_total:.1f}g",
                delta=f"{total_tragos} trago{'s' if total_tragos != 1 else ''}"
            )

        with col_m3:
            if horas_para_conducir == 0:
                val_conducir = "¡Ya puedes!"
                delta_conducir = "Bajo el límite"
            else:
                h = int(horas_para_conducir)
                m = int((horas_para_conducir % 1) * 60)
                val_conducir = f"{h}h {m}m"
                delta_conducir = f"OK a las {hora_ok_conducir.strftime('%H:%M')}"

            st.metric(
                label="🚗 Para poder manejar",
                value=val_conducir,
                delta=delta_conducir
            )

        with col_m4:
            if horas_para_legal == 0:
                val_ebriedad = "Bajo límite"
                delta_ebriedad = "No ebriedad"
            else:
                h2 = int(horas_para_legal)
                m2 = int((horas_para_legal % 1) * 60)
                val_ebriedad = f"{h2}h {m2}m"
                delta_ebriedad = f"OK a las {hora_ok_ebriedad.strftime('%H:%M')}"

            st.metric(
                label="⚖️ Para salir de ebriedad",
                value=val_ebriedad,
                delta=delta_ebriedad
            )

        # ── Estado legal ──
        st.markdown("<br>", unsafe_allow_html=True)
        if bac_actual == 0:
            css_class = "status-safe"
            mensaje = "✅ Sin alcohol en sangre — Puedes conducir con total normalidad"
        elif bac_actual < LIMITE_CONDUCIR:
            css_class = "status-safe"
            mensaje = f"✅ BAC {bac_actual:.3f} g/L — Bajo el límite legal. Puedes conducir, pero recuerda que incluso niveles bajos afectan tus reflejos."
        elif bac_actual < LIMITE_EBRIEDAD:
            css_class = "status-warning"
            mensaje = f"⚠️ BAC {bac_actual:.3f} g/L — INFRACCIÓN GRAVE (0.30–0.50 g/L). Suspensión de licencia + multa. PROHIBIDO conducir. Puedes conducir a las {hora_ok_conducir.strftime('%H:%M')} aprox."
        else:
            css_class = "status-danger"
            mensaje = f"🚫 BAC {bac_actual:.3f} g/L — ESTADO DE EBRIEDAD. DELITO según Art. 196. Penas de cárcel + cancelación de licencia. NUNCA conduzcas. Podrías manejar a las {hora_ok_conducir.strftime('%H:%M')} aprox."

        st.markdown(f'<div class="{css_class}">{mensaje}</div>', unsafe_allow_html=True)

        # ── Gráfico de curva BAC ──
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">📈 Curva de Alcohol en el Tiempo</div>',
                    unsafe_allow_html=True)

        df_curva = generar_curva_bac(
            gramos_total, peso, r, factor_comida, dt_inicio, ventana_horas=14
        )

        fig = go.Figure()

        # Zona de ebriedad
        fig.add_hrect(
            y0=LIMITE_EBRIEDAD, y1=max(df_curva["bac"].max() * 1.2, LIMITE_EBRIEDAD + 0.2),
            fillcolor="rgba(231,76,60,0.15)", line_width=0,
            annotation_text="Estado de ebriedad (≥0.50)", annotation_position="top right",
            annotation_font_color="#e74c3c"
        )

        # Zona de infracción
        fig.add_hrect(
            y0=LIMITE_CONDUCIR, y1=LIMITE_EBRIEDAD,
            fillcolor="rgba(243,156,18,0.15)", line_width=0,
            annotation_text="Infracción grave (0.30–0.50)", annotation_position="top right",
            annotation_font_color="#f39c12"
        )

        # Zona segura
        fig.add_hrect(
            y0=0, y1=LIMITE_CONDUCIR,
            fillcolor="rgba(39,174,96,0.08)", line_width=0,
        )

        # Líneas límite
        fig.add_hline(y=LIMITE_CONDUCIR, line_dash="dash", line_color="#f39c12",
                      line_width=1.5)
        fig.add_hline(y=LIMITE_EBRIEDAD, line_dash="dash", line_color="#e74c3c",
                      line_width=1.5)

        # Curva principal
        fig.add_trace(go.Scatter(
            x=df_curva["tiempo"],
            y=df_curva["bac"],
            mode="lines",
            name="Tu BAC",
            line=dict(color="#C0392B", width=3),
            fill="tozeroy",
            fillcolor="rgba(192,57,43,0.15)"
        ))

        # Punto actual
        bac_en_dt_actual = calcular_bac_en_momento(
            gramos_total, peso, r, factor_comida,
            horas_transcurridas, horas_transcurridas
        )
        fig.add_trace(go.Scatter(
            x=[dt_actual],
            y=[bac_en_dt_actual],
            mode="markers+text",
            name="Ahora",
            marker=dict(color="#f1c40f", size=14, symbol="diamond",
                        line=dict(color="white", width=2)),
            text=["Ahora"],
            textposition="top center",
            textfont=dict(color="white", size=11)
        ))

        # Punto "OK para conducir"
        if horas_para_conducir > 0:
            fig.add_trace(go.Scatter(
                x=[hora_ok_conducir],
                y=[LIMITE_CONDUCIR],
                mode="markers+text",
                name="OK para manejar",
                marker=dict(color="#27ae60", size=12, symbol="star",
                            line=dict(color="white", width=2)),
                text=[f"🚗 {hora_ok_conducir.strftime('%H:%M')}"],
                textposition="top center",
                textfont=dict(color="#27ae60", size=11)
            ))

        fig.update_layout(
            title=dict(text="Evolución del BAC en el tiempo", font=dict(
                family="Raleway", size=16, color="white"
            )),
            xaxis_title="Hora",
            yaxis_title="BAC (g/L de sangre)",
            template="plotly_dark",
            paper_bgcolor="rgba(15,15,30,0.95)",
            plot_bgcolor="rgba(15,15,30,0.95)",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1,
                font=dict(color="white")
            ),
            hovermode="x unified",
            height=420,
            xaxis=dict(
                tickformat="%H:%M",
                gridcolor="rgba(255,255,255,0.05)",
                color="white"
            ),
            yaxis=dict(
                gridcolor="rgba(255,255,255,0.05)",
                color="white",
                ticksuffix=" g/L"
            ),
            margin=dict(t=60, b=40, l=60, r=30)
        )

        st.plotly_chart(fig, use_container_width=True)

        # ── Desglose de tragos ──
        tragos_consumidos = {k: v for k, v in conteo_tragos.items() if v > 0}
        if tragos_consumidos:
            st.markdown('<div class="section-header">🍹 Desglose de Tragos</div>',
                        unsafe_allow_html=True)

            cols_detalle = st.columns(3)
            for i, (trago, cant) in enumerate(tragos_consumidos.items()):
                col = cols_detalle[i % 3]
                with col:
                    g = gramos_alcohol_trago(trago, cant)
                    t_info = TRAGOS[trago]
                    st.markdown(f"""
                    <div class="drink-card">
                        <b>{trago}</b><br>
                        <small>×{cant} unidad{'es' if cant > 1 else ''}</small><br>
                        <small style="color:#C0392B">{g:.1f}g alcohol | {t_info['ml']*cant}ml</small>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Info legal ──
        with st.expander("⚖️ Marco Legal Chileno — Ley de Tránsito"):
            st.markdown("""
            **Ley 18.290 (modificada por Ley 20.770 "Ley Emilia") — Art. 196:**

            | BAC (g/L sangre) | Equivalente (g/dL) | Situación Legal |
            |---|---|---|
            | < 0.30 | < 0.03 | Legal. Sin sanción |
            | 0.30 – < 0.50 | 0.03 – < 0.05 | **Infracción grave**: multa + suspensión licencia 1 año |
            | ≥ 0.50 | ≥ 0.05 | **Estado de ebriedad**: delito, cárcel hasta 5 años, cancelación definitiva de licencia |

            > 📌 Chile mide en **g/L** (gramos de etanol por litro de sangre).
            La tasa de eliminación promedio es ~0.15 g/L por hora.
            Estos valores son **estimaciones** y varían individualmente.
            """)

        # ── Disclaimer ──
        st.markdown("""
        <div class="disclaimer">
        ⚠️ <b>AVISO IMPORTANTE:</b> Esta calculadora entrega estimaciones basadas en fórmulas farmacológicas estándar (modelo de Widmark).
        Los resultados son <b>orientativos</b> y pueden variar según factores individuales (metabolismo, medicamentos, tolerancia, hidratación, etc.).
        <b>Nunca conduzcas si has consumido alcohol.</b> En caso de duda, utiliza taxi, Uber, o designa un conductor. Esta herramienta no reemplaza un alcoholímetro certificado.
        </div>
        """, unsafe_allow_html=True)

# ─── Footer ──────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; color:#555; font-size:0.75rem; font-family:Lato">
Calculadora BAC Chile · Basada en el modelo de Widmark y Ley 18.290 · Solo uso informativo<br>
<b>¿Tomaste? No manejes. 🚗❌🍺</b>
</div>
""", unsafe_allow_html=True)
