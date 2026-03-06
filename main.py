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

if df is not None:
    # Selector de columnas en sidebar
    with st.sidebar:
        st.subheader("🎯 Filtros")
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'])
            años = sorted(df['fecha'].dt.year.unique())
            
    
    # Mostrar datos
    tab1, tab2, tab3 = st.tabs(["📋 Datos", "📈 Estadísticas", "ℹ️ Info"])
    
    with tab1:
        st.subheader("Vista previa de datos")
    
    with tab2:
        st.subheader("Estadísticas descriptivas")
    with tab3:
        st.subheader("Información del dataset")
