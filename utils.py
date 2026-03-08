import pandas as pd
import streamlit as st
import os

@st.cache_data(ttl=86400)
def cargar_datos_base():
    archivos = ['datos_2018_2022.csv', 'datos_2023_2025.csv', 'datos_2026.csv']
    dfs = []
    
    for archivo in archivos:
        if os.path.exists(archivo):
            df_temp = pd.read_csv(archivo)
            dfs.append(df_temp)
    
    if not dfs:
        return pd.DataFrame()
        
    df = pd.concat(dfs, ignore_index=True)
    df['fecha'] = pd.to_datetime(df['fecha'])
    # Creamos columnas auxiliares para facilitar filtrado
    df['año'] = df['fecha'].dt.year
    df['mes_nombre'] = df['fecha'].dt.month_name()
    df['periodo'] = df['fecha'].dt.to_period('M')
    return df

def obtener_metricas(df_segmento):
    if df_segmento.empty:
        return {k: 0 for k in ['total', 'postpago', 'equipos', 'financiado', 'asesores']}
    
    # Equipos es la suma de estas 3 categorías
    mask_equipos = df_segmento['producto'].isin(['Kit Contado', 'Kit Cuotas', 'Reposicion'])
    
    return {
        'total': len(df_segmento),
        'postpago': (df_segmento['producto'] == 'Postpago').sum(),
        'equipos': mask_equipos.sum(),
        'financiado': df_segmento['metodo_pago'].count(),
        'asesores': df_segmento['nombre_asesor'].nunique()
    }

def calcular_proyeccion(df_mes_actual):
    if df_mes_actual.empty:
        return 0
    ult_dia = df_mes_actual['fecha'].max()
    dias_transcurridos = ult_dia.day
    total_dias_mes = ult_dia.days_in_month
    return total_dias_mes / dias_transcurridos
