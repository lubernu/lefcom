'''import streamlit as st
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
            st.rerun()  # Recarga la página para que desaparezca la venta asignada '''

import streamlit as st
from supabase import create_client

# ==========================================
# Configuración
# ==========================================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🔍 DIAGNÓSTICO - Ventas pendientes")

# ------------------------------------------------------------
# 1. Ver todas las filas (sin filtro) y mostrar las primeras 5
# ------------------------------------------------------------
try:
    respuesta_todas = supabase.table("ventas").select("*").limit(5).execute()
    st.subheader("📌 Primeras 5 filas de la tabla 'ventas'")
    st.dataframe(respuesta_todas.data)
except Exception as e:
    st.error(f"Error al consultar todas las ventas: {e}")

# ------------------------------------------------------------
# 2. Contar total de filas
# ------------------------------------------------------------
try:
    conteo_total = supabase.table("ventas").select("*", count="exact").execute()
    st.write(f"**Total de registros en ventas:** {conteo_total.count}")
except Exception as e:
    st.error(f"Error en conteo total: {e}")

# ------------------------------------------------------------
# 3. Contar ventas con vendedor_cedula = NULL (usando .is_ con None)
# ------------------------------------------------------------
try:
    pendientes_is = supabase.table("ventas") \
        .select("*", count="exact") \
        .is_("vendedor_cedula", None) \
        .execute()
    st.write(f"**Ventas con vendedor_cedula = NULL (usando .is_ con None):** {pendientes_is.count}")
except Exception as e:
    st.error(f"Error en filtro .is_ con None: {e}")

# ------------------------------------------------------------
# 4. Contar ventas con vendedor_cedula = 'null' (como texto)
# ------------------------------------------------------------
try:
    pendientes_texto = supabase.table("ventas") \
        .select("*", count="exact") \
        .eq("vendedor_cedula", "null") \
        .execute()
    st.write(f"**Ventas con vendedor_cedula = 'null' (texto):** {pendientes_texto.count}")
except Exception as e:
    st.error(f"Error en filtro eq('null'): {e}")

# ------------------------------------------------------------
# 5. Contar ventas con vendedor_cedula = cadena vacía ''
# ------------------------------------------------------------
try:
    pendientes_vacio = supabase.table("ventas") \
        .select("*", count="exact") \
        .eq("vendedor_cedula", "") \
        .execute()
    st.write(f"**Ventas con vendedor_cedula = '' (vacío):** {pendientes_vacio.count}")
except Exception as e:
    st.error(f"Error en filtro eq(''): {e}")

# ------------------------------------------------------------
# 6. Mostrar valores únicos de vendedor_cedula (para ver qué hay)
# ------------------------------------------------------------
try:
    valores_unicos = supabase.table("ventas") \
        .select("vendedor_cedula") \
        .execute()
    valores = list(set([fila["vendedor_cedula"] for fila in valores_unicos.data]))
    st.write("**Valores únicos en columna vendedor_cedula:**", valores)
except Exception as e:
    st.error(f"Error al obtener valores únicos: {e}")


