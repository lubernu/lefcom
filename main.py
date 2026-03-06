import streamlit as st
import pandas as pd
import glob
import os

# Configuración de la página
st.set_page_config(page_title="Data Assembly", layout="wide")
st.title("📊 Visualizador de Datos Históricos")

@st.cache_data(ttl=86400)  # Cache por 1 dia
def cargar_todos_los_datos():
    """
    Carga y combina todos los archivos CSV de manera eficiente
    """
    # Patrón para encontrar los archivos
    archivos = [
        'datos_2018_2022.csv',
        'datos_2023_2025.csv',
        'datos_2026.csv'
    ]
    
    dfs = []
    total_registros = 0
    
    # Barra de progreso para carga inicial
    progreso = st.progress(0, "Cargando archivos...")
    
    for i, archivo in enumerate(archivos):
        if os.path.exists(archivo):
            # Leer archivo
            df_temp = pd.read_csv(archivo)
            dfs.append(df_temp)
            total_registros += len(df_temp)
            
            # Actualizar progreso
            progreso.progress((i + 1) / len(archivos), 
                            f"Cargado: {os.path.basename(archivo)} - {len(df_temp):,} registros")
        else:
            st.warning(f"⚠️ Archivo no encontrado: {archivo}")
    
    progreso.empty()  # Eliminar barra de progreso
    
    if dfs:
        # Combinar todos los DataFrames
        df_completo = pd.concat(dfs, ignore_index=True)
        return df_completo   
    return None

# Cargar datos (solo se ejecuta una vez y se guarda en caché)
df = cargar_todos_los_datos()
df['año'] = df['fecha'].dt.year
df['mes'] = df['fecha'].dt.month

if df is not None:
    # Selector de columnas en sidebar
    with st.sidebar:
        st.subheader("🎯 Filtros")
            anios = sorted(df['año'].unique(), reverse=True)
            anio_sel = st.sidebar.selectbox("Año", anios)            
            meses = df[df['año'] == anio_sel]['mes'].unique()
            mes_sel = st.sidebar.selectbox("Mes", meses)            
            df_filtered = df[(df['año'] == anio_sel) & (df['mes'] == mes_sel)]            
    
    # Mostrar datos
    tab1, tab2, tab3 = st.tabs(["📋 Datos", "📈 Estadísticas", "ℹ️ Info"])
    
    with tab1:
        st.subheader("Vista previa de datos")
            total_ingresos = df_filtered['ingresos_totales'].sum()
            ingresos_post = df_filtered.loc[df_filtered['producto'] == 'Postpago', 'ingresos_totales'].sum()
            ingresos_kit = df_filtered.loc[df_filtered['producto'] == 'Kit Contado', 'ingresos_totales'].sum()
            ingreso_repo = df_filtered.loc[df_filtered['producto'] == 'Reposicion', 'ingresos_totales'].sum()
            total_ventas = len(df_filtered)    
            vend_activos = df_filtered['nombre_asesor'].nunique()
            total_post = (df_filtered['producto'] == 'Postpago').sum()
            total_kit = (df_filtered['producto'] == 'Kit Contado').sum()
            total_repo = (df_filtered['producto'] == 'Reposicion').sum()
            ticket_post = ingresos_post / total_post if total_post > 0 else 0
            ticket_kit = ingresos_kit / total_kit if total_kit > 0 else 0
            count_financieras = df_filtered['metodo_pago'].count()
            ticket_repo = ingreso_repo / total_repo if total_repo > 0 else 0
        
        
            col1, col2, col3  = st.columns(3)
            with col1:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Ventas Totales</div><div class="metric-value">{total_ventas:,.0f}</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Ventas Post</div><div class="metric-value">{total_post:,}</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Ticket Promedio</div><div class="metric-value">${ticket_post:,.0f}</div></div>', unsafe_allow_html=True)
        
            col4, col5, col6 = st.columns(3)
            with col4:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Vendedores Activos</div><div class="metric-value">{vend_activos:,}</div></div>', unsafe_allow_html=True)
            with col5:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Ventas Kit</div><div class="metric-value">{total_kit:,}</div></div>', unsafe_allow_html=True)    
            with col6:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Ticket Promedio</div><div class="metric-value">${ticket_kit:,.0f}</div></div>', unsafe_allow_html=True)
            
            col7, col8, col9 = st.columns(3)
            with col7:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Ventas Financieras</div><div class="metric-value">{count_financieras:,}</div></div>', unsafe_allow_html=True)
            with col8:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Ventas Repo</div><div class="metric-value">{total_repo:,}</div></div>', unsafe_allow_html=True)    
            with col9:
                st.markdown(f'<div class="metric-card"><div class="metric-title">Ticket Promedio</div><div class="metric-value">${ticket_repo:,.0f}</div></div>', unsafe_allow_html=True)

    with tab2:
        st.subheader("Estadísticas descriptivas")
    with tab3:
        st.subheader("Información del dataset")
