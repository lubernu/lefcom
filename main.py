import streamlit as st
import pandas as pd
import glob
import os

# Configuración de la página
st.set_page_config(page_title="Data Assembly", layout="wide")
st.title("📊 Visualizador de Datos Históricos")

@st.cache_data(ttl=3600)  # Cache por 1 hora
def cargar_todos_los_datos():
    """
    Carga y combina todos los archivos CSV de manera eficiente
    """
    # Patrón para encontrar los archivos
    archivos = [
        'data/historico/datos_2018_2022.csv',
        'data/historico/datos_2023_2025.csv',
        'data/diario/datos_2026.csv'
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
        
        # Mostrar resumen en el sidebar
        with st.sidebar:
            st.success(f"📊 **Total registros:** {len(df_completo):,}")
            st.info(f"📁 **Archivos cargados:** {len(dfs)}")
            st.info(f"💾 **Memoria estimada:** {df_completo.memory_usage(deep=True).sum() / 1e6:.2f} MB")
        
        return df_completo
    
    return None

# Cargar datos (solo se ejecuta una vez y se guarda en caché)
df = cargar_todos_los_datos()

if df is not None:
    # Selector de columnas en sidebar
    with st.sidebar:
        st.divider()
        st.subheader("🔧 Configuración")
        
        # Selección de columnas a mostrar
        todas_columnas = df.columns.tolist()
        columnas_seleccionadas = st.multiselect(
            "Columnas a mostrar",
            todas_columnas,
            default=todas_columnas[:5]  # Mostrar primeras 5 por defecto
        )
        
        # Filtro de filas (opcional)
        st.subheader("🎯 Filtros")
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'])
            años = sorted(df['fecha'].dt.year.unique())
            años_seleccionados = st.multiselect("Años", años, default=años[-3:])
    
    # Mostrar datos
    tab1, tab2, tab3 = st.tabs(["📋 Datos", "📈 Estadísticas", "ℹ️ Info"])
    
    with tab1:
        st.subheader("Vista previa de datos")
        
        # Aplicar filtros
        df_display = df.copy()
        if 'fecha' in df.columns and años_seleccionados:
            df_display = df_display[df_display['fecha'].dt.year.isin(años_seleccionados)]
        
        # Mostrar solo columnas seleccionadas
        if columnas_seleccionadas:
            df_display = df_display[columnas_seleccionadas]
        
        # Métricas rápidas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total filas", f"{len(df_display):,}")
        with col2:
            st.metric("Total columnas", len(df_display.columns))
        with col3:
            st.metric("Memoria", f"{df_display.memory_usage(deep=True).sum() / 1e6:.2f} MB")
        
        # Mostrar dataframe con paginación
        st.dataframe(df_display, use_container_width=True)
    
    with tab2:
        st.subheader("Estadísticas descriptivas")
        if columnas_seleccionadas:
            columnas_numericas = df_display.select_dtypes(include=['number']).columns
            if len(columnas_numericas) > 0:
                st.dataframe(df_display[columnas_numericas].describe())
    
    with tab3:
        st.subheader("Información del dataset")
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.write("**Estructura de datos:**")
            info_df = pd.DataFrame({
                'Columna': df.columns,
                'Tipo': df.dtypes.values,
                'No Nulos': df.count().values,
                'Nulos': df.isnull().sum().values
            })
            st.dataframe(info_df, use_container_width=True)
        
        with col_info2:
            st.write("**Muestra de datos (primeras filas):**")
            st.dataframe(df.head(3))
