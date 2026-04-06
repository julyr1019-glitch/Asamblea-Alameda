import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Configuración de Preguntas
preguntas = [
    "1. ¿Aprueba la elección del Consejo de Administración por planchas?",
    "2. ¿Aprueba la elección del Comité de Convivencia por planchas?",
    "3. ¿Autoriza la pintura de la fachada de ladrillo?",
    "4. ¿Está de acuerdo con la 'cerca viva' entre etapas?",
    "5. ¿Aprueba el contenido del nuevo Manual de Convivencia?",
    "6. ¿Aprueba el decomiso preventivo de objetos en zonas comunes?",
    "7. ¿Aprueba cuota extraordinaria para canales de desagüe?",
    "8. ¿Acuerda el encerramiento de la malla del parqueadero?"
]

st.title("🏛️ Asamblea Virtual 2026")

# --- LÓGICA DE NAVEGACIÓN ---
rol = st.sidebar.radio("Seleccione su Rol:", ["Copropietario", "Administrador"])

# --- VISTA ADMINISTRADOR ---
if rol == "Administrador":
    st.subheader("👨‍💼 Panel de Control")
    clave = st.text_input("Contraseña de Admin", type="password")
    
    if clave == "admin2026":
        # Selección de pregunta activa
        idx = st.selectbox("Activar Pregunta para todos:", range(len(preguntas)), format_func=lambda x: preguntas[x])
        
        if st.button("🚀 LANZAR PREGUNTA"):
            # Actualizamos la celda A2 de la hoja 'Control' con el número de la pregunta
            df_control = pd.DataFrame({"pregunta_activa": [idx]})
            conn.update(worksheet="Control", data=df_control)
            st.success(f"Pregunta {idx + 1} activada en todos los celulares.")

# --- VISTA VOTANTE ---
else:
    # 1. Leer qué pregunta está activa desde la nube
    try:
        df_status = conn.read(worksheet="Control", ttl=2) # ttl=2 para que actualice rápido
        p_activa = int(df_status.iloc[0, 0])
    except:
        p_activa = -1 # Si no hay nada iniciado

    if p_activa == -1:
        st.warning("☕ Esperando a que el Administrador inicie la asamblea...")
        if st.button("🔄 Verificar inicio"): st.rerun()
    else:
        st.info(f"Pregunta actual: {p_activa + 1} de {len(preguntas)}")
        st.subheader(preguntas[p_activa])
        
        # Pedir identificación
        casa = st.text_input("🏠 Número de Casa (1-184):", placeholder="Ej: 45")
        
        if casa:
            # 2. Verificar si ya votó en esta pregunta
            df_votos = conn.read(worksheet="Votos", ttl=0)
            ya_voto = not df_votos[(df_votos['casa'].astype(str) == casa) & 
                                   (df_votos['pregunta'] == preguntas[p_activa])].empty
            
            if ya_voto:
                st.error(f"La casa {casa} ya registró su voto. Espere a la siguiente pregunta.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ SÍ", use_container_width=True):
                        # Enviar a Google Sheets
                        nuevo_voto = pd.DataFrame([{"casa": casa, "pregunta": preguntas[p_activa], "voto": "SÍ"}])
                        df_final = pd.concat([df_votos, nuevo_voto])
                        conn.update(worksheet="Votos", data=df_final)
                        st.success("Voto 'SÍ' registrado correctamente.")
                        st.balloons()
                with col2:
                    if st.button("❌ NO", use_container_width=True):
                        nuevo_voto = pd.DataFrame([{"casa": casa, "pregunta": preguntas[p_activa], "voto": "NO"}])
                        df_final = pd.concat([df_votos, nuevo_voto])
                        conn.update(worksheet="Votos", data=df_final)
                        st.success("Voto 'NO' registrado correctamente.")
