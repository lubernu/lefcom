import streamlit as st
import plotly.express as px
import pandas as pd
from utils import cargar_datos_base, obtener_metricas, calcular_proyeccion
import os

# === NUEVO: Función para filas compactas ===
def set_compact_row_height():
    """Inyecta CSS para filas compactas de 30px en todas las tablas."""
    css = """
    <style>
        /* Aplica a todas las tablas de Streamlit */
        div[data-testid="stDataFrame"] table tbody tr,
        div[data-testid="stDataFrame"] table thead tr {
            height: 30px !important;
        }
        
        /* Padding interno compacto */
        div[data-testid="stDataFrame"] table td,
        div[data-testid="stDataFrame"] table th {
            padding: 4px 8px !important;
            vertical-align: middle !important;
            font-size: 13px !important;
        }
        
        /* Estilo adicional para mejor legibilidad */
        div[data-testid="stDataFrame"] table {
            font-family: 'Inter', sans-serif;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
# ==========================================



# --- 1. CONFIGURACIÓN Y SEGURIDAD ---
st.set_page_config(page_title="Data Assembly", layout="wide")

def check_password():
    """Retorna True si el usuario ingresó la contraseña correcta."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Mostrar formulario de login
    st.title("🔐 Acceso Restringido")
    # Intentamos obtener la clave de secrets, si no existe (local), usamos una por defecto
    password_master = st.secrets.get("password", "LEFCOM2026")
    
    password_input = st.text_input("Introduce la contraseña corporativa", type="password")
    
    if st.button("Ingresar"):
        if password_input == password_master:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("🚫 Contraseña incorrecta")
    return False

# Si no está autenticado, detiene la ejecución aquí
if not check_password():
    st.stop()

# --- CONFIGURACIÓN Y ESTILOS ---
PALETA = ["#a19c9c","#65bd55","#12583EFF","#020D22","#16a34a"]

st.markdown(f"""
    <style>
    .metric-card {{
        background-color: white; padding: 20px; border-radius: 12px;
        border-left: 8px solid {PALETA[2]}; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center; margin-bottom: 10px;
    }}
    .metric-title {{ font-size: 14px; color: #666; font-weight: bold; text-transform: uppercase; }}
    .metric-value {{ font-size: 32px; font-weight: 800; color: {PALETA[3]}; }}
    .metric-delta {{ font-size: 14px; margin-top: 5px; }}
    .up {{ color: green; }} .down {{ color: red; }}
    </style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
df_completo = cargar_datos_base()

if df_completo.empty:
    st.error("No se encontraron archivos de datos.")
    st.stop()

# --- SIDEBAR / FILTROS ---
with st.sidebar:
    st.header("Filtros")
    anios = sorted(df_completo['año'].unique(), reverse=True)
    anio_sel = st.selectbox("Año", anios)
    
    meses_disponibles = df_completo[df_completo['año'] == anio_sel]['mes_nombre'].unique()
    mes_sel = st.selectbox("Mes", meses_disponibles)

# --- LÓGICA DE COMPARACIÓN (EL CORAZÓN DEL PROBLEMA) ---
# 1. Mes Actual
df_actual = df_completo[(df_completo['año'] == anio_sel) & (df_completo['mes_nombre'] == mes_sel)]
m_actual = obtener_metricas(df_actual)

# 2. Mes Anterior (Buscamos en el periodo anterior del DF completo)
periodo_actual = df_actual['periodo'].iloc[0]
periodo_anterior = periodo_actual - 1
df_anterior = df_completo[df_completo['periodo'] == periodo_anterior]
m_anterior = obtener_metricas(df_anterior)

# 3. Proyección
factor_proy = calcular_proyeccion(df_actual)

# --- RENDERIZADO ---
st.title("📊 Dashboard De Ventas")
# === NUEVO: Activar filas compactas ===
set_compact_row_height()
# ======================================

def render_metric(titulo, valor_actual, valor_anterior, factor_proy):
    # Calculamos la proyección
    proyeccion = valor_actual * factor_proy
    
    # La diferencia real para el negocio: ¿Mi proyección actual supera al cierre anterior?
    dif_vs_cierre = proyeccion - valor_anterior
    
    # Formateo de colores basado en la proyección
    delta_class = "up" if dif_vs_cierre >= 0 else "down"
    simbolo = "+" if dif_vs_cierre >= 0 else ""
    
    st.markdown(f"""
        <div class="metric-card" style="background-color: #f0f2f6; padding: 15px; border-radius: 10px;">
            <div class="metric-title">{titulo}</div>
            <div class="metric-value">{valor_actual:,}</div>
            <div class="metric-delta {delta_class}">
                <div style="font-size: 1.1em; font-weight: bold;">
                    Proy: {proyeccion:.0f}
                </div>
                <div>
                    {simbolo}{dif_vs_cierre:.0f} vs cierre ant.
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📋 General", "📈 PDV", "ℹ️ Marcas"])

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        render_metric(f"Ventas {mes_sel}", m_actual['total'], m_anterior['total'], factor_proy)
    with c2: 
        render_metric("Postpago", m_actual['postpago'], m_anterior['postpago'], factor_proy)
    with c3: 
        render_metric("Equipos", m_actual['equipos'], m_anterior['equipos'], factor_proy)
    with c4: 
        render_metric("Financiado", m_actual['financiado'], m_anterior['financiado'], factor_proy)

    st.divider()
    
    col_left, col_right = st.columns([0.6, 0.4])
    with col_left:
        st.subheader("Ventas por CPS")
        pivot_cps = df_actual.pivot_table(index='cps', columns='producto', values='fecha', aggfunc='count', fill_value=0)
        pivot_cps['Total'] = pivot_cps.sum(axis=1)
        st.dataframe(pivot_cps.sort_values('Total', ascending=False), use_container_width=True)
        
    with col_right:
        st.subheader("Distribución de Productos")
        fig_prod = px.bar(df_actual['producto'].value_counts().reset_index(), 
                         x='producto', y='count', text='count',
                         color_discrete_sequence=[PALETA[1]])
        st.plotly_chart(fig_prod, use_container_width=True)

    st.divider()

    col1, col2, col3 = st.columns([0.3,0.3, 0.4])
    with col1:
        st.subheader("Ventas por Financieras")
        vent_financiera = df_actual.groupby('metodo_pago').size().reset_index(name='Cant.').sort_values('Cant.',ascending=True)
        st.dataframe(vent_financiera,hide_index=True)
    with col2:
        st.subheader("Ingreso por producto")
        ing_equipos = df_actual.groupby('producto')['Ingreso'].sum().reset_index(name='Ingreso_Total')
        st.dataframe(ing_equipos,hide_index=True)

    with col3:
        st.subheader("Ventas por Marca")
        vent_marcas = df_actual.groupby('Marca').size().reset_index(name='Cant.').sort_values('Cant.', ascending=True)
        vent_marcas = vent_marcas[vent_marcas['Marca'] != 'TRAIDO' ]
        fig = px.bar(vent_marcas, 
                 x='Cant.', 
                 y='Marca',
                 orientation='h',
                 text='Cant.') 
        fig.update_traces(marker_color=PALETA[1], textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
with tab2:
    c1,c2,c3,c4,c5 = st.columns([.15,.2125,.2125,.2125,.2125])
    with c1:
        pdv = sorted(df_actual['cps'].unique(), reverse=True)
        pdv_sel = st.selectbox("Punto de Venta", pdv)
        df_actual_pdv = df_actual[(df_actual['cps'] == pdv_sel)]
        m_actual = obtener_metricas(df_actual_pdv)
        df_anterior = df_completo[(df_completo['periodo'] == periodo_anterior) & (df_completo['cps']== pdv_sel) ]
        m_anterior = obtener_metricas(df_anterior)
        f_corte = df_actual_pdv['fecha'].max()
        st.info(f"##### Fecha Corte: {f_corte.strftime('%d/%m/%Y')}")

    with c2: 
        render_metric(f"Ventas {mes_sel}", m_actual['total'], m_anterior['total'], factor_proy)
    with c3: 
        render_metric("Postpago", m_actual['postpago'], m_anterior['postpago'], factor_proy)
    with c4: 
        render_metric("Equipos", m_actual['equipos'], m_anterior['equipos'], factor_proy)
    with c5: 
        render_metric("Financiado", m_actual['financiado'], m_anterior['financiado'], factor_proy)

    st.divider()
    col_left, col_right = st.columns([0.6, 0.4])
    with col_left:
        st.subheader("Ventas por Vendedor")
        pivot_vendedor = df_actual_pdv.pivot_table(index='nombre_asesor', columns='producto', values='fecha', aggfunc='count', fill_value=0)
        pivot_vendedor['Total'] = pivot_vendedor.sum(axis=1)
        st.dataframe(pivot_vendedor.sort_values('Total', ascending=False), use_container_width=True)

    with col_right:
        st.subheader("Distribución de Productos")
        fig_prod = px.bar(df_actual_pdv['producto'].value_counts().reset_index(), 
                         x='producto', y='count', text='count',
                         color_discrete_sequence=[PALETA[1]])
        st.plotly_chart(fig_prod, use_container_width=True)

    st.divider()

    col1,col2, col3 = st.columns([0.3,0.3, 0.4])
    with col1:
        st.subheader("Ventas por Financieras")
        vent_financiera = df_actual_pdv.groupby('metodo_pago').size().reset_index(name='Cant.').sort_values('Cant.',ascending=True)
        st.dataframe(vent_financiera,hide_index=True)
    with col2:
        st.subheader("Ventas por producto")
        ing_equipos = df_actual_pdv.groupby('producto')['Ingreso'].sum().reset_index(name='Ingreso_Total')
        st.dataframe(ing_equipos,hide_index=True)

    with col3:
        st.subheader("Ventas por Marca")
        vent_marcas = df_actual_pdv.groupby('Marca').size().reset_index(name='Cant.').sort_values('Cant.', ascending=True)
        vent_marcas = vent_marcas[vent_marcas['Marca'] != 'TRAIDO' ]
        fig = px.bar(vent_marcas, 
                 x='Cant.', 
                 y='Marca',
                 orientation='h',
                 text='Cant.') 
        fig.update_traces(marker_color=PALETA[1], textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
