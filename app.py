import streamlit as st
import pandas as pd
import os

# 1. Configuración de pantalla
st.set_page_config(page_title="Asamblea Alameda 7", page_icon="🏢")

# --- INICIALIZACIÓN DE MEMORIA (Session State) ---
if 'db_votos' not in st.session_state:
    st.session_state.db_votos = pd.DataFrame(columns=["casa", "pregunta", "voto"])

if 'p_activa' not in st.session_state:
    st.session_state.p_activa = 0

if 'ver_resultados' not in st.session_state:
    st.session_state.ver_resultados = False

if 'casa_identificada' not in st.session_state:
    st.session_state.casa_identificada = None

# --- PREGUNTAS OFICIALES ---
preguntas = [
    "1. ¿Aprueba la elección del Consejo de Administración por planchas?",
    "2. ¿Aprueba la elección del Comité de Convivencia por planchas?",
    "3. ¿Autoriza la pintura de la fachada de ladrillo (sujeto a recursos)?",
    "4. ¿Está de acuerdo con la 'cerca viva' entre etapas (sujeto a recursos)?",
    "5. ¿Aprueba el contenido del nuevo Manual de Convivencia?",
    "6. ¿Aprueba el decomiso preventivo de objetos en zonas comunes?",
    "7. ¿Aprueba la cuota extraordinaria para canales de desagüe?",
    "8. ¿Acuerda el encerramiento de la malla del parqueadero?"
]

# --- CABECERA CON LOGO ---
logo_path = "image_f94506.jpg"
if os.path.exists(logo_path):
    st.image(logo_path, use_container_width=True)
else:
    st.title("🏢 Asamblea Alameda 7")

st.divider()

# --- NAVEGACIÓN ---
rol = st.sidebar.radio("Menú de Acceso:", ["Votante", "Administrador"])

# --- VISTA ADMINISTRADOR ---
if rol == "Administrador":
    st.header("👨‍💼 Panel de Control")
    clave = st.text_input("Contraseña Maestro:", type="password")
    
    if clave == "Alameda2026*":
        st.success("Control de Asamblea Activado")
        
        # El Admin elige qué pregunta se muestra a TODOS
        st.session_state.p_activa = st.selectbox(
            "Seleccionar Pregunta para lanzar:", 
            range(len(preguntas)), 
            index=st.session_state.p_activa,
            format_func=lambda x: preguntas[x]
        )
        
        st.session_state.ver_resultados = st.checkbox(
            "Publicar Gráficos de Resultados", 
            value=st.session_state.ver_resultados
        )
        
        st.info(f"Actualmente todos ven la Pregunta {st.session_state.p_activa + 1}")
        
        st.divider()
        st.subheader("📊 Reporte de Votos")
        if not st.session_state.db_votos.empty:
            st.dataframe(st.session_state.db_votos)
            csv = st.session_state.db_votos.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Excel de Votación", data=csv, file_name="votos_asamblea.csv")
        else:
            st.write("Aún no hay registros.")

# --- VISTA VOTANTE ---
else:
    # PASO 1: Identificación (Solo se pide una vez)
    if st.session_state.casa_identificada is None:
        st.subheader("Identificación de Copropietario")
        casa_input = st.text_input("🏠 Por favor, ingrese su Número de Casa (1-184):", key="input_casa").strip()
        if st.button("Ingresar a la Asamblea"):
            if casa_input:
                st.session_state.casa_identificada = casa_input
                st.rerun()
            else:
                st.error("Debe ingresar un número de casa.")
    
    # PASO 2: Votación (Una vez identificado)
    else:
        casa = st.session_state.casa_identificada
        p_idx = st.session_state.p_activa
        pregunta_texto = preguntas[p_idx]
        
        st.sidebar.write(f"🏠 Casa: **{casa}**")
        if st.sidebar.button("Cambiar de Casa / Salir"):
            st.session_state.casa_identificada = None
            st.rerun()

        st.subheader(f"Pregunta {p_idx + 1}")
        st.markdown(f"### {pregunta_texto}")
        
        # Verificar si ya votó
        df = st.session_state.db_votos
        ya_voto = not df[(df['casa'] == casa) & (df['pregunta'] == pregunta_texto)].empty
        
        if st.session_state.ver_resultados:
            st.success("📊 Votación Cerrada. Resultados en pantalla:")
            resumen = df[df['pregunta'] == pregunta_texto]['voto'].value_counts()
            if not resumen.empty:
                st.bar_chart(resumen)
            else:
                st.write("No se registraron votos.")
        
        elif ya_voto:
            st.warning(f"Su voto (Casa {casa}) ya fue registrado. Por favor, espere a que el administrador lance la siguiente pregunta.")
            if st.button("🔄 Verificar nueva pregunta"):
                st.rerun()
        
        else:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ SÍ", use_container_width=True):
                    nuevo = pd.DataFrame([{"casa": casa, "pregunta": pregunta_texto, "voto": "SÍ"}])
                    st.session_state.db_votos = pd.concat([st.session_state.db_votos, nuevo], ignore_index=True)
                    st.balloons()
                    st.rerun()
            with col2:
                if st.button("❌ NO", use_container_width=True):
                    nuevo = pd.DataFrame([{"casa": casa, "pregunta": pregunta_texto, "voto": "NO"}])
                    st.session_state.db_votos = pd.concat([st.session_state.db_votos, nuevo], ignore_index=True)
                    st.rerun()
