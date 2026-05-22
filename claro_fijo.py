import streamlit as st
from supabase import create_client
import pandas as pd

# Configuración (guarda estas credenciales en .streamlit/secrets.toml)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Asignación de Vendedores", layout="centered")
st.title("📋 Ventas pendientes de asignar")

# Cargar ventas sin vendedor (solo las no asignadas)
ventas_pendientes = supabase.table("ventas") \
    .select("*") \
    .is_("vendedor_cedula", None)
    .execute()

# Cargar vendedores para el desplegable
vendedores = supabase.table("vendedores") \
    .select("cedula, nombre") \
    .execute()

vendedores_dict = {v["nombre"]: v["cedula"] for v in vendedores.data}

if not ventas_pendientes.data:
    st.success("✅ No hay ventas pendientes. ¡Todo asignado!")
    st.stop()

st.info(f"🔔 Hay **{len(ventas_pendientes.data)}** ventas sin vendedor.")

# Mostrar cada venta en una tarjeta
for venta in ventas_pendientes.data:
    with st.expander(f"Venta ID {venta['id']} - {venta['fecha']} - {venta['cuenta']}"):
        st.write(f"**Asesor original:** {venta['nombre_asesor_origen']}")
        st.write(f"**Producto:** {venta['tipo_producto']} | **Valor:** ${venta['valor']}")
        
        # Desplegable
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
            st.rerun()  # Recarga la página para que desaparezca la venta asignada 
