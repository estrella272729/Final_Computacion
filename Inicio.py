import pandas as pd
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AirLab EAFIT — Monitor de Gas",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
#  UMBRALES (ajustables en sidebar)
# ══════════════════════════════════════════════════════════════════════════════
UMBRAL_ALERTA  = 400
UMBRAL_PELIGRO = 700
UMBRAL_Z       = 2.5

# ══════════════════════════════════════════════════════════════════════════════
#  ESTILOS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Barlow:wght@300;400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif;
    background-color: #080B10;
    color: #CDD5E0;
}
.stApp { background-color: #080B10; }

section[data-testid="stSidebar"] {
    background-color: #0C0F16 !important;
    border-right: 1px solid #161C28;
}
section[data-testid="stSidebar"] * { color: #8A97B0 !important; }
section[data-testid="stSidebar"] .stSlider > label,
section[data-testid="stSidebar"] .stSelectbox > label { color: #5A6580 !important; font-size: 11px; letter-spacing: 1px; }

/* ── Header ── */
.app-header {
    display: flex;
    align-items: flex-end;
    gap: 18px;
    margin-bottom: 4px;
}
.app-logo {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 4px;
    color: #1DB954;
    background: #091810;
    border: 1px solid #1DB954;
    padding: 4px 10px;
    border-radius: 4px;
}
.app-title {
    font-family: 'Barlow', sans-serif;
    font-size: 30px;
    font-weight: 800;
    color: #E8EEF8;
    letter-spacing: -0.5px;
    line-height: 1;
}
.app-subtitle {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 3px;
    color: #3A4560;
    text-transform: uppercase;
    margin-top: 2px;
}

/* ── Divider ── */
.hdivider {
    border: none;
    border-top: 1px solid #161C28;
    margin: 14px 0 20px 0;
}

/* ── Tarjetas métricas ── */
.metric-row { display: flex; gap: 12px; margin-bottom: 20px; }
.mcard {
    flex: 1;
    background: #0C0F18;
    border: 1px solid #161C28;
    border-top: 2px solid var(--ac);
    border-radius: 8px;
    padding: 16px 18px 14px;
    min-width: 0;
}
.mcard-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #3A4560;
    margin-bottom: 8px;
}
.mcard-val {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 26px;
    font-weight: 700;
    color: var(--ac);
    line-height: 1;
}
.mcard-unit {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: #2A3248;
    margin-top: 5px;
}

/* ── Badge estado ── */
.badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 5px 14px;
    border-radius: 3px;
    display: inline-block;
}
.badge-ok     { background:#071A0F; color:#1DB954; border:1px solid #1DB954; }
.badge-warn   { background:#1A1200; color:#F0A500; border:1px solid #F0A500; }
.badge-danger { background:#1A0505; color:#E03C3C; border:1px solid #E03C3C; }

/* ── Alerta box ── */
.abox {
    border-radius: 6px;
    padding: 12px 16px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    line-height: 1.7;
    border-left: 3px solid var(--ac);
    background: var(--bg);
    color: var(--ac);
    margin-bottom: 10px;
}

/* ── Section label ── */
.sec-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #2A3450;
    border-bottom: 1px solid #161C28;
    padding-bottom: 7px;
    margin: 22px 0 16px 0;
}

/* ── Upload zone ── */
.upload-hint {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #2A3450;
    text-align: center;
    padding: 40px;
    border: 1px dashed #1C2230;
    border-radius: 8px;
    margin-top: 20px;
}

/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0C0F18;
    border-bottom: 1px solid #161C28;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #3A4560;
    background: transparent;
    border: none;
    padding: 10px 20px;
}
.stTabs [aria-selected="true"] {
    color: #1DB954 !important;
    border-bottom: 2px solid #1DB954 !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 20px; }

/* ── Dataframe ── */
.dataframe { font-family: 'IBM Plex Mono', monospace !important; font-size: 11px !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; background: #080B10; }
::-webkit-scrollbar-thumb { background: #1C2230; border-radius: 2px; }

/* hide default metric widget */
div[data-testid="stMetric"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def estado_gas(valor, ua, up):
    if valor >= up:
        return "PELIGRO", "badge-danger", "#E03C3C", "#1A0505"
    elif valor >= ua:
        return "ALERTA",  "badge-warn",   "#F0A500", "#1A1200"
    else:
        return "NORMAL",  "badge-ok",     "#1DB954", "#071A0F"

def fig_dark(figsize=(14, 4)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor('#080B10')
    ax.set_facecolor('#080B10')
    ax.spines[['top','right','left','bottom']].set_color('#161C28')
    ax.tick_params(colors='#3A4560', labelsize=8)
    ax.yaxis.label.set_color('#3A4560')
    ax.xaxis.label.set_color('#3A4560')
    return fig, ax

def style_legend(ax):
    ax.legend(fontsize=8, facecolor='#0C0F18', edgecolor='#161C28', labelcolor='#6A7890')

def render_fig(fig):
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

def metric_card(label, value, unit, color):
    return f"""
    <div class="mcard" style="--ac:{color};">
        <div class="mcard-label">{label}</div>
        <div class="mcard-val">{value}</div>
        <div class="mcard-unit">{unit}</div>
    </div>"""


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:12px 0 28px;">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:16px;font-weight:700;color:#1DB954;">
            ◈ AirLab
        </div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:3px;color:#2A3450;margin-top:2px;">
            EAFIT · MEDELLÍN
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-family:IBM Plex Mono,monospace;font-size:9px;letter-spacing:2px;color:#2A3450;border-bottom:1px solid #161C28;padding-bottom:6px;margin-bottom:14px;">UMBRALES DE ALERTA</div>', unsafe_allow_html=True)
    UMBRAL_ALERTA  = st.slider("⚠️ Alerta (ppm)",  100, 800, 400, step=50)
    UMBRAL_PELIGRO = st.slider("🚨 Peligro (ppm)", 200, 1200, 700, step=50)
    UMBRAL_Z       = st.slider("σ  Z-score",       1.5, 4.0, 2.5, step=0.1)

    st.markdown('<div style="font-family:IBM Plex Mono,monospace;font-size:9px;letter-spacing:2px;color:#2A3450;border-bottom:1px solid #161C28;padding-bottom:6px;margin:20px 0 14px;">SENSOR INFO</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#2A3450;line-height:2;">
    Tipo · MQ-2 / MQ-5<br>
    Unidad · ppm<br>
    Plataforma · ESP32<br>
    Campus · EAFIT<br>
    Lat · 6.2006<br>
    Lon · −75.5783
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown("""
    <div class="app-header">
        <span class="app-logo">GAS · PPM</span>
        <div>
            <div class="app-title">AirLab Monitor</div>
            <div class="app-subtitle">Análisis de Calidad de Aire — Universidad EAFIT, Medellín</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    st.markdown(f"""
    <div style="text-align:right;padding-top:12px;">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:9px;color:#2A3450;letter-spacing:2px;">
            {datetime.now().strftime('%d %b %Y · %H:%M')}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="hdivider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MAPA
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("📍 Ubicación del Sensor — Universidad EAFIT", expanded=False):
    eafit_location = pd.DataFrame({'lat': [6.2006], 'lon': [-75.5783]})
    st.map(eafit_location, zoom=15)
    st.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#2A3450;margin-top:8px;">
    Sensor instalado en Campus EAFIT · Medellín, Colombia · Alt: ~1,495 m.s.n.m.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  CARGA DE ARCHIVO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-label">Fuente de datos</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Cargar archivo CSV del sensor",
    type=["csv"],
    help="El CSV debe tener una columna 'Time' (datetime) y una columna de valores de gas (ppm)."
)

if uploaded_file is None:
    st.markdown("""
    <div class="upload-hint">
        ◈ &nbsp; Carga un archivo CSV para comenzar el análisis<br><br>
        <span style="font-size:9px;letter-spacing:2px;">FORMATO ESPERADO: columna Time + columna de gas (ppm)</span>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  PROCESAMIENTO
# ══════════════════════════════════════════════════════════════════════════════
try:
    df_raw = pd.read_csv(uploaded_file)

    # Detectar columna de tiempo
    if 'Time' in df_raw.columns:
        other_cols = [c for c in df_raw.columns if c != 'Time']
        if other_cols:
            df_raw = df_raw.rename(columns={other_cols[0]: 'gas'})
        df_raw['Time'] = pd.to_datetime(df_raw['Time'])
        df_raw = df_raw.set_index('Time')
    else:
        df_raw = df_raw.rename(columns={df_raw.columns[0]: 'gas'})

    df_raw = df_raw[['gas']].dropna()
    df_raw['gas'] = df_raw['gas'].astype(float)
    s = df_raw['gas']

except Exception as e:
    st.error(f"Error al leer el archivo: {e}")
    st.stop()

# Estadísticos base
media    = s.mean()
mediana  = s.median()
std_     = s.std()
min_     = s.min()
max_     = s.max()
q1, q3   = s.quantile(0.25), s.quantile(0.75)
iqr      = q3 - q1
z_scores = (s - media) / std_
n_anom   = int((z_scores.abs() > UMBRAL_Z).sum())
n_out    = int(((s < q1 - 1.5*iqr) | (s > q3 + 1.5*iqr)).sum())
valor_actual = s.iloc[-1]
estado, badge_cls, color_est, bg_est = estado_gas(valor_actual, UMBRAL_ALERTA, UMBRAL_PELIGRO)


# ══════════════════════════════════════════════════════════════════════════════
#  MÉTRICAS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-label">Resumen del período</div>', unsafe_allow_html=True)

cards_html = '<div class="metric-row">'
cards_html += metric_card("Último valor",   f"{valor_actual:.1f}", "ppm actual",    color_est)
cards_html += metric_card("Promedio",        f"{media:.1f}",        "ppm media",     "#2E7DD1")
cards_html += metric_card("Máximo",          f"{max_:.1f}",         "ppm pico",      "#E03C3C")
cards_html += metric_card("Mínimo",          f"{min_:.1f}",         "ppm base",      "#8A5CF6")
cards_html += metric_card("Desv. Estándar",  f"{std_:.1f}",         "ppm σ",         "#F0A500")
cards_html += metric_card("Anomalías",       str(n_anom),           f"de {len(s)} pts", "#E07820")
cards_html += metric_card("Registros",       str(len(s)),           "total puntos",  "#3A9BAA")
cards_html += '</div>'
st.markdown(cards_html, unsafe_allow_html=True)

# Badge estado
col_b1, col_b2 = st.columns([1, 5])
with col_b1:
    st.markdown(f'<span class="badge {badge_cls}">● {estado}</span>', unsafe_allow_html=True)
with col_b2:
    if estado != "NORMAL":
        st.markdown(f"""
        <div class="abox" style="--ac:{color_est};--bg:{bg_est};">
            {'🚨' if estado == 'PELIGRO' else '⚠️'} Concentración actual <strong>{valor_actual:.2f} ppm</strong>
            {'supera el umbral de PELIGRO' if estado == 'PELIGRO' else 'supera el umbral de ALERTA'}
            ({UMBRAL_PELIGRO if estado == 'PELIGRO' else UMBRAL_ALERTA} ppm)
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈  Serie de Tiempo",
    "📊  Distribución",
    "⚠️  Anomalías",
    "🔍  Filtros",
    "📋  Reporte",
])


# ─── TAB 1: SERIE DE TIEMPO ──────────────────────────────────────────────────
with tab1:
    tipo_viz = st.radio(
        "Vista",
        ["Señal + Media Móvil", "Solo señal cruda", "Solo tendencia (MM15)"],
        horizontal=True,
        label_visibility="collapsed"
    )

    fig, ax = fig_dark((14, 4.5))
    rm5  = s.rolling(window=5,  center=True).mean()
    rm15 = s.rolling(window=15, center=True).mean()

    if tipo_viz in ["Señal + Media Móvil", "Solo señal cruda"]:
        ax.plot(s.index, s, color='#1DB954', alpha=0.2, linewidth=1, label='Señal cruda')
    if tipo_viz in ["Señal + Media Móvil"]:
        ax.plot(rm5.index,  rm5,  color='#1DB954', alpha=0.7, linewidth=1.5, label='MM 5 pts')
        ax.plot(rm15.index, rm15, color='#A8F0C0', alpha=1.0, linewidth=2.5, label='MM 15 pts (tendencia)')
    if tipo_viz == "Solo tendencia (MM15)":
        ax.plot(rm15.index, rm15, color='#A8F0C0', linewidth=2.5, label='MM 15 pts')

    ax.axhspan(UMBRAL_ALERTA,  UMBRAL_PELIGRO, alpha=0.04, color='#F0A500')
    ax.axhspan(UMBRAL_PELIGRO, max(s.max(), UMBRAL_PELIGRO+50), alpha=0.04, color='#E03C3C')
    ax.axhline(UMBRAL_ALERTA,  color='#F0A500', linestyle='--', linewidth=0.8, alpha=0.5, label=f'Umbral alerta ({UMBRAL_ALERTA})')
    ax.axhline(UMBRAL_PELIGRO, color='#E03C3C', linestyle='--', linewidth=0.8, alpha=0.5, label=f'Umbral peligro ({UMBRAL_PELIGRO})')
    ax.fill_between(s.index, s, alpha=0.05, color='#1DB954')

    # Anomalías
    anomalias = s[z_scores.abs() > UMBRAL_Z]
    if len(anomalias):
        ax.scatter(anomalias.index, anomalias, color='#F0A500', s=40, zorder=5, label=f'Anomalías ({len(anomalias)})')

    ax.set_ylabel('Gas (ppm)', fontsize=9)
    if hasattr(s.index, 'strftime'):
        try:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.gcf().autofmt_xdate(rotation=45)
        except:
            pass
    style_legend(ax)
    plt.tight_layout()
    render_fig(fig)

    if st.checkbox("Mostrar datos crudos"):
        st.dataframe(df_raw, use_container_width=True)


# ─── TAB 2: DISTRIBUCIÓN ─────────────────────────────────────────────────────
with tab2:
    col_hist, col_box = st.columns(2)

    with col_hist:
        st.markdown('<div style="font-family:IBM Plex Mono,monospace;font-size:9px;letter-spacing:2px;color:#2A3450;margin-bottom:10px;">HISTOGRAMA + KDE</div>', unsafe_allow_html=True)
        fig, ax = fig_dark((6, 4))
        sns.histplot(s, bins=25, kde=True, ax=ax, color='#1DB954', alpha=0.35)
        ax.axvline(media,   color='#A8F0C0', linestyle='--', linewidth=1.5, label=f'Media: {media:.1f}')
        ax.axvline(mediana, color='#F0A500', linestyle='-.',  linewidth=1.5, label=f'Mediana: {mediana:.1f}')
        ax.axvline(UMBRAL_ALERTA,  color='#F0A500', linestyle=':', linewidth=1, alpha=0.5)
        ax.axvline(UMBRAL_PELIGRO, color='#E03C3C', linestyle=':', linewidth=1, alpha=0.5)
        ax.set_xlabel('Gas (ppm)', fontsize=9)
        ax.set_ylabel('Frecuencia', fontsize=9)
        style_legend(ax)
        plt.tight_layout()
        render_fig(fig)

    with col_box:
        st.markdown('<div style="font-family:IBM Plex Mono,monospace;font-size:9px;letter-spacing:2px;color:#2A3450;margin-bottom:10px;">BOXPLOT</div>', unsafe_allow_html=True)
        fig, ax = fig_dark((6, 4))
        bp = ax.boxplot(s, patch_artist=True, vert=True, widths=0.5,
                        medianprops=dict(color='#080B10', linewidth=2.5))
        bp['boxes'][0].set_facecolor('#1DB954')
        bp['boxes'][0].set_alpha(0.6)
        for w in bp['whiskers'] + bp['caps']:
            w.set_color('#1DB954'); w.set_alpha(0.6)
        for flier in bp['fliers']:
            flier.set(marker='o', color='#F0A500', alpha=0.7, markersize=5)
        ax.annotate(f'Q3 = {q3:.1f}', xy=(1.32, q3),  fontsize=8, color='#6A7890')
        ax.annotate(f'Md = {mediana:.1f}', xy=(1.32, mediana), fontsize=8, color='#A8F0C0', fontweight='bold')
        ax.annotate(f'Q1 = {q1:.1f}', xy=(1.32, q1),  fontsize=8, color='#6A7890')
        ax.set_title(f'{n_out} outlier(s) detectados', color='#3A4560', fontsize=9)
        ax.set_ylabel('Gas (ppm)', fontsize=9)
        ax.set_xticks([])
        plt.tight_layout()
        render_fig(fig)


# ─── TAB 3: ANOMALÍAS ────────────────────────────────────────────────────────
with tab3:
    fig, ax = fig_dark((14, 4))
    ax.plot(s.index, s, color='#1DB954', linewidth=1.3, alpha=0.7, label='Señal')
    ax.fill_between(s.index,
                    media - UMBRAL_Z*std_,
                    media + UMBRAL_Z*std_,
                    alpha=0.07, color='#1DB954', label='Zona normal')
    ax.axhline(media + UMBRAL_Z*std_, color='#3A4560', linestyle=':', linewidth=1)
    ax.axhline(media - UMBRAL_Z*std_, color='#3A4560', linestyle=':', linewidth=1)

    if len(anomalias):
        ax.scatter(anomalias.index, anomalias, color='#F0A500', s=60,
                   zorder=5, label=f'Anomalías |z|>{UMBRAL_Z} ({len(anomalias)})')
    ax.set_ylabel('Gas (ppm)', fontsize=9)
    style_legend(ax)
    try:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gcf().autofmt_xdate(rotation=45)
    except:
        pass
    plt.tight_layout()
    render_fig(fig)

    if len(anomalias) > 0:
        st.markdown('<div class="sec-label">Detalle de anomalías</div>', unsafe_allow_html=True)
        anom_df = pd.DataFrame({
            'Tiempo'    : [str(t) for t in anomalias.index],
            'Gas (ppm)' : anomalias.values.round(2),
            'Z-score'   : z_scores[anomalias.index].values.round(3),
            'Severidad' : ['🚨 PELIGRO' if v >= UMBRAL_PELIGRO else '⚠️ ALERTA' if v >= UMBRAL_ALERTA else '📊 Estadística'
                           for v in anomalias.values],
        })
        st.dataframe(anom_df, use_container_width=True, hide_index=True)
    else:
        st.markdown("""
        <div class="abox" style="--ac:#1DB954;--bg:#071A0F;">
            ✅ Sin anomalías estadísticas detectadas en el período analizado
        </div>
        """, unsafe_allow_html=True)


# ─── TAB 4: FILTROS ──────────────────────────────────────────────────────────
with tab4:
    if s.min() == s.max():
        st.warning("Todos los valores son iguales — no se pueden aplicar filtros.")
        st.dataframe(df_raw, use_container_width=True)
    else:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            min_val = st.slider("Valor mínimo", float(min_), float(max_), float(media), key="fmin")
            df_fmin = df_raw[df_raw['gas'] > min_val]
            st.markdown(f'<div class="sec-label">{len(df_fmin)} registros con gas > {min_val:.1f} ppm</div>', unsafe_allow_html=True)
            st.dataframe(df_fmin, use_container_width=True)
        with col_f2:
            max_val = st.slider("Valor máximo", float(min_), float(max_), float(media), key="fmax")
            df_fmax = df_raw[df_raw['gas'] < max_val]
            st.markdown(f'<div class="sec-label">{len(df_fmax)} registros con gas < {max_val:.1f} ppm</div>', unsafe_allow_html=True)
            st.dataframe(df_fmax, use_container_width=True)

        csv_bytes = df_fmin.to_csv().encode('utf-8')
        st.download_button(
            "⬇  Descargar datos filtrados (CSV)",
            data=csv_bytes,
            file_name='gas_filtrado.csv',
            mime='text/csv',
        )


# ─── TAB 5: REPORTE ──────────────────────────────────────────────────────────
with tab5:
    col_r1, col_r2 = st.columns([3, 2])

    with col_r1:
        st.markdown('<div class="sec-label">Estadísticos completos</div>', unsafe_allow_html=True)
        reporte = pd.DataFrame({
            'Estadístico': ['Registros', 'Mínimo', 'Máximo', 'Rango', 'Media', 'Mediana',
                            'Desv. Std', 'Varianza', 'IQR', 'Asimetría', 'Curtosis',
                            'Outliers (IQR)', 'Anomalías (Z)', 'Autocorr. lag-1'],
            'Valor': [
                len(s),
                f"{min_:.2f} ppm",
                f"{max_:.2f} ppm",
                f"{max_ - min_:.2f} ppm",
                f"{media:.2f} ppm",
                f"{mediana:.2f} ppm",
                f"{std_:.2f} ppm",
                f"{s.var():.2f}",
                f"{iqr:.2f} ppm",
                f"{s.skew():.4f}",
                f"{s.kurt():.4f}",
                n_out,
                n_anom,
                f"{s.autocorr(lag=1):.4f}",
            ]
        })
        st.dataframe(reporte, use_container_width=True, hide_index=True)

    with col_r2:
        st.markdown('<div class="sec-label">Autocorrelación por lag</div>', unsafe_allow_html=True)
        if len(s) > 31:
            fig, ax = fig_dark((5, 3.5))
            lags  = range(1, 31)
            acors = [s.autocorr(lag=k) for k in lags]
            colors_bar = ['#1DB954' if v >= 0 else '#E03C3C' for v in acors]
            ax.bar(lags, acors, color=colors_bar, alpha=0.75, width=0.7)
            ax.axhline(0,     color='#3A4560', linewidth=0.8)
            ax.axhline( 0.3,  color='#2A3450', linestyle='--', linewidth=1)
            ax.axhline(-0.3,  color='#2A3450', linestyle='--', linewidth=1)
            ax.set_xlabel('Lag', fontsize=8)
            ax.set_ylabel('ACF', fontsize=8)
            plt.tight_layout()
            render_fig(fig)
        else:
            st.info("Se necesitan más de 31 registros para calcular autocorrelación.")

    # Interpretación automática
    st.markdown('<div class="sec-label">Interpretación automática</div>', unsafe_allow_html=True)
    skew_ = s.skew()
    interp_color = color_est
    interp_bg    = bg_est

    interpretaciones = []
    interpretaciones.append(f"{'🚨' if estado=='PELIGRO' else '⚠️' if estado=='ALERTA' else '✅'} Estado actual: <strong>{estado}</strong> — último valor {valor_actual:.2f} ppm")

    if skew_ > 1:
        interpretaciones.append("📐 Distribución con <strong>sesgo positivo pronunciado</strong>: la mayoría de lecturas son bajas pero hay picos altos ocasionales.")
    elif skew_ < -1:
        interpretaciones.append("📐 Distribución con <strong>sesgo negativo</strong>: los valores tienden a concentrarse en rangos altos.")
    else:
        interpretaciones.append("📐 Distribución <strong>aproximadamente simétrica</strong> alrededor de la media.")

    if n_anom > 0:
        interpretaciones.append(f"⚡ Se detectaron <strong>{n_anom} anomalías estadísticas</strong> por Z-score — revisar picos en la serie de tiempo.")

    r_lag1 = s.autocorr(lag=1) if len(s) > 5 else 0
    if r_lag1 > 0.7:
        interpretaciones.append(f"🔗 Autocorrelación lag-1 alta (r={r_lag1:.3f}): la señal tiene <strong>alta inercia</strong>, valores consecutivos muy similares.")
    elif r_lag1 > 0.3:
        interpretaciones.append(f"🔗 Autocorrelación lag-1 moderada (r={r_lag1:.3f}): cierta <strong>persistencia</strong> en la señal.")
    else:
        interpretaciones.append(f"🔗 Autocorrelación baja (r={r_lag1:.3f}): las lecturas son <strong>relativamente independientes</strong> entre sí.")

    for i in interpretaciones:
        color_i = color_est if '🚨' in i or '⚠️' in i else '#2E7DD1' if '🔗' in i else '#6A7890'
        bg_i    = bg_est    if '🚨' in i or '⚠️' in i else '#050D1A' if '🔗' in i else '#0C0F18'
        st.markdown(f'<div class="abox" style="--ac:{color_i};--bg:{bg_i};">{i}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<hr style="border:none;border-top:1px solid #161C28;margin:40px 0 16px;">
<div style="text-align:center;font-family:'IBM Plex Mono',monospace;font-size:9px;
     color:#1C2230;letter-spacing:2px;">
    ◈ AIRLAB MONITOR &nbsp;·&nbsp; SENSOR MQ-2 / MQ-5 &nbsp;·&nbsp;
    ESP32 &nbsp;·&nbsp; UNIVERSIDAD EAFIT &nbsp;·&nbsp; MEDELLÍN 🇨🇴
</div>
""", unsafe_allow_html=True)
