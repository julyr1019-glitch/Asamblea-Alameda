import streamlit as st
import pandas as pd
import os

# --- CONFIGURACIÓN DE ARCHIVOS ---
# Estos archivos guardan la memoria de la asamblea en el servidor
ARCHIVO_VOTOS = "votos_alameda.csv"
ARCHIVO_CONTROL = "control_asamblea.txt"

def inicializar_archivos():
    if not os.path.exists(ARCHIVO_VOTOS):
        pd.DataFrame(columns=["casa", "pregunta", "voto"]).to_csv(ARCHIVO_VOTOS, index=False)
    if not os.path.exists(ARCHIVO_CONTROL):
        with open(ARCHIVO_CONTROL, "w") as f:
            f.write("0|False") # Pregunta 0, Resultados ocultos

def guardar_control(id_p, ver_res):
    with open(ARCHIVO_CONTROL, "w") as f:
        f.write(f"{id_p}|{ver_res}")

def leer_control():
    if not os.path.exists(ARCHIVO_CONTROL):
        return 0, False
    with open(ARCHIVO_CONTROL, "r") as f:
        data = f.read().split("|")
        return int(data[0]), data[1] == "True"

# --- INICIO DE APP ---
st.set_page_config(page_title="Asamblea Alameda 7", page_icon="🏢")
inicializar_archivos()

# Preguntas
preguntas = [
    "1. ¿Aprueba la elección del Consejo de Administración por planchas?",
    "2. ¿Aprueba la elección del Comité de Convivencia por planchas?",
    "3. ¿Autoriza la pintura de la fachada de ladrillo?",
    "4. ¿Está de acuerdo con la 'cerca viva'?",
    "5. ¿Aprueba el nuevo Manual de Convivencia?",
    "6. ¿Aprueba el decomiso preventivo de objetos?",
    "7. ¿Aprueba cuota extraordinaria para canales?",
    "8. ¿Acuerda el encerramiento de la malla del parqueadero?"
]

# Logo
if os.path.exists("image_f94506.jpg"):
    st.image("image_f94506.jpg", use_container_width=True)

st.divider()

# Navegación
rol = st.sidebar.radio("MENÚ PRINCIPAL", ["Votante (Vecino)", "Administrador"])

# --- VISTA ADMINISTRADOR ---
if rol == "Administrador":
    st.header("👨‍💼 Panel de Mando")
    clave = st.text_input("Contraseña de Acceso:", type="password")
    
    if clave == "Alameda2026*":
        st.success("Conectado como Administrador")
        
        # Leemos el estado actual para que el selector no se mueva solo
        p_actual, res_actual = leer_control()
        
        st.subheader("Control de la Asamblea")
        nueva_p = st.selectbox("1. Seleccionar Pregunta:", range(len(preguntas)), index=p_actual, format_func=lambda x: preguntas[x])
        mostrar_graficos = st.checkbox("2. ¿Mostrar resultados a los vecinos?", value=res_actual)
        
        # BOTÓN MAESTRO
        if st.button("🚀 ACTUALIZAR PARA TODOS LOS CELULARES", type="primary", use_container_width=True):
            guardar_control(nueva_p, mostrar_graficos)
            st.toast("¡Sincronizando con todos los dispositivos!")
            st.rerun()

        st.divider()
        st.subheader("📥 Reporte de Votos")
        df_votos = pd.read_csv(ARCHIVO_VOTOS)
        if not df_votos.empty:
            st.dataframe(df_votos.tail(10)) # Muestra los últimos 10 votos
            csv = df_votos.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar Excel de Votos", data=csv, file_name="votos_alameda.csv")
        
        if st.button("⚠️ REINICIAR TODA LA VOTACIÓN (BORRAR TODO)"):
            pd.DataFrame(columns=["casa", "pregunta", "voto"]).to_csv(ARCHIVO_VOTOS, index=False)
            guardar_control(0, False)
            st.rerun()

# --- VISTA VOTANTE ---
else:
    # 1. Leer qué orden dio el administrador
    p_activa_id, ver_resultados = leer_control()
    
    # 2. Pedir identificación una sola vez
    if 'mi_casa' not in st.session_state:
        st.subheader("Bienvenido")
        casa_input = st.text_input("🏠 Ingrese su Número de Casa:").strip()
        if st.button("Entrar a Votar", use_container_width=True):
            if casa_input:
                st.session_state.mi_casa = casa_input
                st.rerun()
    else:
        casa = st.session_state.mi_casa
        st.sidebar.info(f"Sesión iniciada: Casa {casa}")
        if st.sidebar.button("Cerrar Sesión"):
            del st.session_state.mi_casa
            st.rerun()

        # 3. Mostrar la pregunta actual
        st.subheader(f"Pregunta {p_activa_id + 1}")
        st.markdown(f"**{preguntas[p_activa_id]}**")
        
        # Consultar votos reales
        df_votos = pd.read_csv(ARCHIVO_VOTOS)
        ya_voto = not df_votos[(df_votos['casa'].astype(str) == casa) & (df_votos['pregunta'] == preguntas[p_activa_id])].empty
        
        if ver_resultados:
            st.success("📊 Resultados en Vivo")
            resumen = df_votos[df_votos['pregunta'] == preguntas[p_activa_id]]['voto'].value_counts()
            if not resumen.empty:
                st.bar_chart(resumen)
            else:
                st.write("No hay votos registrados para esta pregunta.")
            if st.button("🔄 Actualizar"): st.rerun()

        elif ya_voto:
            st.warning(f"Casa {casa}, su voto ya fue recibido. Por favor, espere la siguiente pregunta.")
            if st.button("🔄 Buscar Nueva Pregunta"): st.rerun()
        
        else:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ SÍ", use_container_width=True):
                    nuevo = pd.DataFrame([{"casa": casa, "pregunta": preguntas[p_activa_id], "voto": "SÍ"}])
                    nuevo.to_csv(ARCHIVO_VOTOS, mode='a', header=False, index=False)
                    st.balloons()
                    st.rerun()
            with col2:
                if st.button("❌ NO", use_container_width=True):
                    nuevo = pd.DataFrame([{"casa": casa, "pregunta": preguntas[p_activa_id], "voto": "NO"}])
                    nuevo.to_csv(ARCHIVO_VOTOS, mode='a', header=False, index=False)
                    st.rerun()
