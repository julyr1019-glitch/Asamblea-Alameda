import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Asamblea Alameda 7 PRO", page_icon="🏢", layout="centered")

# --- 2. MEMORIA GLOBAL ---
@st.cache_resource
def iniciar_servidor():
    return {
        "asamblea_iniciada": False,
        "fase": "espera", 
        "p_idx": 0,
        "votos": pd.DataFrame(columns=["casa", "representa", "p_id", "voto"]),
        "conectados": {}, 
        "tiempo_cierre": None
    }

servidor = iniciar_servidor()
TOTAL_CASAS = 184

# --- 3. PREGUNTAS ---
preguntas = [
    "1. ¿Aprueba la elección del Consejo de Administración por planchas?",
    "2. ¿Aprueba la elección del Comité de Convivencia por planchas?",
    "3. ¿Autoriza la pintura de la fachada de ladrillo?",
    "4. ¿Está de acuerdo con la 'cerca viva' entre etapas?",
    "5. ¿Aprueba el contenido del nuevo Manual de Convivencia?",
    "6. ¿Aprueba el decomiso preventivo de objetos en zonas comunes?",
    "7. ¿Aprueba la cuota extraordinaria para canales de desagüe?",
    "8. ¿Acuerda el encerramiento de la malla del parqueadero?",
    "9. ¿De estas tres opciones de cuota de administración está de acuerdo?",
    "10. ¿Aprueban la App para la votación en la Asamblea General de Alameda 7?"
]
opciones_p9 = ["70.000", "75.000", "85.000"]

# --- 4. LOGO ---
if os.path.exists("image_f94506.jpg"):
    st.image("image_f94506.jpg", use_container_width=True)
else:
    st.title("🏢 Asamblea Alameda 7")

st.divider()

# --- 5. NAVEGACIÓN ---
rol = st.sidebar.radio("SISTEMA DE ASAMBLEA", ["Votante", "Administrador"])

# --- VISTA ADMINISTRADOR ---
if rol == "Administrador":
    st.header("👨‍💼 Panel de Mando (Admin)")
    clave = st.text_input("Contraseña Maestro:", type="password", key="admin_key")
    
    if clave == "Alameda2026*":
        casas_presentes = sum(servidor["conectados"].values())
        porcentaje_quorum = (casas_presentes / TOTAL_CASAS) * 100
        st.subheader(f"📊 Quórum Actual: {porcentaje_quorum:.1f}%")
        st.progress(min(porcentaje_quorum / 100, 1.0))
        
        if not servidor["asamblea_iniciada"]:
            if st.button("🚀 INICIAR ASAMBLEA", type="primary", use_container_width=True, key="btn_init"):
                servidor["asamblea_iniciada"] = True
                st.rerun()
        else:
            sel_p = st.selectbox("Gestionar Pregunta:", range(len(preguntas)), 
                                 index=servidor['p_idx'], format_func=lambda x: preguntas[x], key="sel_preg")
            segundos = st.slider("Segundos de votación:", 30, 300, 60, key="slider_sec")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📢 LANZAR PREGUNTA", type="primary", use_container_width=True, key="btn_lanzar"):
                    servidor['p_idx'] = sel_p
                    servidor['fase'] = "votacion"
                    servidor['tiempo_cierre'] = datetime.now() + timedelta(seconds=segundos)
                    st.rerun()
            with c2:
                if st.button("📊 VER RESULTADOS", use_container_width=True, key="btn_res"):
                    servidor['fase'] = "resultados"
                    st.rerun()

            df_v = servidor['votos']
            votos_act = df_v[df_v['p_id'] == sel_p]
            if not votos_act.empty:
                res_sum = votos_act.groupby('voto')['representa'].sum()
                fig, ax = plt.subplots(figsize=(5,3))
                col = ['#2ecc71', '#e74c3c', '#3498db'] if
