import json
import os
from pathlib import Path
import streamlit as st

# ── Configuración ─────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[2]
MODEL_LOG_PATH = Path(os.getenv("MODEL_LOG_PATH", ROOT_DIR / "models" / "model_log.json"))

# Paleta Insight Commerce
COLOR_PRIMARY   = "#FE495F"   # rojo coral
COLOR_SECONDARY = "#FE9D97"   # rosa salmón
COLOR_ACCENT    = "#BDED7E"   # verde lima
COLOR_LIGHT     = "#FFFEC8"   # amarillo crema
COLOR_BG_CARD   = "#1A1F2C"   # fondo card (secundario)

st.set_page_config(
    page_title="Dashboard · Insight Commerce",
    page_icon="📊",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    .kpi-card {{
        background-color: {COLOR_BG_CARD};
        border-left: 4px solid {COLOR_PRIMARY};
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.5rem;
    }}
    .kpi-label {{
        font-size: 0.8rem;
        font-weight: 600;
        color: {COLOR_SECONDARY};
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.2rem;
    }}
    .kpi-value {{
        font-size: 2rem;
        font-weight: 700;
        color: #FAFAFA;
        line-height: 1.1;
    }}
    .kpi-sub {{
        font-size: 0.78rem;
        color: #888;
        margin-top: 0.2rem;
    }}
    .kpi-accent {{
        border-left-color: {COLOR_ACCENT};
    }}
    .kpi-yellow {{
        border-left-color: {COLOR_LIGHT};
    }}
    .section-title {{
        font-size: 1rem;
        font-weight: 700;
        color: {COLOR_PRIMARY};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 1.5rem 0 0.8rem 0;
    }}
    .feature-bar-label {{
        font-size: 0.85rem;
        color: #FAFAFA;
        margin-bottom: 0.15rem;
    }}
    .coverage-badge {{
        display: inline-block;
        background-color: {COLOR_ACCENT};
        color: #1A1A1A;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 3px 12px;
        border-radius: 20px;
        margin-left: 0.5rem;
    }}
</style>
""", unsafe_allow_html=True)

# ── Carga de datos ────────────────────────────────────────────────────────────
@st.cache_data
def load_model_log() -> dict:
    with open(MODEL_LOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

try:
    log = load_model_log()
except FileNotFoundError:
    st.error(
        f"No se encontró model_log.json en {MODEL_LOG_PATH}. "
        "Verificá que los artefactos del modelo estén en la carpeta models/."
    )
    st.stop()

metrics   = log.get("metrics_test", {})
split     = log.get("split", {})
top10     = log.get("importance_top10", [])
zero_feat = log.get("features_zero_importance", [])
n_features = log.get("n_features", 0)
model_ts  = log.get("timestamp", "—")[:10]

# Métricas clave
precision = metrics.get("precision", 0)
recall    = metrics.get("recall", 0)
f1        = metrics.get("f1", 0)
auc       = metrics.get("auc", 0)

# Derivados de negocio
auc_lift_pct   = round((auc - 0.5) / 0.5 * 100)   # % mejor que azar
precision_pct  = round(precision * 100, 1)
n_test_users   = split.get("n_test_users", 0)
n_train_users  = split.get("n_train_users", 0)
n_val_users    = split.get("n_val_users", 0)
total_users    = n_train_users + n_val_users + n_test_users
active_features = n_features - len(zero_feat)

# Nombres legibles de features para el PO
FEATURE_LABELS = {
    "up_reorder_rate":           "Tasa de recompra del producto por el usuario",
    "up_days_since_last":        "Días desde la última compra del producto",
    "product_reorder_rate":      "Popularidad global del producto",
    "user_reorder_ratio":        "Frecuencia de recompra del usuario",
    "up_delta_days":             "Variación en el intervalo de compra",
    "p_aisle_reorder_rate":      "Popularidad del pasillo del producto",
    "up_first_order_number":     "Antigüedad del producto en el historial",
    "u_favorite_aisle":          "Pasillo favorito del usuario",
    "user_days_since_last_order": "Días desde la última visita del usuario",
    "up_times_purchased":        "Cantidad de veces que el usuario compró el producto",
}

# ── Título ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<h1 style='color:{COLOR_PRIMARY}; margin-bottom:0;'>📊 Dashboard de Impacto</h1>
<p style='color:#888; margin-top:0.2rem;'>
    Insight Commerce · Modelo entrenado el {model_ts}
    <span class="coverage-badge">100% cobertura de usuarios</span>
</p>
""", unsafe_allow_html=True)

st.divider()

# ── KPIs principales ──────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Rendimiento del modelo</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Precisión Top-10</div>
        <div class="kpi-value">{precision_pct}%</div>
        <div class="kpi-sub">De cada 10 productos que el sistema sugiere, más de 4 son productos que el usuario efectivamente compraría.</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card kpi-accent">
        <div class="kpi-label">Poder de discriminación</div>
        <div class="kpi-value">{round(auc * 100, 1)}%</div>
        <div class="kpi-sub">AUC-ROC · El modelo acierta en 8 de cada 10 comparaciones entre productos</div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Cobertura de recall</div>
        <div class="kpi-value">{round(recall * 100, 1)}%</div>
        <div class="kpi-sub">El sistema encuentra el 41% de todos los productos que el usuario compraría. Lo que no aparece en el top-10 queda fuera por límite de espacio, no por error del modelo.</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card kpi-yellow">
        <div class="kpi-label">Usuarios evaluados</div>
        <div class="kpi-value">{n_test_users:,}</div>
        <div class="kpi-sub">El modelo fue probado sobre 1.498 usuarios reales que nunca vio durante el entrenamiento, garantizando que los resultados son representativos.</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Cobertura del sistema ─────────────────────────────────────────────────────
st.markdown('<div class="section-title">Cobertura del sistema</div>', unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown(f"""
    <div class="kpi-card kpi-accent">
        <div class="kpi-label">Modelo LightGBM</div>
        <div class="kpi-value">{total_users:,}</div>
        <div class="kpi-sub">Usuarios con ≥ 5 órdenes<br>Recomendación personalizada completa</div>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Cold-start personal</div>
        <div class="kpi-value">1 – 4</div>
        <div class="kpi-sub">Órdenes previas<br>Recomendación por historial propio</div>
    </div>
    """, unsafe_allow_html=True)

with col_c:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Usuario nuevo</div>
        <div class="kpi-value">0</div>
        <div class="kpi-sub">Órdenes previas<br>Recomendación por popularidad global</div>
    </div>
    """, unsafe_allow_html=True)

st.caption("El sistema nunca devuelve un error por falta de historial — todo usuario recibe recomendaciones.")

st.divider()

# ── Top 10 señales del modelo ─────────────────────────────────────────────────
st.markdown('<div class="section-title">¿Qué señales usa el modelo para recomendar?</div>', unsafe_allow_html=True)
st.caption("Las 10 variables con mayor impacto en las predicciones, en lenguaje de negocio.")

max_importance = max(item["importance"] for item in top10) if top10 else 1

for item in top10:
    feature     = item["feature"]
    importance  = item["importance"]
    label       = FEATURE_LABELS.get(feature, feature)
    bar_pct     = importance / max_importance
    bar_color   = COLOR_ACCENT if importance == max_importance else COLOR_SECONDARY

    col_label, col_bar = st.columns([4, 6])
    with col_label:
        st.markdown(
            f'<div class="feature-bar-label">🔹 {label}</div>',
            unsafe_allow_html=True
        )
    with col_bar:
        st.progress(bar_pct)

st.divider()

# ── Dataset ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Dataset de entrenamiento</div>', unsafe_allow_html=True)

col_d1, col_d2, col_d3, col_d4 = st.columns(4)

with col_d1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Usuarios de entrenamiento</div>
        <div class="kpi-value">{n_train_users:,}</div>
        <div class="kpi-sub">70% del total</div>
    </div>
    """, unsafe_allow_html=True)

with col_d2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Usuarios de validación</div>
        <div class="kpi-value">{n_val_users:,}</div>
        <div class="kpi-sub">15% del total</div>
    </div>
    """, unsafe_allow_html=True)

with col_d3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Usuarios de test</div>
        <div class="kpi-value">{n_test_users:,}</div>
        <div class="kpi-sub">15% del total — evaluación final</div>
    </div>
    """, unsafe_allow_html=True)

with col_d4:
    st.markdown(f"""
    <div class="kpi-card kpi-accent">
        <div class="kpi-label">Features activas</div>
        <div class="kpi-value">{active_features} / {n_features}</div>
        <div class="kpi-sub">{len(zero_feat)} con importancia cero<br>descartadas automáticamente</div>
    </div>
    """, unsafe_allow_html=True)