import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="PENDIENTES", layout="wide")

PALETA_COLORES = ['#e24b3c', '#448ea1', '#a8b0b3', '#dbe0da', '#fafbfa']

st.markdown(f"""
    <style>
    .metric-card {{
        background-color: {PALETA_COLORES[4]};
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid {PALETA_COLORES[1]};
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 15px;
    }}
    .metric-title {{ font-size: 14px; color: {PALETA_COLORES[2]}; font-weight: bold; text-transform: uppercase; }}
    .metric-value {{ font-size: 26px; color: {PALETA_COLORES[0]}; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# 2. FUNCIÓN DE CARGA DE DATOS
@st.cache_data
def load_data():
    ruta1 = r"C:\Users\lubernu\Desktop\streamlit\Archivos\kit_pendiente.csv"
    ruta2 = r"C:\Users\lubernu\Desktop\streamlit\Archivos\post_pendiente.csv"
    df_kit = pd.read_csv(ruta1)
    df_post = pd.read_csv(ruta2)
    return df_kit, df_post

try:
    df_kit, df_post = load_data()
except Exception as e:
    st.error(f"Error al cargar el archivo: {e}")
    st.stop()

# Calcular métricas
total_kit = len(df_kit)
vendidos_kit = df_kit[df_kit['cps'].notna()]
vendidos_kit_count = len(vendidos_kit)
pct_kit = (vendidos_kit_count / total_kit * 100) if total_kit > 0 else 0

total_post = len(df_post)
vendidos_post = df_post[df_post['cps'].notna()]
vendidos_post_count = len(vendidos_post)
pct_post = (vendidos_post_count / total_post * 100) if total_post > 0 else 0

st.title("Seguimiento Seriales por Vender")

# Mostrar métricas en columnas
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📦 Total Kit</div>
            <div class="metric-value">{total_kit:,}</div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">✅ Vendidos Kit</div>
            <div class="metric-value">{vendidos_kit_count:,} ({pct_kit:.1f}%)</div>
        </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📦 Total Post</div>
            <div class="metric-value">{total_post:,}</div>
        </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">✅ Vendidos Post</div>
            <div class="metric-value">{vendidos_post_count:,} ({pct_post:.1f}%)</div>
        </div>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📋 Kit", "📈 Post"])

with tab1:
    st.dataframe(vendidos_kit)
    st.markdown("### Listado Original")
    st.dataframe(df_kit)

with tab2:
    st.dataframe(vendidos_post)
    st.markdown("### Listado Original")
    st.dataframe(df_post)
