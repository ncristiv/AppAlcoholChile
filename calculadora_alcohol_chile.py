"""
Calculadora BAC Chile
- Sesiones por nombre de usuario (sin email)
- Límite seguro 0.05 g/L además del legal 0.30 g/L
- Tipo pasado/futuro manual por fila
- Tragos con vodka, fernet, y versión "fuerte" en combinados
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, time as dtime
from zoneinfo import ZoneInfo
import json, os

TZ = ZoneInfo("America/Santiago")
DB = "sesiones_bac.json"

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
    padding:.9rem 1.4rem;border-radius:8px;color:#2ecc71;font-family:'Raleway',sans-serif;font-weight:700;}
.status-ok{background:linear-gradient(135deg,#0a2e1a,#061a0f);border-left:4px solid #1abc9c;
    padding:.9rem 1.4rem;border-radius:8px;color:#1abc9c;font-family:'Raleway',sans-serif;font-weight:700;}
.status-warning{background:linear-gradient(135deg,#3d1c00,#1a0a00);border-left:4px solid #f39c12;
    padding:.9rem 1.4rem;border-radius:8px;color:#f39c12;font-family:'Raleway',sans-serif;font-weight:700;}
.status-danger{background:linear-gradient(135deg,#2c0000,#1a0000);border-left:4px solid #e74c3c;
    padding:.9rem 1.4rem;border-radius:8px;color:#e74c3c;font-family:'Raleway',sans-serif;font-weight:700;}
.disclaimer{background:rgba(231,76,60,.1);border:1px solid rgba(231,76,60,.3);
    border-radius:8px;padding:1rem;font-size:.8rem;color:#e74c3c;margin-top:1rem;}
div[data-testid="stSidebar"]{background:linear-gradient(180deg,#1a0a00,#0d0d0d);
    border-right:1px solid rgba(192,57,43,.2);}
.tag-pasado{background:rgba(192,57,43,.15);color:#e74c3c;border-radius:4px;padding:1px 7px;font-size:.72rem;font-weight:700;}
.tag-futuro{background:rgba(52,152,219,.15);color:#3498db;border-radius:4px;padding:1px 7px;font-size:.72rem;font-weight:700;}
.session-card{background:rgba(39,174,96,.07);border:1px solid rgba(39,174,96,.2);
    border-radius:10px;padding:.9rem 1.2rem;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PERSISTENCIA
# ─────────────────────────────────────────────
def cargar_db():
    if os.path.exists(DB):
        try:
            return json.loads(open(DB, encoding="utf-8").read())
        except Exception:
            return {}
    return {}

def guardar_db(data):
    open(DB, "w", encoding="utf-8").write(json.dumps(data, indent=2, default=str))

def guardar_sesion(usuario: str):
    db = cargar_db()
    filas_serial = []
    for f in st.session_state.get("filas", []):
        fid = f["id"]
        hora_val = st.session_state.get(f"hora_{fid}", dtime(20, 0))
        filas_serial.append({
            "id":      fid,
            "trago":   st.session_state.get(f"trago_{fid}", TRAGOS_LISTA[0]),
            "cant":    int(st.session_state.get(f"cant_{fid}", 1)),
            "hora":    hora_val.strftime("%H:%M") if hasattr(hora_val,"strftime") else str(hora_val)[:5],
            "es_futuro": bool(st.session_state.get(f"futuro_{fid}", False)),
        })
    hora_m = st.session_state.get("hora_manejo", dtime(23, 0))
    db[usuario.strip().lower()] = {
        "nombre":      usuario.strip(),
        "sexo":        st.session_state.get("sexo_val",   "Masculino"),
        "peso":        st.session_state.get("peso_val",   75.0),
        "altura":      st.session_state.get("altura_val", 170.0),
        "edad":        st.session_state.get("edad_val",   30),
        "comida":      st.session_state.get("comida_val", COMIDA_LISTA[2]),
        "hora_manejo": hora_m.strftime("%H:%M") if hasattr(hora_m,"strftime") else str(hora_m)[:5],
        "filas":       filas_serial,
        "next_id":     st.session_state.get("next_id", 1),
        "guardado_en": datetime.now(TZ).strftime("%Y-%m-%d %H:%M"),
    }
    guardar_db(db)

def cargar_sesion(usuario: str) -> bool:
    db = cargar_db()
    data = db.get(usuario.strip().lower())
    if not data:
        return False
    st.session_state["sexo_val"]   = data.get("sexo",   "Masculino")
    st.session_state["peso_val"]   = float(data.get("peso",   75.0))
    st.session_state["altura_val"] = float(data.get("altura", 170.0))
    st.session_state["edad_val"]   = int(data.get("edad", 30))
    st.session_state["comida_val"] = data.get("comida", COMIDA_LISTA[2]) \
        if data.get("comida", COMIDA_LISTA[2]) in COMIDA_LISTA else COMIDA_LISTA[2]
    filas_raw = data.get("filas", [])
    if filas_raw:
        st.session_state["filas"]   = [{"id": f["id"]} for f in filas_raw]
        st.session_state["next_id"] = int(data.get("next_id", max(f["id"] for f in filas_raw)+1))
        for f in filas_raw:
            fid = f["id"]
            trago = f.get("trago", TRAGOS_LISTA[0])
            if trago not in TRAGOS_LISTA:
                trago = TRAGOS_LISTA[0]
            st.session_state[f"trago_{fid}"]  = trago
            st.session_state[f"cant_{fid}"]   = int(f.get("cant", 1))
            st.session_state[f"futuro_{fid}"] = bool(f.get("es_futuro", False))
            try:
                h, m = str(f.get("hora","20:00"))[:5].split(":")
                st.session_state[f"hora_{fid}"] = dtime(int(h), int(m))
            except Exception:
                st.session_state[f"hora_{fid}"] = dtime(20, 0)
    try:
        h, m = data.get("hora_manejo","23:00")[:5].split(":")
        st.session_state["hora_manejo"] = dtime(int(h), int(m))
    except Exception:
        st.session_state["hora_manejo"] = dtime(23, 0)
    return True

# ─────────────────────────────────────────────
# TRAGOS
# ─────────────────────────────────────────────
TRAGOS = {
    # Cervezas
    "🍺 Cerveza latita (355ml, 5°)":              {"ml": 355, "grad": 5.0},
    "🍺 Cerveza botella (330ml, 5°)":             {"ml": 330, "grad": 5.0},
    "🍺 Schop (500ml, 5°)":                       {"ml": 500, "grad": 5.0},
    # Pisco
    "🍹 Pisco Sour (120ml, 14°)":                 {"ml": 120, "grad": 14.0},
    "🥃 Pisco con Coca-Cola (250ml, 10°)":        {"ml": 250, "grad": 10.0},
    "🥃 Pisco con Coca-Cola fuerte (250ml, 16°)": {"ml": 250, "grad": 16.0},
    "🍹 Chilcano (250ml, 10°)":                   {"ml": 250, "grad": 10.0},
    "🍹 Chilcano fuerte (250ml, 16°)":            {"ml": 250, "grad": 16.0},
    # Whisky
    "🥃 Whisky en las rocas (90ml, 40°)":         {"ml":  90, "grad": 40.0},
    "🥃 Whisky con soda (250ml, 14°)":            {"ml": 250, "grad": 14.0},
    "🥃 Whisky con soda fuerte (250ml, 20°)":     {"ml": 250, "grad": 20.0},
    # Vodka
    "🧊 Vodka shot (45ml, 40°)":                  {"ml":  45, "grad": 40.0},
    "🧊 Vodka con jugo (250ml, 10°)":             {"ml": 250, "grad": 10.0},
    "🧊 Vodka con jugo fuerte (250ml, 16°)":      {"ml": 250, "grad": 16.0},
    "🧊 Vodka tónica (250ml, 10°)":               {"ml": 250, "grad": 10.0},
    "🧊 Vodka tónica fuerte (250ml, 16°)":        {"ml": 250, "grad": 16.0},
    # Fernet
    "🌿 Fernet con Coca-Cola (250ml, 12°)":       {"ml": 250, "grad": 12.0},
    "🌿 Fernet con Coca-Cola fuerte (250ml, 20°)":{"ml": 250, "grad": 20.0},
    "🌿 Fernet shot (45ml, 39°)":                 {"ml":  45, "grad": 39.0},
    # Mojito / Ron
    "🍸 Mojito Cubano (300ml, 8.5°)":             {"ml": 300, "grad":  8.5},
    "🍸 Mojito Cubano fuerte (300ml, 14°)":       {"ml": 300, "grad": 14.0},
    # Tequila
    "🥂 Tequila shot (45ml, 38°)":               {"ml":  45, "grad": 38.0},
    "🍹 Margarita (150ml, 16°)":                  {"ml": 150, "grad": 16.0},
    # Vino / Espumante
    "🍷 Vino tinto (150ml, 13°)":                 {"ml": 150, "grad": 13.0},
    "🥂 Espumante / Champaña (150ml, 11°)":       {"ml": 150, "grad": 11.5},
    # Aperol
    "🍸 Aperol Spritz (200ml, 8°)":               {"ml": 200, "grad":  8.0},
}
TRAGOS_LISTA = list(TRAGOS.keys())

COMIDA_LISTA = [
    "🚫 Nada (estómago vacío)",
    "🥗 Snacks livianos (maní, crudités)",
    "🥘 Entradas / finger food (cóctel)",
    "🍖 Cena completa (entrada + fondo)",
    "🍽️ Cena abundante + pan + postre",
]
COMIDA_FACTOR = dict(zip(COMIDA_LISTA, [1.0, 0.85, 0.70, 0.55, 0.45]))

LIMITE_SEGURO   = 0.05   # nuevo límite conservador
LIMITE_CONDUCIR = 0.30   # infracción grave
LIMITE_EBRIEDAD = 0.50   # delito

# ─────────────────────────────────────────────
# FUNCIONES BAC
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
    t_abs    = 0.5 + 0.5*(1.0 - fc)
    bac_pico = (gramos * fc) / (r * peso_kg)
    return max(0.0, bac_pico - 0.15 * max(0.0, horas - t_abs))

def bac_en_momento(eventos, fc, peso_kg, r, dt_c):
    total = 0.0
    for ev in eventos:
        if ev["dt"] <= dt_c:
            h = (dt_c - ev["dt"]).total_seconds() / 3600.0
            total += bac_de_evento(ev["gramos"], fc, peso_kg, r, h)
    return round(total, 3)

def hora_ok(eventos, fc, peso_kg, r, desde, limite):
    dt = desde
    for _ in range(24*60):
        if bac_en_momento(eventos, fc, peso_kg, r, dt) < limite:
            return dt
        dt += timedelta(minutes=1)
    return None

def curva_bac(eventos, fc, peso_kg, r, ventana_h=16):
    if not eventos:
        return pd.DataFrame()
    dt_inicio = min(ev["dt"] for ev in eventos)
    dt_fin    = max(ev["dt"] for ev in eventos) + timedelta(hours=ventana_h)
    filas, dt = [], dt_inicio
    while dt <= dt_fin:
        filas.append({"t": dt.strftime("%Y-%m-%d %H:%M:%S"),
                      "bac": bac_en_momento(eventos, fc, peso_kg, r, dt),
                      "dt": dt})
        dt += timedelta(minutes=10)
    return pd.DataFrame(filas)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in [("filas",[{"id":0}]),("next_id",1),
             ("usuario_activo",""),("sesion_cargada",False)]:
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
# PANEL SESIÓN
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">👤 Tu Sesión</div>', unsafe_allow_html=True)

cs1, cs2, cs3, cs4 = st.columns([3, 1, 1, 3])
with cs1:
    usuario_input = st.text_input(
        "Nombre de usuario (puede ser tu nombre, apodo, etc.)",
        placeholder="Ej: juanito, pedro_99, La Rochi...",
        value=st.session_state.get("usuario_activo", ""),
    )
with cs2:
    st.markdown("<div style='padding-top:1.8rem'>", unsafe_allow_html=True)
    if st.button("📂 Cargar", use_container_width=True):
        if usuario_input.strip():
            ok = cargar_sesion(usuario_input)
            if ok:
                st.session_state["usuario_activo"] = usuario_input.strip().lower()
                st.rerun()
            else:
                st.session_state["usuario_activo"] = usuario_input.strip().lower()
                st.warning("No hay sesión guardada para ese usuario.")
        else:
            st.error("Ingresa un nombre de usuario.")
    st.markdown("</div>", unsafe_allow_html=True)
with cs3:
    st.markdown("<div style='padding-top:1.8rem'>", unsafe_allow_html=True)
    if st.button("💾 Guardar", use_container_width=True, type="primary"):
        if usuario_input.strip():
            st.session_state["usuario_activo"] = usuario_input.strip().lower()
            guardar_sesion(usuario_input)
            st.success(f"✅ Guardado como **{usuario_input.strip().lower()}**")
        else:
            st.error("Ingresa un nombre de usuario.")
    st.markdown("</div>", unsafe_allow_html=True)
with cs4:
    if st.session_state.get("usuario_activo"):
        db_c = cargar_db()
        dat  = db_c.get(st.session_state["usuario_activo"])
        if dat:
            st.markdown(
                f"<div class='session-card' style='margin-top:.5rem'>"
                f"✅ Usuario: <b>{dat.get('nombre', st.session_state['usuario_activo'])}</b><br>"
                f"<small style='color:#888'>Último guardado: {dat.get('guardado_en','—')}</small>"
                f"</div>", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 👤 Datos Personales")
    sexo = st.radio("Sexo biológico", ["Masculino","Femenino"],
                    index=0 if st.session_state.get("sexo_val","Masculino")=="Masculino" else 1,
                    key="sexo_val")
    peso   = st.number_input("Peso (kg)",   40.0, 200.0,
                             value=st.session_state.get("peso_val",   75.0), step=0.5, key="peso_val")
    altura = st.number_input("Altura (cm)", 140.0, 220.0,
                             value=st.session_state.get("altura_val", 170.0), step=1.0, key="altura_val")
    edad   = st.number_input("Edad (años)", 18, 90,
                             value=st.session_state.get("edad_val",   30), step=1, key="edad_val")

    st.markdown("---")
    st.markdown("## 🍽️ Comida consumida")
    c_idx  = COMIDA_LISTA.index(st.session_state["comida_val"]) \
             if st.session_state.get("comida_val") in COMIDA_LISTA else 2
    comida = st.selectbox("¿Qué has comido?", COMIDA_LISTA, index=c_idx, key="comida_val")
    factor_comida = COMIDA_FACTOR[comida]

    st.markdown("---")
    st.markdown("## ⏰ Hora actual")
    st.info(f"🕐 **{ahora.strftime('%H:%M')}** hrs\n\n📍 Santiago de Chile")

    st.markdown("---")
    st.markdown("## 🚗 ¿A qué hora quieres manejar?")
    if "hora_manejo" not in st.session_state:
        st.session_state["hora_manejo"] = dtime(min(ahora.hour+3, 23), 0)
    hora_manejo  = st.time_input("Hora objetivo", key="hora_manejo")
    dt_manejo    = datetime.combine(hoy, hora_manejo)
    if dt_manejo <= ahora:
        dt_manejo += timedelta(days=1)
    horas_hasta = (dt_manejo - ahora).total_seconds() / 3600
    st.caption(f"Faltan **{horas_hasta:.1f} h** para las {dt_manejo.strftime('%H:%M')}.")
    manejo_str = dt_manejo.strftime("%Y-%m-%d %H:%M:%S")

    r = factor_widmark(peso, altura, edad, sexo)
    st.markdown("---")
    st.caption(f"Factor Widmark (r): **{r:.3f}**")
    st.caption("Tasa eliminación: **0.15 g/L/hora**")

    st.markdown("---")
    if st.button("💾 Guardar ahora", use_container_width=True):
        u = st.session_state.get("usuario_activo","")
        if u:
            guardar_sesion(u)
            st.success("¡Guardado!")
        else:
            st.warning("Ingresa un nombre de usuario arriba.")

# ─────────────────────────────────────────────
# TABLA DE CONSUMO
# ─────────────────────────────────────────────
st.markdown('<div class="section-header">🍹 Registro de Consumo</div>', unsafe_allow_html=True)
st.markdown("Ingresa cada trago con su hora. Elige manualmente si fue **Pasado** o **Futuro** "
            "(útil cuando el evento cruza la medianoche).")

# Encabezados
h1,h2,h3,h4,h5 = st.columns([4,1,2,2,1])
h1.markdown("<small style='color:#666'>**Trago**</small>", unsafe_allow_html=True)
h2.markdown("<small style='color:#666'>**Cant.**</small>", unsafe_allow_html=True)
h3.markdown("<small style='color:#666'>**Hora de consumo**</small>", unsafe_allow_html=True)
h4.markdown("<small style='color:#666'>**¿Pasado o Futuro?**</small>", unsafe_allow_html=True)
h5.markdown("<small style='color:#666'>**✕**</small>", unsafe_allow_html=True)

eventos_consumo = []

for fila in st.session_state.filas:
    fid = fila["id"]
    c1,c2,c3,c4,c5 = st.columns([4,1,2,2,1])

    with c1:
        idx_t = TRAGOS_LISTA.index(st.session_state[f"trago_{fid}"]) \
                if st.session_state.get(f"trago_{fid}") in TRAGOS_LISTA else 0
        trago_sel = st.selectbox("Trago", TRAGOS_LISTA, index=idx_t,
                                 key=f"trago_{fid}", label_visibility="collapsed")
    with c2:
        cantidad = st.number_input("Cant", min_value=1, max_value=20,
                                   value=int(st.session_state.get(f"cant_{fid}",1)),
                                   step=1, key=f"cant_{fid}", label_visibility="collapsed")
    with c3:
        hora_def   = st.session_state.get(f"hora_{fid}", dtime(20,0))
        hora_trago = st.time_input("Hora", value=hora_def,
                                   key=f"hora_{fid}", label_visibility="collapsed")
    with c4:
        # Toggle manual pasado/futuro
        default_futuro = bool(st.session_state.get(f"futuro_{fid}", False))
        tipo_sel = st.radio(
            "Tipo", ["✅ Pasado", "🔮 Futuro"],
            index=1 if default_futuro else 0,
            key=f"tipo_{fid}",
            horizontal=True,
            label_visibility="collapsed"
        )
        es_futuro = (tipo_sel == "🔮 Futuro")
        st.session_state[f"futuro_{fid}"] = es_futuro
    with c5:
        if len(st.session_state.filas) > 1:
            if st.button("✕", key=f"del_{fid}"):
                eliminar_fila(fid)
                st.rerun()

    # Construir datetime del trago
    dt_trago = datetime.combine(hoy, hora_trago)
    if es_futuro and dt_trago <= ahora:
        dt_trago += timedelta(days=1)   # futuro que parece pasado → mañana
    elif not es_futuro and dt_trago > ahora:
        dt_trago -= timedelta(days=1)   # pasado que parece futuro → ayer

    t_info = TRAGOS[trago_sel]
    g_unit = gramos_etanol(t_info["ml"], t_info["grad"])
    color  = "#5dade2" if es_futuro else "#888"
    st.markdown(
        f"<small style='color:{color};margin-left:4px'>"
        f"{t_info['ml']}ml · {t_info['grad']}° · {g_unit:.1f}g c/u · "
        f"<b>{g_unit*cantidad:.1f}g total</b></small>",
        unsafe_allow_html=True
    )
    eventos_consumo.append({
        "nombre": trago_sel, "cantidad": cantidad,
        "dt": dt_trago, "gramos": g_unit*cantidad, "es_futuro": es_futuro,
    })

st.markdown("<br>", unsafe_allow_html=True)
ca,cb = st.columns([1,3])
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

dt_ok_seguro   = hora_ok(eventos_consumo, factor_comida, peso, r, ahora, LIMITE_SEGURO)
dt_ok_legal    = hora_ok(eventos_consumo, factor_comida, peso, r, ahora, LIMITE_CONDUCIR)

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

m1,m2,m3,m4 = st.columns(4)
with m1:
    st.metric("🩸 BAC Ahora (g/L)", f"{bac_ahora:.3f}",
              delta=f"Límite legal: {LIMITE_CONDUCIR} g/L",
              delta_color="inverse" if bac_ahora > LIMITE_CONDUCIR else "normal")
with m2:
    st.metric(f"🚗 BAC a las {dt_manejo.strftime('%H:%M')}",
              f"{bac_al_manejar:.3f} g/L",
              delta="✅ Apto" if bac_al_manejar < LIMITE_CONDUCIR else "🚫 No apto",
              delta_color="normal" if bac_al_manejar < LIMITE_CONDUCIR else "inverse")
with m3:
    if dt_ok_legal and dt_ok_legal > ahora:
        st.metric("⚖️ Bajo límite legal (0.30)",
                  dt_ok_legal.strftime("%H:%M"),
                  delta=f"en {(dt_ok_legal-ahora).seconds//3600}h {((dt_ok_legal-ahora).seconds%3600)//60}m")
    else:
        st.metric("⚖️ Bajo límite legal (0.30)", "¡Ya estás!", delta="✅")
with m4:
    if dt_ok_seguro and dt_ok_seguro > ahora:
        st.metric("🟢 Bajo límite seguro (0.05)",
                  dt_ok_seguro.strftime("%H:%M"),
                  delta=f"en {(dt_ok_seguro-ahora).seconds//3600}h {((dt_ok_seguro-ahora).seconds%3600)//60}m")
    else:
        st.metric("🟢 Bajo límite seguro (0.05)", "¡Ya estás!", delta="✅")

st.markdown("<br>", unsafe_allow_html=True)

# Estado actual
if bac_ahora < LIMITE_SEGURO:
    st.markdown(f'<div class="status-safe">✅ BAC {bac_ahora:.3f} g/L — Bajo el límite seguro (0.05 g/L). Apto para conducir con total confianza.</div>', unsafe_allow_html=True)
elif bac_ahora < LIMITE_CONDUCIR:
    ok_s = dt_ok_seguro.strftime("%H:%M") if dt_ok_seguro else "—"
    st.markdown(f'<div class="status-ok">🟡 BAC {bac_ahora:.3f} g/L — Bajo el límite legal, pero sobre 0.05 g/L. Puedes conducir sin infracción. Bajo límite seguro a las {ok_s}.</div>', unsafe_allow_html=True)
elif bac_ahora < LIMITE_EBRIEDAD:
    ok_l = dt_ok_legal.strftime("%H:%M") if dt_ok_legal else "—"
    st.markdown(f'<div class="status-warning">⚠️ BAC {bac_ahora:.3f} g/L — INFRACCIÓN GRAVE (0.30–0.50 g/L). Prohibido conducir. Podrás manejar a las {ok_l}.</div>', unsafe_allow_html=True)
else:
    ok_l = dt_ok_legal.strftime("%H:%M") if dt_ok_legal else "—"
    st.markdown(f'<div class="status-danger">🚫 BAC {bac_ahora:.3f} g/L — ESTADO DE EBRIEDAD. DELITO conducir. Podrás manejar a las {ok_l}.</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Estado al manejar
if bac_al_manejar < LIMITE_SEGURO:
    st.markdown(f'<div class="status-safe">🚗 A las {dt_manejo.strftime("%H:%M")} tu BAC será ~{bac_al_manejar:.3f} g/L — ✅ Bajo el límite seguro. Perfecto para manejar.</div>', unsafe_allow_html=True)
elif bac_al_manejar < LIMITE_CONDUCIR:
    st.markdown(f'<div class="status-ok">🚗 A las {dt_manejo.strftime("%H:%M")} tu BAC será ~{bac_al_manejar:.3f} g/L — 🟡 Sin infracción legal, pero aún sobre 0.05 g/L.</div>', unsafe_allow_html=True)
else:
    ok_txt = f"Podrás manejar legalmente a las {dt_ok_legal.strftime('%H:%M')}." if dt_ok_legal else "No podrás manejar en 24h."
    cls2 = "status-warning" if bac_al_manejar < LIMITE_EBRIEDAD else "status-danger"
    st.markdown(f'<div class="{cls2}">🚗 A las {dt_manejo.strftime("%H:%M")} tu BAC será ~{bac_al_manejar:.3f} g/L — No podrás manejar. {ok_txt}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# GRÁFICO
# ─────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">📈 Curva de BAC en el Tiempo</div>', unsafe_allow_html=True)

df = curva_bac(eventos_consumo, factor_comida, peso, r, ventana_h=16)

if not df.empty and gramos_total > 0:
    y_max = max(df["bac"].max()*1.25, LIMITE_EBRIEDAD+0.15)
    df_p  = df[df["dt"] <= ahora]
    df_f  = df[df["dt"] >= ahora]

    fig = go.Figure()

    # Zonas
    fig.add_hrect(y0=LIMITE_EBRIEDAD, y1=y_max, fillcolor="rgba(231,76,60,.12)", line_width=0)
    fig.add_hrect(y0=LIMITE_CONDUCIR, y1=LIMITE_EBRIEDAD, fillcolor="rgba(243,156,18,.10)", line_width=0)
    fig.add_hrect(y0=LIMITE_SEGURO,   y1=LIMITE_CONDUCIR, fillcolor="rgba(243,196,18,.06)", line_width=0)
    fig.add_hrect(y0=0, y1=LIMITE_SEGURO, fillcolor="rgba(39,174,96,.07)", line_width=0)

    # Líneas horizontales de límites
    for y_val, col_h, lbl in [
        (LIMITE_SEGURO,   "#1abc9c", f"0.05 g/L — Límite seguro"),
        (LIMITE_CONDUCIR, "#f39c12", f"0.30 g/L — Límite legal"),
        (LIMITE_EBRIEDAD, "#e74c3c", f"0.50 g/L — Ebriedad"),
    ]:
        fig.add_shape(type="line", x0=0, x1=1, xref="paper",
                      y0=y_val, y1=y_val,
                      line=dict(color=col_h, width=1.5, dash="dash"))
        fig.add_annotation(x=1, xref="paper", y=y_val, text=lbl,
                           showarrow=False, xanchor="right", yanchor="bottom",
                           font=dict(color=col_h, size=10))

    # Curvas
    if not df_p.empty:
        fig.add_trace(go.Scatter(x=df_p["t"], y=df_p["bac"], mode="lines",
            name="BAC consumido", line=dict(color="#C0392B", width=3),
            fill="tozeroy", fillcolor="rgba(192,57,43,.12)"))
    if not df_f.empty:
        fig.add_trace(go.Scatter(x=df_f["t"], y=df_f["bac"], mode="lines",
            name="BAC proyectado", line=dict(color="#3498db", width=2.5, dash="dot"),
            fill="tozeroy", fillcolor="rgba(52,152,219,.08)"))

    # Línea "Ahora"
    fig.add_trace(go.Scatter(x=[ahora_str,ahora_str], y=[0,y_max], mode="lines",
        line=dict(color="rgba(255,255,255,.35)",width=1.5),
        showlegend=False, hoverinfo="skip"))
    fig.add_annotation(x=ahora_str, y=y_max*0.97, text="Ahora",
                       showarrow=False, font=dict(color="white",size=11), xanchor="left")

    # Punto ahora
    fig.add_trace(go.Scatter(x=[ahora_str], y=[bac_ahora], mode="markers",
        name=f"Ahora ({bac_ahora:.3f} g/L)",
        marker=dict(color="#f1c40f",size=13,symbol="diamond",line=dict(color="white",width=2))))

    # Línea "Hora de manejo"
    fig.add_trace(go.Scatter(x=[manejo_str,manejo_str], y=[0,y_max], mode="lines",
        line=dict(color="rgba(52,152,219,.55)",width=1.5,dash="dash"),
        showlegend=False, hoverinfo="skip"))
    fig.add_annotation(x=manejo_str, y=y_max*0.88,
                       text=f"🚗 {dt_manejo.strftime('%H:%M')}",
                       showarrow=False, font=dict(color="#3498db",size=11), xanchor="left")

    # Punto hora de manejo
    col_m = "#27ae60" if bac_al_manejar < LIMITE_CONDUCIR else "#e74c3c"
    fig.add_trace(go.Scatter(x=[manejo_str], y=[bac_al_manejar], mode="markers",
        name=f"Al manejar ({bac_al_manejar:.3f} g/L)",
        marker=dict(color=col_m,size=13,symbol="star",line=dict(color="white",width=2))))

    # Punto OK legal
    if dt_ok_legal and dt_ok_legal > ahora:
        ok_l_str = dt_ok_legal.strftime("%Y-%m-%d %H:%M:%S")
        fig.add_trace(go.Scatter(x=[ok_l_str], y=[LIMITE_CONDUCIR],
            mode="markers+text", name=f"OK legal {dt_ok_legal.strftime('%H:%M')}",
            marker=dict(color="#f39c12",size=11,symbol="triangle-up",line=dict(color="white",width=2)),
            text=[f"  ⚖️ {dt_ok_legal.strftime('%H:%M')}"], textposition="top right",
            textfont=dict(color="#f39c12",size=10)))

    # Punto OK seguro
    if dt_ok_seguro and dt_ok_seguro > ahora:
        ok_s_str = dt_ok_seguro.strftime("%Y-%m-%d %H:%M:%S")
        fig.add_trace(go.Scatter(x=[ok_s_str], y=[LIMITE_SEGURO],
            mode="markers+text", name=f"OK seguro {dt_ok_seguro.strftime('%H:%M')}",
            marker=dict(color="#1abc9c",size=11,symbol="triangle-up",line=dict(color="white",width=2)),
            text=[f"  🟢 {dt_ok_seguro.strftime('%H:%M')}"], textposition="top right",
            textfont=dict(color="#1abc9c",size=10)))

    # Marcas de tragos
    for ev in eventos_consumo:
        ev_str = ev["dt"].strftime("%Y-%m-%d %H:%M:%S")
        col_ev = "rgba(52,152,219,.2)" if ev["es_futuro"] else "rgba(192,57,43,.2)"
        fig.add_trace(go.Scatter(x=[ev_str,ev_str], y=[0,y_max], mode="lines",
            line=dict(color=col_ev,width=1,dash="dot"),
            showlegend=False, hoverinfo="skip"))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15,15,30,.97)", plot_bgcolor="rgba(15,15,30,.97)",
        title=dict(text="Evolución del BAC · azul punteado = proyección futura",
                   font=dict(family="Raleway",size=14,color="white")),
        xaxis=dict(tickformat="%H:%M", gridcolor="rgba(255,255,255,.05)",
                   color="white", title="Hora (Santiago)"),
        yaxis=dict(gridcolor="rgba(255,255,255,.05)", color="white",
                   title="BAC (g/L)", ticksuffix=" g/L", range=[0,y_max]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, font=dict(color="white")),
        hovermode="x unified", height=460,
        margin=dict(t=70,b=40,l=60,r=30)
    )
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# LEGAL + DISCLAIMER
# ─────────────────────────────────────────────
with st.expander("⚖️ Marco Legal Chileno — Ley 18.290 Art. 196"):
    st.markdown("""
| BAC (g/L) | Situación |
|---|---|
| < 0.05 | 🟢 **Límite seguro** — recomendado por esta app |
| 0.05 – < 0.30 | 🟡 Legal sin infracción, pero con alcohol detectable |
| 0.30 – < 0.50 | ⚠️ **Infracción grave**: multa + suspensión 1 año |
| ≥ 0.50 | 🚫 **Ebriedad**: delito, hasta 5 años cárcel, cancelación definitiva |

> Eliminación promedio: **0.15 g/L/hora** · Modelo de Widmark
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
