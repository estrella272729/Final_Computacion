import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from influxdb_client import InfluxDBClient
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════════════════
URL    = "http://localhost:8086"
TOKEN  = "tu_token_aqui"
ORG    = "tu_org"
BUCKET = "tu_bucket"
CAMPO  = "gas"

UMBRAL_ALERTA   = 400   # ppm — alerta amarilla
UMBRAL_PELIGRO  = 700   # ppm — alerta roja
UMBRAL_Z        = 2.5

st.set_page_config(
    page_title="GasSafe Monitor",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
#  ESTILOS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #0D0F14;
    color: #E8EAF0;
}

/* Fondo general */
.stApp { background-color: #0D0F14; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #13161E;
    border-right: 1px solid #1F2330;
}

/* Tarjetas métricas */
.metric-card {
    background: linear-gradient(135deg, #1A1E2A 0%, #13161E 100%);
    border: 1px solid #252A3A;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent);
}
.metric-label {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #6B7494;
    margin-bottom: 8px;
}
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 32px;
    font-weight: 700;
    color: var(--accent);
    line-height: 1;
}
.metric-sub {
    font-size: 12px;
    color: #4A5068;
    margin-top: 6px;
    font-family: 'Space Mono', monospace;
}

/* Badge de estado */
.status-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.status-ok      { background: #0D2818; color: #27AE60; border: 1px solid #27AE60; }
.status-alerta  { background: #2A1F00; color: #F39C12; border: 1px solid #F39C12; }
.status-peligro { background: #2A0A0A; color: #E74C3C; border: 1px solid #E74C3C; }

/* Título principal */
.main-title {
    font-family: 'Syne', sans-serif;
    font-size: 36px;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(90deg, #27AE60, #2ECC71, #A8E6CF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.sub-title {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 3px;
    color: #4A5068;
    text-transform: uppercase;
    margin-top: -4px;
}

/* Alertas */
.alerta-box {
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    border-left: 4px solid;
}
.alerta-ok      { background: #0A1F12; border-color: #27AE60; color: #27AE60; }
.alerta-warn    { background: #1F1500; border-color: #F39C12; color: #F39C12; }
.alerta-danger  { background: #1F0505; border-color: #E74C3C; color: #E74C3C; }

/* Sección headers */
.section-header {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 3px;
    color: #4A5068;
    text-transform: uppercase;
    border-bottom: 1px solid #1F2330;
    padding-bottom: 8px;
    margin-bottom: 16px;
}

div[data-testid="stMetric"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  FUNCIONES
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60)
def cargar_datos(horas: int) -> pd.Series:
    try:
        client = InfluxDBClient(url=URL, token=TOKEN, org=ORG, verify_ssl=False)
        query = f'''
        from(bucket: "{BUCKET}")
          |> range(start: -{horas}h)
          |> filter(fn: (r) => r._field == "{CAMPO}")
        '''
        tablas = client.query_api().query(query, org=ORG)
        tiempos, valores = [], []
        for tabla in tablas:
            for record in tabla.records:
                tiempos.append(record.get_time())
                valores.append(record.get_value())

        idx = pd.DatetimeIndex(
            pd.to_datetime(pd.Series(tiempos), utc=True)
        ).tz_convert('America/Bogota')
        serie = pd.Series(valores, index=idx, name='gas', dtype=float).sort_index()
        client.close()
        return serie
    except Exception as e:
        # Datos simulados si no hay conexión
        np.random.seed(42)
        n = horas * 60
        idx = pd.date_range(end=pd.Timestamp.now(tz='America/Bogota'), periods=n, freq='1min')
        base = 250 + np.cumsum(np.random.randn(n) * 3)
        base = np.clip(base, 100, 900)
        # Inyectar algunos picos
        for i in np.random.choice(n, 5):
            base[i] += np.random.randint(300, 500)
        return pd.Series(base, index=idx, name='gas')


def estado_gas(valor: float):
    if valor >= UMBRAL_PELIGRO:
        return "PELIGRO", "status-peligro", "#E74C3C", "alerta-danger", "🚨"
    elif valor >= UMBRAL_ALERTA:
        return "ALERTA", "status-alerta", "#F39C12", "alerta-warn", "⚠️"
    else:
        return "NORMAL", "status-ok", "#27AE60", "alerta-ok", "✅"


def fig_to_streamlit(fig):
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='padding: 8px 0 24px 0;'>
        <div style='font-family: Syne; font-size: 20px; font-weight: 800; color: #27AE60;'>⬡ GasSafe</div>
        <div style='font-family: Space Mono; font-size: 10px; color: #4A5068; letter-spacing: 2px;'>MONITOR INDUSTRIAL</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Configuración</div>', unsafe_allow_html=True)
    horas = st.slider("Ventana de tiempo (horas)", 1, 24, 2)
    intervalo_resample = st.selectbox("Resolución", ["1min", "2min", "5min"], index=0)
    auto_refresh = st.checkbox("Auto-refresh (60s)", value=False)

    st.markdown('<div class="section-header" style="margin-top:24px;">Umbrales</div>', unsafe_allow_html=True)
    u_alerta  = st.number_input("⚠️ Alerta (ppm)",  value=UMBRAL_ALERTA,  step=50)
    u_peligro = st.number_input("🚨 Peligro (ppm)", value=UMBRAL_PELIGRO, step=50)
    UMBRAL_ALERTA  = u_alerta
    UMBRAL_PELIGRO = u_peligro

    st.markdown("---")
    st.markdown("""
    <div style='font-family: Space Mono; font-size: 10px; color: #3A4055; line-height: 1.8;'>
    Sensor: MQ-2 / MQ-5<br>
    Unidad: ppm<br>
    Zona horaria: UTC−5 Bogotá
    </div>
    """, unsafe_allow_html=True)

    if auto_refresh:
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  CARGA DE DATOS
# ══════════════════════════════════════════════════════════════════════════════
with st.spinner("Consultando InfluxDB..."):
    s_raw = cargar_datos(horas)

df = s_raw.resample(intervalo_resample).mean().dropna().to_frame()
df.index.name = 'tiempo'

valor_actual = df['gas'].iloc[-1]
estado, badge_class, color_estado, alerta_class, emoji_estado = estado_gas(valor_actual)


# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown('<div class="main-title">GasSafe Monitor</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sub-title">Monitoreo continuo de gas — {df.index[-1].strftime("%d %b %Y, %H:%M")} hora Bogotá</div>',
        unsafe_allow_html=True
    )
with col_status:
    st.markdown(f"""
    <div style='text-align:right; padding-top: 8px;'>
        <span class='status-badge {badge_class}'>{emoji_estado} {estado}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MÉTRICAS
# ══════════════════════════════════════════════════════════════════════════════
s = df['gas']
q1, q3 = s.quantile(0.25), s.quantile(0.75)
iqr = q3 - q1
n_outliers = int(((s < q1 - 1.5*iqr) | (s > q3 + 1.5*iqr)).sum())
z_scores = (s - s.mean()) / s.std()
n_anomalias = int((z_scores.abs() > UMBRAL_Z).sum())

metricas = [
    ("Valor Actual",  f"{valor_actual:.1f}",  "ppm",         color_estado),
    ("Promedio",      f"{s.mean():.1f}",       "ppm media",   "#2980B9"),
    ("Máximo",        f"{s.max():.1f}",        "ppm pico",    "#E74C3C"),
    ("Mínimo",        f"{s.min():.1f}",        "ppm base",    "#8E44AD"),
    ("Desv. Estándar",f"{s.std():.1f}",        "ppm σ",       "#F39C12"),
    ("Anomalías",     str(n_anomalias),         f"de {len(s)} pts", "#E67E22"),
]

cols = st.columns(6)
for col, (label, valor, sub, accent) in zip(cols, metricas):
    with col:
        st.markdown(f"""
        <div class="metric-card" style="--accent: {accent};">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{valor}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PANEL DE ALERTAS
# ══════════════════════════════════════════════════════════════════════════════
with st.expander(f"{emoji_estado} Estado del sistema — {estado}", expanded=(estado != "NORMAL")):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class='alerta-box {alerta_class}'>
            {emoji_estado} <strong>Concentración actual:</strong> {valor_actual:.2f} ppm<br>
            Umbral alerta: {UMBRAL_ALERTA} ppm &nbsp;|&nbsp; Umbral peligro: {UMBRAL_PELIGRO} ppm
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        if n_anomalias > 0:
            st.markdown(f"""
            <div class='alerta-box alerta-warn'>
                ⚡ <strong>{n_anomalias} anomalía(s)</strong> detectadas por Z-score (|z| > {UMBRAL_Z})
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='alerta-box alerta-ok'>
                ✅ <strong>Sin anomalías</strong> estadísticas en el período analizado
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  GRÁFICO PRINCIPAL — Serie de tiempo
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Serie de Tiempo</div>', unsafe_allow_html=True)

fig, ax = plt.subplots(figsize=(14, 4.5))
fig.patch.set_facecolor('#0D0F14')
ax.set_facecolor('#0D0F14')

color_gas = '#27AE60'
rm5  = s.rolling(window=5,  center=True).mean()
rm15 = s.rolling(window=15, center=True).mean()

ax.plot(s.index, s,    color=color_gas,  alpha=0.25, linewidth=1,   label='Señal cruda')
ax.plot(rm5.index,  rm5,  color=color_gas,  alpha=0.7,  linewidth=1.5, label='MM 5 min')
ax.plot(rm15.index, rm15, color='#A8E6CF', alpha=1.0,  linewidth=2.5, label='MM 15 min (tendencia)')

# Zonas de umbral
ax.axhspan(UMBRAL_ALERTA,  UMBRAL_PELIGRO, alpha=0.06, color='#F39C12')
ax.axhspan(UMBRAL_PELIGRO, s.max()*1.1,   alpha=0.06, color='#E74C3C')
ax.axhline(UMBRAL_ALERTA,  color='#F39C12', linestyle='--', linewidth=1, alpha=0.5, label=f'Umbral alerta ({UMBRAL_ALERTA} ppm)')
ax.axhline(UMBRAL_PELIGRO, color='#E74C3C', linestyle='--', linewidth=1, alpha=0.5, label=f'Umbral peligro ({UMBRAL_PELIGRO} ppm)')

# Anomalías
anomalias = s[z_scores.abs() > UMBRAL_Z]
if len(anomalias):
    ax.scatter(anomalias.index, anomalias, color='#F39C12', s=60, zorder=5, label=f'Anomalías ({len(anomalias)})')

ax.fill_between(s.index, s, alpha=0.08, color=color_gas)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
plt.gcf().autofmt_xdate(rotation=45)
ax.set_ylabel('Gas (ppm)', color='#6B7494', fontsize=10)
ax.set_xlabel('Hora (Colombia)', color='#6B7494', fontsize=10)
ax.tick_params(colors='#4A5068')
ax.spines[['top','right','left','bottom']].set_color('#1F2330')
ax.legend(loc='upper left', fontsize=8, facecolor='#13161E', edgecolor='#252A3A', labelcolor='#8A9BB0')
plt.tight_layout()
fig_to_streamlit(fig)


# ══════════════════════════════════════════════════════════════════════════════
#  SEGUNDA FILA — Histograma + Boxplot
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Distribución Estadística</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    import seaborn as sns
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor('#0D0F14')
    ax.set_facecolor('#0D0F14')
    sns.histplot(s, bins=25, kde=True, ax=ax, color='#27AE60', alpha=0.45)
    ax.axvline(s.mean(),   color='#A8E6CF', linestyle='--', linewidth=1.5, label=f'Media: {s.mean():.1f}')
    ax.axvline(s.median(), color='#F39C12', linestyle='-.',  linewidth=1.5, label=f'Mediana: {s.median():.1f}')
    ax.axvline(UMBRAL_ALERTA,  color='#F39C12', linestyle=':', linewidth=1, alpha=0.6)
    ax.axvline(UMBRAL_PELIGRO, color='#E74C3C', linestyle=':', linewidth=1, alpha=0.6)
    ax.set_title('Histograma + KDE', color='#8A9BB0', fontsize=11)
    ax.set_xlabel('Gas (ppm)', color='#6B7494', fontsize=9)
    ax.set_ylabel('Frecuencia', color='#6B7494', fontsize=9)
    ax.tick_params(colors='#4A5068')
    ax.spines[['top','right','left','bottom']].set_color('#1F2330')
    ax.legend(fontsize=8, facecolor='#13161E', edgecolor='#252A3A', labelcolor='#8A9BB0')
    plt.tight_layout()
    fig_to_streamlit(fig)

with col2:
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor('#0D0F14')
    ax.set_facecolor('#0D0F14')
    bp = ax.boxplot(s, patch_artist=True, vert=True, widths=0.5,
                    medianprops=dict(color='#0D0F14', linewidth=2.5))
    bp['boxes'][0].set_facecolor('#27AE60')
    bp['boxes'][0].set_alpha(0.7)
    for w in bp['whiskers'] + bp['caps']:
        w.set_color('#27AE60')
    for flier in bp['fliers']:
        flier.set(marker='o', color='#F39C12', alpha=0.6, markersize=5)
    q1_, med_, q3_ = s.quantile(0.25), s.median(), s.quantile(0.75)
    ax.annotate(f'Q3 = {q3_:.1f}', xy=(1.32, q3_), fontsize=8, color='#6B7494')
    ax.annotate(f'Md = {med_:.1f}', xy=(1.32, med_), fontsize=8, color='#A8E6CF', fontweight='bold')
    ax.annotate(f'Q1 = {q1_:.1f}', xy=(1.32, q1_), fontsize=8, color='#6B7494')
    ax.set_title(f'Boxplot — {n_outliers} outlier(s)', color='#8A9BB0', fontsize=11)
    ax.set_ylabel('Gas (ppm)', color='#6B7494', fontsize=9)
    ax.set_xticks([])
    ax.tick_params(colors='#4A5068')
    ax.spines[['top','right','left','bottom']].set_color('#1F2330')
    plt.tight_layout()
    fig_to_streamlit(fig)


# ══════════════════════════════════════════════════════════════════════════════
#  TERCERA FILA — Autocorrelación + Reporte
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Análisis Avanzado</div>', unsafe_allow_html=True)
col3, col4 = st.columns([3, 2])

with col3:
    fig, ax = plt.subplots(figsize=(8, 3.5))
    fig.patch.set_facecolor('#0D0F14')
    ax.set_facecolor('#0D0F14')
    lags  = range(1, 31)
    acors = [s.autocorr(lag=k) for k in lags]
    colors_bar = ['#27AE60' if v >= 0 else '#E74C3C' for v in acors]
    ax.bar(lags, acors, color=colors_bar, alpha=0.75, width=0.7)
    ax.axhline(0,    color='#4A5068', linewidth=0.8)
    ax.axhline( 0.3, color='#6B7494', linestyle='--', linewidth=1, alpha=0.6, label='±0.3')
    ax.axhline(-0.3, color='#6B7494', linestyle='--', linewidth=1, alpha=0.6)
    ax.set_title('Autocorrelación por Lag', color='#8A9BB0', fontsize=11)
    ax.set_xlabel('Lag (min)', color='#6B7494', fontsize=9)
    ax.set_ylabel('ACF', color='#6B7494', fontsize=9)
    ax.tick_params(colors='#4A5068')
    ax.spines[['top','right','left','bottom']].set_color('#1F2330')
    ax.legend(fontsize=8, facecolor='#13161E', edgecolor='#252A3A', labelcolor='#8A9BB0')
    plt.tight_layout()
    fig_to_streamlit(fig)

with col4:
    r_lag1 = s.autocorr(lag=1)
    skew_  = s.skew()
    kurt_  = s.kurt()

    st.markdown(f"""
    <div style='background: #13161E; border: 1px solid #1F2330; border-radius: 12px; padding: 20px; font-family: Space Mono; font-size: 12px; line-height: 2;'>
        <div style='color: #27AE60; font-weight: 700; letter-spacing: 2px; font-size: 11px; margin-bottom: 12px;'>▸ REPORTE ESTADÍSTICO</div>
        <div style='color: #6B7494;'>Período analizado</div>
        <div style='color: #E8EAF0;'>{horas}h &nbsp;·&nbsp; {len(df)} registros</div>
        <hr style='border-color: #1F2330; margin: 10px 0;'>
        <div style='color: #6B7494;'>Rango</div>
        <div style='color: #E8EAF0;'>{s.min():.1f} – {s.max():.1f} ppm</div>
        <div style='color: #6B7494;'>IQR</div>
        <div style='color: #E8EAF0;'>{(q3-q1):.2f} ppm</div>
        <div style='color: #6B7494;'>Varianza</div>
        <div style='color: #E8EAF0;'>{s.var():.2f}</div>
        <div style='color: #6B7494;'>Asimetría</div>
        <div style='color: #E8EAF0;'>{skew_:.4f}</div>
        <div style='color: #6B7494;'>Curtosis</div>
        <div style='color: #E8EAF0;'>{kurt_:.4f}</div>
        <div style='color: #6B7494;'>Autocorr. lag-1</div>
        <div style='color: #E8EAF0;'>r = {r_lag1:.4f}</div>
        <hr style='border-color: #1F2330; margin: 10px 0;'>
        <div style='color: #6B7494;'>Última actualización</div>
        <div style='color: #A8E6CF;'>{datetime.now().strftime("%H:%M:%S")}</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  TABLA DE ANOMALÍAS
# ══════════════════════════════════════════════════════════════════════════════
if n_anomalias > 0:
    st.markdown('<div class="section-header" style="margin-top:16px;">Registro de Anomalías Detectadas</div>', unsafe_allow_html=True)
    anomalias_df = pd.DataFrame({
        'Hora'       : [t.strftime('%H:%M:%S') for t in anomalias.index],
        'Gas (ppm)'  : anomalias.values.round(2),
        'Z-score'    : z_scores[anomalias.index].values.round(3),
        'Severidad'  : ['🚨 PELIGRO' if v >= UMBRAL_PELIGRO else '⚠️ ALERTA' if v >= UMBRAL_ALERTA else '📊 Estadística' for v in anomalias.values],
    })
    st.dataframe(
        anomalias_df,
        use_container_width=True,
        hide_index=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style='text-align: center; margin-top: 40px; padding: 20px; border-top: 1px solid #1F2330;
     font-family: Space Mono; font-size: 10px; color: #3A4055; letter-spacing: 1px;'>
    ⬡ GasSafe Monitor &nbsp;·&nbsp; Sensor MQ-2/MQ-5 &nbsp;·&nbsp; InfluxDB + Streamlit &nbsp;·&nbsp; Colombia 🇨🇴
</div>
""", unsafe_allow_html=True)
