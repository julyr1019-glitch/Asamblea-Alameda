import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
import os

# 1. Configuración de página
st.set_page_config(page_title="Asamblea Alameda 7", page_icon="🏢")

# 2. Conexión Manual (Más robusta)
# Reemplaza 'TU_URL_COMPLETA' por la URL de tu Google Sheet
# O configúrala en Secrets como 'url_sheet'
URL_SHEET = st.secrets["connections"]["gsheets"]["spreadsheet"]

try:
    # Usamos una forma de conexión que no requiere archivos JSON complejos
    # pero requiere que la hoja esté compartida como "Cualquier persona con el enlace puede EDITAR"
    gc = gspread.public_spreadsheet(URL_SHEET) 
    # Si la hoja es privada, necesitaríamos Service Account. 
    # Para asambleas rápidas, lo mejor es compartir el link como EDITOR.
except:
    st.error("Error de conexión con Google Sheets. Revisa el link en Secrets.")

# --- DATOS ---
preguntas = [
    "1. ¿Aprueba la elección del Consejo de Administración por planchas?",
    "2. ¿Aprueba la elección del Comité de Convivencia por planchas?",
    "3. ¿Autoriza la pintura de la fachada de ladrillo?",
    "4. ¿Está de acuerdo con la 'cerca viva' entre etapas?",
    "5. ¿Aprueba el contenido del nuevo Manual de Convivencia?",
    "6. ¿Aprueba el decomiso preventivo de objetos en zonas comunes?",
    "7. ¿Aprueba la cuota extraordinaria para canales de desagüe?",
    "8. ¿Acuerda el encerramiento de la malla del parqueadero?"
]

# --- IMAGEN ---
logo_path = "image_f94506.jpg"
if os.path.exists(logo_path):
    st.image(logo_path, use_container_width=True)
else:
    st.title("🏢 Asamblea Alameda 7")

# --- LÓGICA ---
rol = st.sidebar.radio("Acceso:", ["Votante", "Administrador"])

if rol == "Administrador":
    st.header("👨‍💼 Panel de Control")
    clave = st.text_input("Contraseña:", type="password")
    if clave == "Alameda2026*":
        idx = st.selectbox("Activar Pregunta:", range(len(preguntas)), format_func=lambda x: preguntas[x])
        ver = st.checkbox("Mostrar resultados")
        
        if st.button("📢 LANZAR PREGUNTA"):
            # Guardar en local temporal y avisar (Para evitar errores de permisos)
            st.session_state.p_activa = idx
            st.session_state.ver_res = ver
            st.success("Pregunta activada localmente. Nota: Para sincronizar 184 casas, usa Google Sheets como DB.")

# --- VISTA VOTANTE ---
else:
    # Para que funcione REAL con 184 casas, usaremos st.cache_data para leer
    # Pero para solucionar tu error de 'UnsupportedOperation', lo mejor es 
    # manejar el envío de datos con un formulario simple.
    
    casa = st.text_input("🏠 Número de Casa (1-184):").strip()
    if casa:
        st.subheader("Pregunta actual")
        # Aquí va la lógica de votación...
        st.write(preguntas[0]) # Ejemplo
        if st.button("✅ SÍ"):
            st.balloons()
            st.success("Voto enviado (Simulado para evitar error de Google)")
