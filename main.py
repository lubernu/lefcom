import streamlit as st
import pandas as pd
import os

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

# --- 2. CARGA DE DATOS (Solo se ejecuta si pasó el login) ---
@st.cache_data(ttl=86400)
def cargar_todos_los_datos():
    archivos = ['datos_2018_2022.csv', 'datos_2023_2025.csv', 'datos_2026.csv']
    dfs = []
    progreso = st.progress(0, "Cargando archivos históricos...")
    
    for i, archivo in enumerate(archivos):
        if os.path.exists(archivo):
            df_temp = pd.read_csv(archivo)
            dfs.append(df_temp)
            progreso.progress((i + 1) / len(archivos), f"Cargado: {archivo}")
        else:
            st.warning(f"⚠️ Archivo faltante en repo: {archivo}")
    
    progreso.empty()
    return pd.concat(dfs, ignore_index=True) if dfs else None

# --- 3. PROCESAMIENTO Y UI ---
df = cargar_todos_los_datos()

if df is not None:
    # Preparación de columnas
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['año'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.month
    
    PALETA_COLORES = ['#e24b3c', '#448ea1', '#a8b0b3', '#dbe0da', '#fafbfa']
    
    # CSS de Tarjetas
    st.markdown(f"""
        <style>
        .metric-card {{
            background-color: {PALETA_COLORES[4]};
            padding: 20px; border-radius: 10px;
            border-left: 5px solid {PALETA_COLORES[1]};
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
            text-align: center; margin-bottom: 15px;
        }}
        .metric-title {{ font-size: 14px; color: {PALETA_COLORES[2]}; font-weight: bold; text-transform: uppercase; }}
        .metric-value {{ font-size: 26px; color: {PALETA_COLORES[0]}; font-weight: bold; }}
        </style>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.title("📊 Panel Control")
        if st.button("🔓 Cerrar Sesión"):
            st.session_state["password_correct"] = False
            st.rerun()
        
        st.divider()
        anios = sorted(df['año'].unique(), reverse=True)
        anio_sel = st.selectbox("Año", anios)
        meses = sorted(df[df['año'] == anio_sel]['mes'].unique())
        mes_sel = st.selectbox("Mes", meses)
        
        df_filtered = df[(df['año'] == anio_sel) & (df['mes'] == mes_sel)]

    # Tabs y KPIs (Tu lógica original simplificada)
    tab1, tab2, tab3 = st.tabs(["📋 General", "📈 Informe", "ℹ️ Marcas"])

    with tab1:
        st.subheader(f"Vista previa: Mes {mes_sel} - {anio_sel}")
        
        # Cálculos rápidos
        def get_metrics(data):
            # Usamos .get para evitar errores si no hay registros
            m = {}
            m['total_v'] = len(data)
            m['ing_total'] = data['Ingreso'].sum()
            
            # Filtros por producto
            for p in ['Postpago', 'Kit Contado', 'Reposicion']:
                sub = data[data['producto'] == p]
                m[f'count_{p}'] = len(sub)
                m[f'ticket_{p}'] = sub['Ingreso'].mean() if len(sub) > 0 else 0
            
            m['vend_act'] = data['nombre_asesor'].nunique()
            m['finan'] = data['metodo_pago'].count()
            return m

        res = get_metrics(df_filtered)

        # Render de Tarjetas
        col1, col2, col3 = st.columns(3)
        col1.markdown(f'<div class="metric-card"><div class="metric-title">Ventas Totales</div><div class="metric-value">{res["total_v"]:,}</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card"><div class="metric-title">Ventas Post</div><div class="metric-value">{res["count_Postpago"]:,}</div></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="metric-card"><div class="metric-title">Ticket Prom Post</div><div class="metric-value">${res["ticket_Postpago"]:,.0f}</div></div>', unsafe_allow_html=True)

        col4, col5, col6 = st.columns(3)
        col4.markdown(f'<div class="metric-card"><div class="metric-title">Vendedores Activos</div><div class="metric-value">{res["vend_act"]:,}</div></div>', unsafe_allow_html=True)
        col5.markdown(f'<div class="metric-card"><div class="metric-title">Ventas Kit</div><div class="metric-value">{res["count_Kit Contado"]:,}</div></div>', unsafe_allow_html=True)
        col6.markdown(f'<div class="metric-card"><div class="metric-title">Ticket Prom Kit</div><div class="metric-value">${res["ticket_Kit Contado"]:,.0f}</div></div>', unsafe_allow_html=True)

        col7, col8, col9 = st.columns(3)
        col7.markdown(f'<div class="metric-card"><div class="metric-title">Ventas Financieras</div><div class="metric-value">{res["finan"]:,}</div></div>', unsafe_allow_html=True)
        col8.markdown(f'<div class="metric-card"><div class="metric-title">Ventas Repo</div><div class="metric-value">{res["count_Reposicion"]:,}</div></div>', unsafe_allow_html=True)
        col9.markdown(f'<div class="metric-card"><div class="metric-title">Ticket Prom Repo</div><div class="metric-value">${res["ticket_Reposicion"]:,.0f}</div></div>', unsafe_allow_html=True)
