import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Asamblea Alameda 7 - Gestión", 
    page_icon="🏢", 
    layout="centered",
    initial_sidebar_state="expanded"
)

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

# --- 3. CSS DIFERENCIADO POR ROL ---
rol = st.sidebar.radio("SISTEMA", ["Votante", "Administrador"], key="nav_final_fixed")

if rol == "Votante":
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        header {visibility: hidden !important;}
        .stDeployButton {display:none !important;}
        [data-testid="stHeader"] {display:none !important;}
        .titulo-v { font-size: 42px !important; font-weight: bold; text-align: center; line-height: 1.2; padding: 20px 0; }
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown("""<style>footer {visibility: hidden !important;} .stDeployButton {display:none !important;}</style>""", unsafe_allow_html=True)

# --- 4. PREGUNTAS ---
preguntas = [
    "¿Logró revisar el contenido de la cartilla para la Asamblea del 19 de Abril de 2026?",
    "¿Delegará poder a un tercero que asista a la Asamblea General?",
    "¿Cuenta con dispositivo móvil para asistir a la asamblea General?",
    "¿Cuenta ud con datos móviles para la participación en la Asamblea General?",
    "¿Tiene dudas acerca de la votación electrónica?",
    "¿Desea que la administración se contacte con ud para resolver sus inquietudes?"
]

# --- 5. LOGO ---
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    if os.path.exists("image_f94506.jpg"):
        st.image("image_f94506.jpg", width=180)
    else:
        st.title("🏢 Alameda 7")

st.divider()

# --- VISTA ADMINISTRADOR ---
if rol == "Administrador":
    st.header("👨‍💼 Panel de Control (Admin)")
    clave = st.text_input("Contraseña Maestro:", type="password", key="pwd_fixed")
    
    if clave == "Alameda2026*":
        st.sidebar.subheader("🛠️ Herramientas")
        if st.sidebar.button("🔄 ACTUALIZAR (RERUN)", use_container_width=True):
            st.rerun()
        if st.sidebar.button("🧹 REINICIAR DATA TOTAL", type="secondary", use_container_width=True):
            servidor["votos"] = pd.DataFrame(columns=["casa", "representa", "p_id", "voto"])
            servidor["conectados"] = {}
            servidor["asamblea_iniciada"] = False
            st.rerun()

        casas_presentes = sum(servidor["conectados"].values())
        porcentaje_quorum = (casas_presentes / TOTAL_CASAS) * 100
        
        st.subheader("📊 Control de Asistencia")
        cm1, cm2 = st.columns(2)
        cm1.metric("Quórum", f"{porcentaje_quorum:.1f}%")
        cm2.metric("Casas Registradas", f"{len(servidor['conectados'])}")
        st.progress(min(porcentaje_quorum / 100, 1.0))

        with st.expander("🏠 VER LISTADO DE ASISTENCIA DETALLADO"):
            if servidor["conectados"]:
                df_asistencia = pd.DataFrame([
                    {"Casa": k, "No. Casas Representadas": v} for k, v in servidor["conectados"].items()
                ]).sort_values(by="Casa")
                st.table(df_asistencia)
            else:
                st.info("No hay casas conectadas aún.")

        st.divider()

        if not servidor["asamblea_iniciada"]:
            if st.button("🚀 ABRIR PLATAFORMA VOTANTES", type="primary", use_container_width=True):
                servidor["asamblea_iniciada"] = True
                st.rerun()
        else:
            sel_p = st.selectbox("Pregunta a lanzar:", range(len(preguntas)), index=servidor['p_idx'], format_func=lambda x: preguntas[x])
            segundos = st.slider("Duración (seg):", 30, 300, 60)
            
            cl, cr = st.columns(2)
            if cl.button("📢 LANZAR PREGUNTA", type="primary", use_container_width=True):
                servidor['p_idx'], servidor['fase'] = sel_p, "votacion"
                servidor['tiempo_cierre'] = datetime.now() + timedelta(seconds=segundos)
                st.rerun()
            if cr.button("📊 VER RESULTADOS", use_container_width=True):
                servidor['fase'] = "resultados"
                st.rerun()

            df_v = servidor['votos']
            v_act = df_v[df_v['p_id'] == sel_p]
            
            if not v_act.empty:
                st.markdown("### 📈 Gráfica de Resultados")
                res = v_act.groupby('voto')['representa'].sum()
                fig, ax = plt.subplots(figsize=(4, 2.2)) 
                ax.pie(res, labels=res.index, autopct='%1.1f%%', startangle=90, 
                       colors=[('#2ecc71' if i=='SÍ' else '#e74c3c') for i in res.index],
                       textprops={'fontsize': 8})
                st.pyplot(fig)

                st.markdown("### 📋 Detalle de Votación")
                st.dataframe(v_act[['casa', 'representa', 'voto']].sort_values(by='casa'), 
                             use_container_width=True, hide_index=True)
            
            if not df_v.empty:
                df_export = df_v.copy()
                df_export['Pregunta'] = df_export['p_id'].apply(lambda x: preguntas[x])
                df_export = df_export[['casa', 'representa', 'Pregunta', 'voto']]
                csv = df_export.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Reporte (Excel)", data=csv, 
                                   file_name=f"Resultados_Alameda_7.csv",
                                   use_container_width=True)

# --- VISTA VOTANTE ---
else:
    if 'mi_casa' not in st.session_state:
        st.subheader("Ingreso de Votante")
        c_in = st.text_input("🏠 Número de Casa:").strip()
        # LA LÍNEA QUE TENÍA EL ERROR CORREGIDA ABAJO:
        podes = st.number_input("Total de casas que representa:", min_value=1, max_value=10, value=1)
        if st.button("Ingresar", type="primary"):
            if c_in:
                st.session_state.mi_casa, st.session_state.num_votos = c_in, podes
                servidor['conectados'][c_in] = podes
                st.rerun()
    else:
        casa, repre = st.session_state.mi_casa, st.session_state.num_votos
        st.sidebar.info(f"📍 Casa: {casa}\n\n🗳️ Representa: {repre} votos")
        if st.sidebar.button("Cerrar Sesión"):
            del st.session_state.mi_casa
            st.rerun()

        if not servidor["asamblea_iniciada"]:
            st.warning("⏳ Esperando apertura del sistema..."); time.sleep(3); st.rerun()
        
        fase, p_id = servidor['fase'], servidor['p_idx']
        
        if fase == "espera":
            st.info("⌛ Preparando siguiente pregunta..."); time.sleep(3); st.rerun()
        else:
            st.markdown(f"<div class='titulo-v'>{preguntas[p_id]}</div>", unsafe_allow_html=True)
            df = servidor['votos']
            ya_voto = not df[(df['casa'] == casa) & (df['p_id'] == p_id)].empty
            
            if fase == "resultados":
                v_p = df[df['p_id'] == p_id]
                if not v_p.empty:
                    res_s = v_p.groupby('voto')['representa'].sum()
                    fig, ax = plt.subplots(figsize=(4,3))
                    ax.pie(res_s, labels=res_s.index, autopct='%1.1f%%', colors=[('#2ecc71' if i=='SÍ' else '#e74c3c') for i in res_s.index])
                    st.pyplot(fig)
                st.button("🔄 Actualizar")
            elif ya_voto:
                st.success("✅ Voto registrado."); time.sleep(5); st.rerun()
            elif fase == "votacion":
                res_t = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()
                if res_t > 0:
                    st.error(f"⏱️ TIEMPO: {int(res_t)} seg")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ SÍ", use_container_width=True, key="si_fixed"):
                        servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "SÍ"}])], ignore_index=True)
                        st.rerun()
                    if c2.button("❌ NO", use_container_width=True, key="no_fixed"):
                        servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "NO"}])], ignore_index=True)
                        st.rerun()
                    time.sleep(1); st.rerun()
                else:
                    st.warning("⌛ El tiempo terminó."); time.sleep(3); st.rerun()
