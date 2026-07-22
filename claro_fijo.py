import streamlit as st
from supabase import create_client
from datetime import date
import pandas as pd

# Configuración (credenciales en .streamlit/secrets.toml)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Asignación de Vendedores", layout="centered")
st.title("📋 Gestión de Ventas")

# Cargar vendedores una sola vez (lo usan ambas pestañas)
@st.cache_data(ttl=3600)
def cargar_vendedores():
    vendedores = supabase.table("vendedores").select("cedula, nombre").execute()
    return {v["nombre"]: v["cedula"] for v in vendedores.data}

vendedores_dict = cargar_vendedores()

# ------------------------------
# Función para cargar ventas según estado
# ------------------------------

def cargar_ventas(pendientes=True, año=2026):
    query = supabase.table("ventas").select("*")
    
    # Filtro de mes (junio)
    inicio = date(año, 7, 1)
    fin = date(año, 8, 1)  # 1 de julio (exclusivo)
    query = query.gte("fecha", inicio.isoformat()).lt("fecha", fin.isoformat())
    
    # Filtro de pendientes
    if pendientes:
        query = query.is_("vendedor_cedula", None)
    else:
        query = query.not_.is_("vendedor_cedula", None)
    
    return query.order("fecha", desc=False).execute()
# ------------------------------
# Crear pestañas
# ------------------------------
tab1, tab2 = st.tabs(["📌 Ventas Pendientes", "✅ Ventas Asignadas"])

# ================= PESTAÑA 1: PENDIENTES =================
with tab1:
    st.subheader("Ventas sin vendedor asignado")
    ventas_pendientes = cargar_ventas(pendientes=True)
    
    if not ventas_pendientes.data:
        st.success("✅ No hay ventas pendientes. ¡Todo asignado!")
    else:
        st.info(f"🔔 Hay **{len(ventas_pendientes.data)}** ventas sin vendedor.")
        
        for venta in ventas_pendientes.data:
            titulo = f"🧑‍💼 {venta['nombre_asesor_origen']} - {venta['fecha']} - Cuenta: {venta['cuenta']}"
            with st.expander(titulo):
                st.write(f"**Asesor original:** {venta['nombre_asesor_origen']}")
                st.write(f"**Producto:** {venta['tipo_producto']} | **Valor:** ${venta['valor']}")
                
                nombre_seleccionado = st.selectbox(
                    "Asignar vendedor:",
                    options=list(vendedores_dict.keys()),
                    key=f"select_{venta['id']}"
                )
                
                if st.button("✅ Asignar", key=f"btn_{venta['id']}"):
                    cedula = vendedores_dict[nombre_seleccionado]
                    supabase.table("ventas") \
                        .update({"vendedor_cedula": cedula}) \
                        .eq("id", venta["id"]) \
                        .execute()
                    st.success(f"Asignado a {nombre_seleccionado}")
                    st.rerun()

# ================= PESTAÑA 2: ASIGNADAS =================
with tab2:
    st.subheader("Ventas con vendedor asignado")
    ventas_asignadas = cargar_ventas(pendientes=False)
    
    if not ventas_asignadas.data:
        st.info("Aún no hay ventas asignadas.")
    else:
        # Convertir a DataFrame para mostrar tabla
        df_asignadas = pd.DataFrame(ventas_asignadas.data)
        
        # Agregar columna con el nombre del vendedor (haciendo JOIN con vendedores)
        # Como vendedores_dict es {nombre: cedula}, necesitamos mapear inversamente
        cedula_a_nombre = {v: k for k, v in vendedores_dict.items()}
        df_asignadas["vendedor_nombre"] = df_asignadas["vendedor_cedula"].map(cedula_a_nombre)
        
        # Seleccionar y renombrar columnas para mostrar
        columnas_mostrar = {
            "id": "ID",
            "fecha": "Fecha",
            "cuenta": "Cuenta",
            "nombre_asesor_origen": "Asesor Original",
            "tipo_producto": "Producto",
            "valor": "Valor",
            "vendedor_nombre": "Vendedor Asignado"
        }
        df_display = df_asignadas[list(columnas_mostrar.keys())].rename(columns=columnas_mostrar)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Opcional: botón para descargar CSV
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar asignadas como CSV",
            data=csv,
            file_name="ventas_asignadas.csv",
            mime="text/csv",
        ) 

# ================= SECCIÓN ADMINISTRATIVA (solo para ti) =================
with st.expander("🔐 Panel de Administración (corrección de asignaciones)"):
    password = st.text_input("Contraseña de administrador", type="password", key="admin_pass")
    if password == "lefcom2026*":
        st.success("Acceso concedido. Puedes modificar el vendedor de cualquier venta.")
        
        # Cargar todas las ventas (sin filtrar)
        todas_ventas = supabase.table("ventas").select("*").order("id").execute()
        if not todas_ventas.data:
            st.info("No hay ventas en la base de datos.")
        else:
            df_todas = pd.DataFrame(todas_ventas.data)
            
            # Mapeo inverso (cédula -> nombre)
            cedula_a_nombre = {v: k for k, v in vendedores_dict.items()}
            df_todas["vendedor_nombre"] = df_todas["vendedor_cedula"].map(cedula_a_nombre)
            
            # Mostrar cada venta en una tarjeta
            for idx, venta in df_todas.iterrows():
                with st.container(border=True):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**ID:** {venta['id']} | **Cuenta:** {venta['cuenta']} | **Fecha:** {venta['fecha']}")
                        st.write(f"**Asesor original:** {venta['nombre_asesor_origen']}")
                        st.write(f"**Producto:** {venta['tipo_producto']} | **Valor:** ${venta['valor']}")
                        estado = venta['vendedor_nombre'] if venta['vendedor_nombre'] else "🔴 Sin asignar"
                        st.write(f"**Vendedor actual:** {estado}")
                    
                    with col2:
                        # Preparar opciones del desplegable
                        opciones = ["(Sin asignar)"] + list(vendedores_dict.keys())
                        # Encontrar el índice actual
                        valor_actual = venta['vendedor_nombre']
                        indice_default = 0
                        if valor_actual in opciones:
                            indice_default = opciones.index(valor_actual)
                        
                        nuevo_vendedor = st.selectbox(
                            "Cambiar a:",
                            options=opciones,
                            index=indice_default,
                            key=f"admin_sel_{venta['id']}"
                        )
                        
                        if st.button("Actualizar", key=f"admin_btn_{venta['id']}"):
                            # Calcular nueva cédula (None si es "Sin asignar")
                            nueva_cedula = None if nuevo_vendedor == "(Sin asignar)" else vendedores_dict[nuevo_vendedor]
                            supabase.table("ventas") \
                                .update({"vendedor_cedula": nueva_cedula}) \
                                .eq("id", venta["id"]) \
                                .execute()
                            st.success(f"✅ Venta ID {venta['id']} actualizada correctamente.")
                            st.rerun()
    elif password:
        st.error("❌ Contraseña incorrecta")
