import streamlit as st
from supabase import create_client
from datetime import date
import pandas as pd

# Configuración (credenciales en .streamlit/secrets.toml)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "lefcom2026*")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Asignación de Vendedores",  layout="wide")
st.title("📋 Gestión de Ventas")

# -------------------------------------------------------------
# Funciones de consulta directa (Sin caché para datos en vivo)
# -------------------------------------------------------------

def cargar_vendedores():
    """Consulta la lista de vendedores directamente de Supabase en cada ejecución."""
    vendedores = supabase.table("vendedores").select("cedula, nombre").execute()
    return {v["nombre"]: v["cedula"] for v in vendedores.data}

def cargar_ventas(pendientes=True, año=2026):
    """Consulta las ventas filtradas por mes y estado de asignación."""
    query = supabase.table("ventas").select("*")
    
    # Filtro de mes (Agosto)
    inicio = date(año, 8, 1)
    fin = date(año, 9, 1)  # 1 de septiembre (exclusivo)
    query = query.gte("fecha", inicio.isoformat()).lt("fecha", fin.isoformat())
    
    # Filtro de asignación
    if pendientes:
        query = query.is_("vendedor_cedula", None)
    else:
        query = query.not_.is_("vendedor_cedula", None)
    
    return query.order("fecha", desc=False).execute()

# Obtener vendedores actualizados
vendedores_dict = cargar_vendedores()
cedula_a_nombre = {v: k for k, v in vendedores_dict.items()}

# -------------------------------------------------------------
# Interfaz de Usuario
# -------------------------------------------------------------
tab1, tab2 = st.tabs(["📌 Ventas Pendientes", "✅ Ventas Asignadas"])

# ================= PESTAÑA 1: PENDIENTES =================
with tab1:
    st.subheader("Ventas sin vendedor asignado")
    ventas_pendientes = cargar_ventas(pendientes=True)
    
    if not ventas_pendientes.data:
        st.success("✅ No hay ventas pendientes. ¡Todo asignado!")
    else:
        df_pendientes = pd.DataFrame(ventas_pendientes.data)
        asesores_origen = df_pendientes["nombre_asesor_origen"].unique()
        
        st.info(f"🔔 Hay **{len(df_pendientes)}** ventas pendientes, agrupadas en **{len(asesores_origen)}** asesores originales.")
        
        for asesor in asesores_origen:
            df_asesor = df_pendientes[df_pendientes["nombre_asesor_origen"] == asesor].copy()
            titulo = f"🧑‍💼 {asesor} ({len(df_asesor)} ventas pendientes)"
            
            with st.expander(titulo):
                df_asesor["vendedor_asignado"] = None 
                
                columnas_mostrar = ["id", "fecha", "cuenta", "tipo_producto", "valor", "vendedor_asignado"]
                df_mostrar = df_asesor[columnas_mostrar]
                
                edited_df = st.data_editor(
                    df_mostrar,
                    column_config={
                        "id": "ID",
                        "fecha": "Fecha",
                        "cuenta": "Cuenta",
                        "tipo_producto": "Producto",
                        "valor": st.column_config.NumberColumn("Valor", format="$%d"),
                        "vendedor_asignado": st.column_config.SelectboxColumn(
                            "Asignar a:",
                            help="Selecciona el vendedor final de la lista",
                            options=list(vendedores_dict.keys()),
                            required=False
                        )
                    },
                    disabled=["id", "fecha", "cuenta", "tipo_producto", "valor"], 
                    hide_index=True,
                    use_container_width=True,
                    key=f"editor_{asesor}"
                )
                
                if st.button("✅ Guardar asignaciones", key=f"btn_guardar_{asesor}"):
                    asignaciones = edited_df.dropna(subset=["vendedor_asignado"])
                    
                    if not asignaciones.empty:
                        for _, row in asignaciones.iterrows():
                            cedula = vendedores_dict[row["vendedor_asignado"]]
                            supabase.table("ventas") \
                                .update({"vendedor_cedula": cedula}) \
                                .eq("id", row["id"]) \
                                .execute()
                        
                        st.success(f"Se asignaron {len(asignaciones)} ventas de {asesor} correctamente.")
                        st.rerun()
                    else:
                        st.warning("⚠️ No has seleccionado ningún vendedor para asignar.")

# ================= PESTAÑA 2: ASIGNADAS =================
with tab2:
    st.subheader("Ventas con vendedor asignado")
    ventas_asignadas = cargar_ventas(pendientes=False)
    
    if not ventas_asignadas.data:
        st.info("Aún no hay ventas asignadas.")
    else:
        df_asignadas = pd.DataFrame(ventas_asignadas.data)
        df_asignadas["vendedor_nombre"] = df_asignadas["vendedor_cedula"].map(cedula_a_nombre)
        
        # ✅ Crear columna consecutiva que empieza en 1
        df_asignadas["N°"] = range(1, len(df_asignadas) + 1)
        
        columnas_mostrar = {
            "N°": "N°",                    # <-- Ahora usa el consecutivo
            "fecha": "Fecha",
            "cuenta": "Cuenta",
            "nombre_asesor_origen": "Asesor Original",
            "tipo_producto": "Producto",
            "valor": "Valor",
            "vendedor_nombre": "Vendedor Asignado"
        }
        df_display = df_asignadas[list(columnas_mostrar.keys())].rename(columns=columnas_mostrar)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar asignadas como CSV",
            data=csv,
            file_name="ventas_asignadas.csv",
            mime="text/csv",
        )

# ================= SECCIÓN ADMINISTRATIVA =================
with st.expander("🔐 Panel de Administración (corrección de asignaciones)"):
    password = st.text_input("Contraseña de administrador", type="password", key="admin_pass")
    
    if password == ADMIN_PASSWORD:
        st.success("Acceso concedido. Puedes modificar el vendedor de cualquier venta.")
        
        todas_ventas = supabase.table("ventas").select("*").order("id").execute()
        
        if not todas_ventas.data:
            st.info("No hay ventas en la base de datos.")
        else:
            df_todas = pd.DataFrame(todas_ventas.data)
            df_todas["vendedor_nombre"] = df_todas["vendedor_cedula"].map(cedula_a_nombre)
            
            for idx, venta in df_todas.iterrows():
                with st.container(border=True):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**ID:** {venta['id']} | **Cuenta:** {venta['cuenta']} | **Fecha:** {venta['fecha']}")
                        st.write(f"**Asesor original:** {venta['nombre_asesor_origen']}")
                        st.write(f"**Producto:** {venta['tipo_producto']} | **Valor:** ${venta['valor']}")
                        estado = venta['vendedor_nombre'] if pd.notna(venta['vendedor_nombre']) else "🔴 Sin asignar"
                        st.write(f"**Vendedor actual:** {estado}")
                    
                    with col2:
                        opciones = ["(Sin asignar)"] + list(vendedores_dict.keys())
                        valor_actual = venta['vendedor_nombre']
                        indice_default = opciones.index(valor_actual) if valor_actual in opciones else 0
                        
                        nuevo_vendedor = st.selectbox(
                            "Cambiar a:",
                            options=opciones,
                            index=indice_default,
                            key=f"admin_sel_{venta['id']}"
                        )
                        
                        if st.button("Actualizar", key=f"admin_btn_{venta['id']}"):
                            nueva_cedula = None if nuevo_vendedor == "(Sin asignar)" else vendedores_dict[nuevo_vendedor]
                            supabase.table("ventas") \
                                .update({"vendedor_cedula": nueva_cedula}) \
                                .eq("id", venta["id"]) \
                                .execute()
                                
                            st.success(f"✅ Venta ID {venta['id']} actualizada correctamente.")
                            st.rerun()
    elif password:
        st.error("❌ Contraseña incorrecta")
