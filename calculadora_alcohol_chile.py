"""
Calculadora BAC Chile — sesiones por email, persistencia JSON
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, time as dtime
from zoneinfo import ZoneInfo
import json, os, re

TZ = ZoneInfo("America/Santiago")
DB = "sesiones_bac.json"

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.set_page_config(page_title="Calculadora BAC Chile 🇨🇱", page_icon="🍻",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@400;700;900&family=Lato:wght@300;400;700&display=swap');
html,body,[class*="css"]{font-family:'Lato',sans-serif;}
h1,h2,h3{font-family:'Raleway',sans-serif !important;}
.main-title{font-family:'Raleway',sans-serif;font-size:2.4rem;font-weight:900;color:#C0392B;letter-spacing:-1px;}
.subtitle{color:#7f8c8d;font-size:.95rem;margin-top:-.4rem;}
.section-header{font-family:'Raleway',sans-serif;font-size:1rem;font-weight:700;color:#C0392B;
    text-transform:uppercase;letter-spacing:2px;margin:1.4rem 0 .7rem;
    border-bottom:2px solid rgba(192,57,43,.3);padding-bottom:.3rem;}
.status-safe{background:linear-gradient(135deg,#0f3460,#16213e);border-left:4px solid #27ae60;
    padding:1rem 1.5rem;border-radius:8px;color:#2ecc71;font-family:'Raleway',sans-serif;font-weight:700;}
.status-warning{background:linear-gradient(135deg,#3d1c00,#1a0a00);border-left:4px solid #f39c12;
    padding:1rem 1.5rem;border-radius:8px;color:#f39c12;font-family:'Raleway',sans-serif;font-weight:700;}
.status-danger{background:linear-gradient(135deg,#2c0000,#1a0000);border-left:4px solid #e74c3c;
    padding:1rem 1.5rem;border-radius:8px;color:#e74c3c;font-family:'Raleway',sans-serif;font-weight:700;}
.disclaimer{background:rgba(231,76,60,.1);border:1px solid rgba(231,76,60,.3);
    border-radius:8px;padding:1rem;font-size:.8rem;color:#e74c3c;margin-top:1rem;}
div[data-testid="stSidebar"]{background:linear-gradient(180deg,#1a0a00,#0d0d0d);
    border-right:1px solid rgba(192,57,43,.2);}
.tag-pasado{background:rgba(192,57,43,.15);color:#e74c3c;border-radius:4px;
    padding:1px 7px;font-size:.72rem;font-weight:700;}
.tag-futuro{background:rgba(52,152,219,.15);color:#3498db;border-radius:4px;
    padding:1px 7px;font-size:.72rem;font-weight:700;}
.session-card{background:rgba(39,174,96,.07);border:1px solid rgba(39,174,96,.2);
    border-radius:10px;padding:.9rem 1.2rem;margin-bottom:1rem;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PERSISTENCIA
# ─────────────────────────────────────────────
def cargar_db() -> dict:
    if os.path.exists(DB):
        try:
            return json.loads(open(DB, encoding="utf-8").read())
        except Exception:
            return {}
    return {}

def guardar_db(data: dict):
    open(DB, "w", encoding="utf-8").write(json.dumps(data, indent=2, default=str))

def email_valido(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()))

def guardar_sesion(email: str):
    """Serializa session_state → JSON y lo guarda bajo la clave email."""
    db = cargar_db()
    filas_serial = []
    for f in st.session_state.get("filas", []):
        fid = f["id"]
        hora_val = st.session_state.get(f"hora_{fid}", dtime(20, 0))
        filas_serial.append({
            "id":    fid,
            "trago": st.session_state.get(f"trago_{fid}", TRAGOS_LISTA[0]),
            "cant":  int(st.session_state.get(f"cant_{fid}", 1)),
            "hora":  hora_val.strftime("%H:%M") if hasattr(hora_val, "strftime") else str(hora_val)[:5],
        })
    hora_m = st.session_state.get("hora_manejo", dtime(23, 0))
    db[email.lower().strip()] = {
        "nombre":      st.session_state.get("nombre_usuario", ""),
        "sexo":        st.session_state.get("sexo_val",   "Masculino"),
        "peso":        st.session_state.get("peso_val",   75.0),
        "altura":      st.session_state.get("altura_val", 170.0),
        "edad":        st.session_state.get("edad_val",   30),
        "comida":      st.session_state.get("comida_val", COMIDA_LISTA[2]),
        "hora_manejo": hora_m.strftime("%H:%M") if hasattr(hora_m, "strftime") else str(hora_m)[:5],
        "filas":       filas_serial,
        "next_id":     st.session_state.get("next_id", 1),
        "guardado_en": datetime.now(TZ).strftime("%Y-%m-%d %H:%M"),
    }
    guardar_db(db)

def cargar_sesion(email: str) -> bool:
    """Carga datos guardados al session_state. Retorna True si existía."""
    db = cargar_db()
    data = db.get(email.lower().strip())
    if not data:
        return False

    st.session_state["nombre_usuario"] = data.get("nombre", "")
    st.session_state["sexo_val"]        = data.get("sexo",   "Masculino")
    st.session_state["peso_val"]        = float(data.get("peso",   75.0))
    st.session_state["altura_val"]      = float(data.get("altura", 170.0))
    st.session_state["edad_val"]        = int(data.get("edad", 30))
    st.session_state["comida_val"]      = data.get("comida", COMIDA_LISTA[2])

    filas_raw = data.get("filas", [])
    if filas_raw:
        st.session_state["filas"]   = [{"id": f["id"]} for f in filas_raw]
        st.session_state["next_id"] = int(data.get("next_id", max(f["id"] for f in filas_raw) + 1))
        for f in filas_raw:
            fid = f["id"]
            trago = f.get("trago", TRAGOS_LISTA[0])
            if trago not in TRAGOS_LISTA:
                trago = TRAGOS_LISTA[0]
            st.session_state[f"trago_{fid}"] = trago
            st.session_state[f"cant_{fid}"]  = int(f.get("cant", 1))
            try:
                h, m = str(f.get("hora", "20:00"))[:5].split(":")
                st.session_state[f"hora_{fid}"] = dtime(int(h), int(m))
            except Exception:
                st.session_state[f"hora_{fid}"] = dtime(20, 0)
    try:
        h, m = data.get("hora_manejo", "23:00")[:5].split(":")
        st.session_state["hora_manejo"] = dtime(int(h), int(m))
    except Exception:
        st.session_state["hora_manejo"] = dtime(23, 0)

    return True

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

COMIDA_LISTA = [
    "🚫 Nada (estómago vacío)",
    "🥗 Snacks livianos (maní, crudités)",
    "🥘 Entradas / finger food (cóctel)",
    "🍖 Cena completa (entrada + fondo)",
    "🍽️ Cena abundante + pan + postre",
]
COMIDA_FACTOR = {k: v for k, v in zip(COMIDA_LISTA, [1.0, 0.85, 0.70, 0.55, 0.45])}

LIMITE_CONDUCIR = 0.30
LIMITE_EBRIEDAD = 0.50

# ─────────────────────────────────────────────
# Funciones BAC
# ─────────────────────────────────────────────
def gramos_etanol(ml, grad):
    return ml * (grad / 100.0) * 0.789

def factor_widmark(peso_kg, altura_cm, edad, sexo):
    if sexo == "Masculino":
        tbw = 2.447 - 0.09516*edad + 0.1074*altura_cm + 0.3362*peso_kg
        return max(0.55, min(tbw/peso_kg, 0.85))
    tbw = -2.097 + 0.1069*altura_cm + 0.2466*peso_kg
    return max(0.45, min(tbw/peso_kg, 0.75))

def bac_de_evento(gramos, fc, peso_kg, r, horas):
    t_abs = 0.5 + 0.5*(1.0 - fc)
    bac_pico = (gramos * fc) / (r * peso_kg)
    return max(0.0, bac_pico - 0.15 * max(0.0, horas - t_abs))

def bac_en_momento(eventos, fc, peso_kg, r, dt_c):
    total = 0.0
    for ev in eventos:
        if ev["dt"] <= dt_c:
            h = (dt_c - ev["dt"]).total_seconds() / 3600.0
            total += bac_de_evento(ev["gramos"], fc, peso_kg, r, h)
    return round(total, 3)

def hora_ok_manejar(eventos, fc, peso_kg, r, desde):
    dt = desde
    for _ in range(24*60):
        if bac_en_momento(eventos, fc, peso_kg, r, dt) < LIMITE_CONDUCIR:
            return dt
        dt += timedelta(minutes=1)
    return None

def curva_bac(eventos, fc, peso_kg, r, ventana_h=16):
    if not eventos:
        return pd.DataFrame()
    dt_inicio = min(ev["dt"] for ev in eventos)
    dt_fin    = max(ev["dt"] for ev in eventos) + timedelta(hours=ventana_h)
    puntos, dt = [], dt_inicio
    while dt <= dt_fin:
        puntos.append({"t": dt.strftime("%Y-%m-%d %H:%M:%S"),
                       "bac": bac_en_momento(eventos, fc, peso_kg, r, dt),
                       "dt": dt})
        dt += timedelta(minutes=10)
    return pd.DataFrame(puntos)

# ─────────────────────────────────────────────
# Session state inicial
# ─────────────────────────────────────────────
for k, v in [("filas", [{"id": 0}]), ("next_id", 1),
             ("email_activo", ""), ("sesion_cargada", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

def agregar_fila():
    st.session_state.filas.append({"id": st.session_state.next_id})
    st.session_state.next_id += 1

def eliminar_fila(fid):
    st.session_state.filas = [f for f in st.session_state.filas if f["id"] != fid]

ahora     = datetime.now(TZ).replace(tzinfo=None)
hoy       = ahora.date()
ahora_str = ahora.strftime("%Y-%m-%d %H:%M:%S")

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="main-title">🍻 Calculadora BAC Chile</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Estimación de alcohol en sangre · Ley 18.290 · 🇨🇱 Hora de Santiago</div>',
            unsafe_allow_html=True)
st.markdown("---")

# ─────────────────────────────────────────────
# BLOQUE DE SESIÓN — email
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🔐 Tu Sesión</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns([3, 1, 1, 3])
with c1:
    email_input = st.text_input(
        "Ingresa tu email para guardar o cargar tu sesión",
        placeholder="tucorreo@ejemplo.com",
        value=st.session_state.get("email_activo", ""),
        label_visibility="visible"
    )

with c2:
    st.markdown("<div style='padding-top:1.8rem'>", unsafe_allow_html=True)
    if st.button("📂 Cargar sesión", use_container_width=True):
        if email_valido(email_input):
            ok = cargar_sesion(email_input)
            if ok:
                st.session_state["email_activo"]  = email_input.lower().strip()
                st.session_state["sesion_cargada"] = True
                st.rerun()
            else:
                st.session_state["email_activo"] = email_input.lower().strip()
                st.warning("No hay sesión guardada para ese email. Completa los datos y guarda.")
        else:
            st.error("Email no válido.")
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown("<div style='padding-top:1.8rem'>", unsafe_allow_html=True)
    if st.button("💾 Guardar sesión", use_container_width=True, type="primary"):
        if email_valido(email_input):
            st.session_state["email_activo"] = email_input.lower().strip()
            guardar_sesion(email_input)
            st.success(f"✅ Sesión guardada para **{email_input.lower().strip()}**")
        else:
            st.error("Ingresa un email válido para guardar.")
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    if st.session_state.get("email_activo"):
        db_check = cargar_db()
        data_check = db_check.get(st.session_state["email_activo"])
        if data_check:
            st.markdown(
                f"<div class='session-card' style='margin-top:.5rem'>"
                f"✅ Sesión activa: <b>{st.session_state['email_activo']}</b><br>"
                f"<small style='color:#888'>Último guardado: {data_check.get('guardado_en','—')}</small>"
                f"</div>",
                unsafe_allow_html=True
            )

st.markdown("---")

# ─────────────────────────────────────────────
# SIDEBAR — datos personales
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 👤 Datos Personales")

    sexo = st.radio("Sexo biológico", ["Masculino", "Femenino"],
                    index=0 if st.session_state.get("sexo_val", "Masculino") == "Masculino" else 1,
                    key="sexo_val")

    peso = st.number_input("Peso (kg)", 40.0, 200.0,
                           value=st.session_state.get("peso_val", 75.0),
                           step=0.5, key="peso_val")

    altura = st.number_input("Altura (cm)", 140.0, 220.0,
                             value=st.session_state.get("altura_val", 170.0),
                             step=1.0, key="altura_val")

    edad = st.number_input("Edad (años)", 18, 90,
                           value=st.session_state.get("edad_val", 30),
                           step=1, key="edad_val")

    st.markdown("---")
    st.markdown("## 🍽️ Comida consumida")
    comida_idx = COMIDA_LISTA.index(st.session_state["comida_val"]) \
        if st.session_state.get("comida_val") in COMIDA_LISTA else 2
    comida = st.selectbox("¿Qué has comido?", COMIDA_LISTA,
                          index=comida_idx, key="comida_val")
    factor_comida = COMIDA_FACTOR[comida]

    st.markdown("---")
    st.markdown("## ⏰ Hora actual")
    st.info(f"🕐 **{ahora.strftime('%H:%M')}** hrs\n\n📍 Santiago de Chile")

    st.markdown("---")
    st.markdown("## 🚗 ¿A qué hora quieres manejar?")
    if "hora_manejo" not in st.session_state:
        st.session_state["hora_manejo"] = dtime(min(ahora.hour + 3, 23), 0)
    hora_manejo = st.time_input("Hora objetivo para manejar", key="hora_manejo")

    dt_manejo = datetime.combine(hoy, hora_manejo)
    if dt_manejo <= ahora:
        dt_manejo += timedelta(days=1)
    horas_hasta = (dt_manejo - ahora).total_seconds() / 3600
    st.caption(f"Faltan **{horas_hasta:.1f} h** para las {dt_manejo.strftime('%H:%M')}.")

    r = factor_widmark(peso, altura, edad, sexo)
    st.markdown("---")
    st.caption(f"Factor Widmark (r): **{r:.3f}**")
    st.caption("Tasa eliminación: **0.15 g/L/hora**")

    # Guardar rápido desde sidebar
    st.markdown("---")
    if st.button("💾 Guardar ahora", use_container_width=True):
        email_sb = st.session_state.get("email_activo", "")
        if email_valido(email_sb):
            guardar_sesion(email_sb)
            st.success("¡Guardado!")
        else:
            st.warning("Primero ingresa tu email arriba.")

manejo_str = dt_manejo.strftime("%Y-%m-%d %H:%M:%S")

# ─────────────────────────────────────────────
# TABLA DE CONSUMO
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🍹 Registro de Consumo</div>', unsafe_allow_html=True)
st.markdown("Ingresa tragos **ya tomados** y también los que **planeas tomar**. "
            "Los futuros se marcan en azul y se proyectan en el gráfico.")

hc1, hc2, hc3, hc4, hc5 = st.columns([4, 1, 2, 2, 1])
hc1.markdown("<small style='color:#666'>**Trago**</small>", unsafe_allow_html=True)
hc2.markdown("<small style='color:#666'>**Cant.**</small>", unsafe_allow_html=True)
hc3.markdown("<small style='color:#666'>**Hora de consumo**</small>", unsafe_allow_html=True)
hc4.markdown("<small style='color:#666'>**Tipo**</small>", unsafe_allow_html=True)
hc5.markdown("<small style='color:#666'>**✕**</small>", unsafe_allow_html=True)

eventos_consumo = []

for fila in st.session_state.filas:
    fid = fila["id"]
    c1, c2, c3, c4, c5 = st.columns([4, 1, 2, 2, 1])

    with c1:
        idx_t = TRAGOS_LISTA.index(st.session_state[f"trago_{fid}"]) \
            if st.session_state.get(f"trago_{fid}") in TRAGOS_LISTA else 0
        trago_sel = st.selectbox("Trago", TRAGOS_LISTA, index=idx_t,
                                 key=f"trago_{fid}", label_visibility="collapsed")
    with c2:
        cantidad = st.number_input("Cant", min_value=1, max_value=20,
                                   value=int(st.session_state.get(f"cant_{fid}", 1)),
                                   step=1, key=f"cant_{fid}", label_visibility="collapsed")
    with c3:
        hora_def = st.session_state.get(f"hora_{fid}", dtime(20, 0))
        hora_trago = st.time_input("Hora", value=hora_def,
                                   key=f"hora_{fid}", label_visibility="collapsed")
    with c4:
        dt_trago = datetime.combine(hoy, hora_trago)
        if dt_trago > ahora + timedelta(hours=12):
            dt_trago -= timedelta(days=1)
        es_futuro = dt_trago > ahora
        if es_futuro:
            st.markdown("<div style='padding-top:.45rem'><span class='tag-futuro'>🔮 FUTURO</span></div>",
                        unsafe_allow_html=True)
        else:
            st.markdown("<div style='padding-top:.45rem'><span class='tag-pasado'>✅ YA TOMADO</span></div>",
                        unsafe_allow_html=True)
    with c5:
        if len(st.session_state.filas) > 1:
            if st.button("✕", key=f"del_{fid}"):
                eliminar_fila(fid)
                st.rerun()

    t_info = TRAGOS[trago_sel]
    g_unit = gramos_etanol(t_info["ml"], t_info["grad"])
    color  = "#5dade2" if es_futuro else "#777"
    st.markdown(
        f"<small style='color:{color};margin-left:4px'>"
        f"{t_info['ml']}ml · {t_info['grad']}° · {g_unit:.1f}g c/u · "
        f"<b>{g_unit*cantidad:.1f}g total</b></small>",
        unsafe_allow_html=True
    )
    eventos_consumo.append({
        "nombre": trago_sel, "cantidad": cantidad,
        "dt": dt_trago, "gramos": g_unit * cantidad, "es_futuro": es_futuro,
    })

st.markdown("<br>", unsafe_allow_html=True)
ca, cb = st.columns([1, 3])
with ca:
    st.button("➕ Agregar trago", on_click=agregar_fila, use_container_width=True)
with cb:
    st.button("🔍 CALCULAR", use_container_width=True, type="primary")

# ─────────────────────────────────────────────
# CÁLCULOS
# ─────────────────────────────────────────────
gramos_total  = sum(ev["gramos"] for ev in eventos_consumo)
gramos_pasado = sum(ev["gramos"] for ev in eventos_consumo if not ev["es_futuro"])
gramos_futuro = sum(ev["gramos"] for ev in eventos_consumo if ev["es_futuro"])

bac_ahora      = bac_en_momento(eventos_consumo, factor_comida, peso, r, ahora)
bac_al_manejar = bac_en_momento(eventos_consumo, factor_comida, peso, r, dt_manejo)
dt_ok          = hora_ok_manejar(eventos_consumo, factor_comida, peso, r, ahora)

# ─────────────────────────────────────────────
# RESULTADOS
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">📊 Resultados</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("---")
    st.markdown("### 🧮 Resumen")
    st.caption(f"Etanol consumido: **{gramos_pasado:.1f} g**")
    if gramos_futuro > 0:
        st.caption(f"Etanol planificado: **{gramos_futuro:.1f} g**")
    st.caption(f"BAC ahora: **{bac_ahora:.3f} g/L**")
    st.caption(f"BAC a las {dt_manejo.strftime('%H:%M')}: **{bac_al_manejar:.3f} g/L**")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("🩸 BAC Ahora (g/L)", f"{bac_ahora:.3f}",
              delta=f"Límite: {LIMITE_CONDUCIR} g/L",
              delta_color="inverse" if bac_ahora > LIMITE_CONDUCIR else "normal")
with m2:
    st.metric(f"🚗 BAC a las {dt_manejo.strftime('%H:%M')}",
              f"{bac_al_manejar:.3f} g/L",
              delta="✅ Apto" if bac_al_manejar < LIMITE_CONDUCIR else "🚫 No apto",
              delta_color="normal" if bac_al_manejar < LIMITE_CONDUCIR else "inverse")
with m3:
    st.metric("🍸 Etanol consumido", f"{gramos_pasado:.1f} g")
with m4:
    if gramos_futuro > 0:
        st.metric("🔮 Etanol planificado", f"{gramos_futuro:.1f} g")
    else:
        st.metric("🍹 Tragos registrados", f"{len(eventos_consumo)}")

st.markdown("<br>", unsafe_allow_html=True)

# Estado ahora
if bac_ahora < LIMITE_CONDUCIR:
    cls = "status-safe"
    msg = f"✅ BAC {bac_ahora:.3f} g/L — {'Sin alcohol.' if bac_ahora==0 else 'Bajo el límite. Apto para conducir.'}"
elif bac_ahora < LIMITE_EBRIEDAD:
    cls = "status-warning"
    msg = f"⚠️ BAC {bac_ahora:.3f} g/L — INFRACCIÓN GRAVE (0.30–0.50 g/L). Prohibido conducir ahora."
else:
    cls = "status-danger"
    msg = f"🚫 BAC {bac_ahora:.3f} g/L — ESTADO DE EBRIEDAD. DELITO conducir."
st.markdown(f'<div class="{cls}">{msg}</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Estado al manejar
if bac_al_manejar < LIMITE_CONDUCIR:
    st.markdown(
        f'<div class="status-safe">🚗 A las {dt_manejo.strftime("%H:%M")} tu BAC será ~{bac_al_manejar:.3f} g/L — ✅ Podrás manejar.</div>',
        unsafe_allow_html=True)
else:
    ok_txt = f"Podrás manejar a las {dt_ok.strftime('%H:%M')}." if dt_ok else "No podrás manejar en las próximas 24h."
    cls2 = "status-warning" if bac_al_manejar < LIMITE_EBRIEDAD else "status-danger"
    st.markdown(
        f'<div class="{cls2}">🚗 A las {dt_manejo.strftime("%H:%M")} tu BAC será ~{bac_al_manejar:.3f} g/L — '
        f'No podrás manejar a esa hora. {ok_txt}</div>',
        unsafe_allow_html=True)

# ─────────────────────────────────────────────
# GRÁFICO
# ─────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">📈 Curva de BAC en el Tiempo</div>', unsafe_allow_html=True)

df = curva_bac(eventos_consumo, factor_comida, peso, r, ventana_h=16)

if not df.empty and gramos_total > 0:
    y_max = max(df["bac"].max() * 1.25, LIMITE_EBRIEDAD + 0.15)

    df_p = df[df["dt"] <= ahora]
    df_f = df[df["dt"] >= ahora]

    fig = go.Figure()

    # Zonas de color
    fig.add_hrect(y0=LIMITE_EBRIEDAD, y1=y_max, fillcolor="rgba(231,76,60,.13)", line_width=0)
    fig.add_hrect(y0=LIMITE_CONDUCIR, y1=LIMITE_EBRIEDAD, fillcolor="rgba(243,156,18,.10)", line_width=0)
    fig.add_hrect(y0=0, y1=LIMITE_CONDUCIR, fillcolor="rgba(39,174,96,.06)", line_width=0)

    # Líneas límite horizontales (via shape, sin anotaciones que rompen)
    for y_val, color_h in [(LIMITE_CONDUCIR, "#f39c12"), (LIMITE_EBRIEDAD, "#e74c3c")]:
        fig.add_shape(type="line", x0=0, x1=1, xref="paper",
                      y0=y_val, y1=y_val,
                      line=dict(color=color_h, width=1.5, dash="dash"))

    # Etiquetas de límites como anotaciones de layout (sin add_hline)
    fig.add_annotation(x=1, xref="paper", y=LIMITE_CONDUCIR,
                       text="0.30 g/L — Límite manejar",
                       showarrow=False, xanchor="right", yanchor="bottom",
                       font=dict(color="#f39c12", size=10))
    fig.add_annotation(x=1, xref="paper", y=LIMITE_EBRIEDAD,
                       text="0.50 g/L — Ebriedad",
                       showarrow=False, xanchor="right", yanchor="bottom",
                       font=dict(color="#e74c3c", size=10))

    # Curvas BAC
    if not df_p.empty:
        fig.add_trace(go.Scatter(x=df_p["t"], y=df_p["bac"], mode="lines",
            name="BAC consumido", line=dict(color="#C0392B", width=3),
            fill="tozeroy", fillcolor="rgba(192,57,43,.12)"))
    if not df_f.empty:
        fig.add_trace(go.Scatter(x=df_f["t"], y=df_f["bac"], mode="lines",
            name="BAC proyectado", line=dict(color="#3498db", width=2.5, dash="dot"),
            fill="tozeroy", fillcolor="rgba(52,152,219,.08)"))

    # Línea vertical "Ahora" como Scatter
    fig.add_trace(go.Scatter(x=[ahora_str, ahora_str], y=[0, y_max],
        mode="lines", line=dict(color="rgba(255,255,255,.35)", width=1.5),
        showlegend=False, hoverinfo="skip"))
    fig.add_annotation(x=ahora_str, y=y_max*0.97, text="Ahora",
                       showarrow=False, font=dict(color="white", size=11), xanchor="left")

    # Punto ahora
    fig.add_trace(go.Scatter(x=[ahora_str], y=[bac_ahora], mode="markers",
        name=f"Ahora ({bac_ahora:.3f} g/L)",
        marker=dict(color="#f1c40f", size=13, symbol="diamond",
                    line=dict(color="white", width=2))))

    # Línea vertical "Hora de manejo"
    fig.add_trace(go.Scatter(x=[manejo_str, manejo_str], y=[0, y_max],
        mode="lines", line=dict(color="rgba(52,152,219,.55)", width=1.5, dash="dash"),
        showlegend=False, hoverinfo="skip"))
    fig.add_annotation(x=manejo_str, y=y_max*0.88,
                       text=f"🚗 {dt_manejo.strftime('%H:%M')}",
                       showarrow=False, font=dict(color="#3498db", size=11), xanchor="left")

    # Punto hora de manejo
    color_m = "#27ae60" if bac_al_manejar < LIMITE_CONDUCIR else "#e74c3c"
    fig.add_trace(go.Scatter(x=[manejo_str], y=[bac_al_manejar], mode="markers",
        name=f"Al manejar ({bac_al_manejar:.3f} g/L)",
        marker=dict(color=color_m, size=13, symbol="star",
                    line=dict(color="white", width=2))))

    # Punto OK para manejar
    if dt_ok and dt_ok > ahora:
        ok_str = dt_ok.strftime("%Y-%m-%d %H:%M:%S")
        fig.add_trace(go.Scatter(x=[ok_str], y=[LIMITE_CONDUCIR], mode="markers+text",
            name=f"OK manejar {dt_ok.strftime('%H:%M')}",
            marker=dict(color="#27ae60", size=11, symbol="triangle-up",
                        line=dict(color="white", width=2)),
            text=[f"  ✅ {dt_ok.strftime('%H:%M')}"], textposition="top right",
            textfont=dict(color="#27ae60", size=11)))

    # Marcas de tragos
    for ev in eventos_consumo:
        ev_str = ev["dt"].strftime("%Y-%m-%d %H:%M:%S")
        col_ev = "rgba(52,152,219,.2)" if ev["es_futuro"] else "rgba(192,57,43,.2)"
        fig.add_trace(go.Scatter(x=[ev_str, ev_str], y=[0, y_max],
            mode="lines", line=dict(color=col_ev, width=1, dash="dot"),
            showlegend=False, hoverinfo="skip"))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15,15,30,.97)", plot_bgcolor="rgba(15,15,30,.97)",
        title=dict(text="Evolución del BAC · azul punteado = proyección futura",
                   font=dict(family="Raleway", size=14, color="white")),
        xaxis=dict(tickformat="%H:%M", gridcolor="rgba(255,255,255,.05)",
                   color="white", title="Hora (Santiago)"),
        yaxis=dict(gridcolor="rgba(255,255,255,.05)", color="white",
                   title="BAC (g/L)", ticksuffix=" g/L", range=[0, y_max]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, font=dict(color="white")),
        hovermode="x unified", height=440,
        margin=dict(t=70, b=40, l=60, r=30)
    )
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# INFO LEGAL + DISCLAIMER
# ─────────────────────────────────────────────
with st.expander("⚖️ Marco Legal Chileno — Ley 18.290 Art. 196"):
    st.markdown("""
| BAC (g/L) | Situación Legal |
|---|---|
| < 0.30 | ✅ Legal, sin sanción |
| 0.30 – < 0.50 | ⚠️ **Infracción grave**: multa + suspensión licencia 1 año |
| ≥ 0.50 | 🚫 **Estado de ebriedad**: delito, hasta 5 años cárcel, cancelación definitiva |

> Chile mide en **g/L**. Eliminación promedio: **0.15 g/L/hora**.
    """)

st.markdown("""
<div class="disclaimer">
⚠️ <b>AVISO:</b> Estimaciones basadas en el modelo de Widmark. El BAC real varía según metabolismo,
medicamentos e hidratación. <b>Ante cualquier duda, no manejes.</b>
Esta herramienta no reemplaza un alcoholímetro certificado.
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center;color:#444;font-size:.72rem'>
Calculadora BAC Chile · Modelo de Widmark · Solo uso informativo · 🇨🇱 America/Santiago<br>
<b>¿Tomaste? No manejes. 🚗❌🍺</b>
</div>
""", unsafe_allow_html=True)
