import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Asamblea Alameda 7 PRO", 
    page_icon="🏢", 
    layout="centered",
    initial_sidebar_state="expanded" # Aseguramos que el menú se vea
)

# --- 2. CSS PARA LIMPIAR Y AGRANDAR LETRA ---
# Ocultamos solo lo que lleva a Streamlit, no tu menú.
st.markdown("""
    <style>
    /* Ocultar branding de Streamlit */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    #manage-app-button {display:none !important;}
    
    /* ESTILO DE PREGUNTA TIPO TÍTULO GIGANTE */
    .titulo-pregunta {
        font-size: 42px !important;
        font-weight: 800 !important;
        color: #1E1E1E !important;
        text-align: center !important;
        line-height: 1.1 !important;
        margin-bottom: 30px !important;
        font-family: 'Source Sans Pro', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. MEMORIA GLOBAL ---
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

# --- 4. PREGUNTAS ---
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

# --- 5. LOGO (TAMAÑO DISMINUIDO) ---
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if os.path.exists("image_f94506.jpg"):
        st.image("image_f94506.jpg", width=200) # Logo pequeño
    else:
        st.title("🏢 Alameda 7")

st.divider()

# --- 6. NAVEGACIÓN (RESTAURADA) ---
rol = st.sidebar.radio("SISTEMA DE ASAMBLEA", ["Votante", "Administrador"], key="rol_selector")

# --- VISTA ADMINISTRADOR ---
if rol == "Administrador":
    st.header("👨‍💼 Panel de Administración")
    clave = st.text_input("Contraseña Maestro:", type="password", key="admin_key")
    
    if clave == "Alameda2026*":
        casas_presentes = sum(servidor["conectados"].values())
        porcentaje_quorum = (casas_presentes / TOTAL_CASAS) * 100
        st.subheader(f"📊 Quórum: {porcentaje_quorum:.1f}%")
        st.progress(min(porcentaje_quorum / 100, 1.0))
        
        if not servidor["asamblea_iniciada"]:
            if st.button("🚀 INICIAR ASAMBLEA", type="primary", use_container_width=True):
                servidor["asamblea_iniciada"] = True
                st.rerun()
        else:
            sel_p = st.selectbox("Pregunta a gestionar:", range(len(preguntas)), 
                                 index=servidor['p_idx'], format_func=lambda x: preguntas[x])
            segundos = st.slider("Tiempo de votación:", 30, 300, 60)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📢 LANZAR PREGUNTA", type="primary", use_container_width=True):
                    servidor['p_idx'] = sel_p
                    servidor['fase'] = "votacion"
                    servidor['tiempo_cierre'] = datetime.now() + timedelta(seconds=segundos)
                    st.rerun()
            with c2:
                if st.button("📊 VER RESULTADOS", use_container_width=True):
                    servidor['fase'] = "resultados"
                    st.rerun()

            # MONITOR
            df_v = servidor['votos']
            v_act = df_v[df_v['p_id'] == sel_p]
            if not v_act.empty:
                res_sum = v_act.groupby('voto')['representa'].sum()
                fig, ax = plt.subplots(figsize=(5,3))
                if sel_p == 8:
                    r_o = res_sum.reindex(opciones_p9).fillna(0)
                    ax.pie(r_o, labels=opciones_p9, autopct='%1.1f%%', colors=['#2ecc71', '#3498db', '#e74c3c'])
                else:
                    r_o = res_sum.sort_index(); l = r_o.index.tolist()
                    ax.pie(r_o, labels=l, autopct='%1.1f%%', colors=[{'SÍ':'#2ecc71','NO':'#e74c3c'}[i] for i in l])
                st.pyplot(fig)
            
            st.download_button("📥 Descargar Resultados", data=df_v.to_csv(index=False).encode('utf-8'), file_name="resultados.csv")

# --- VISTA VOTANTE ---
else:
    if 'mi_casa' not in st.session_state:
        st.subheader("Registro de Ingreso")
        c_in = st.text_input("🏠 Número de Casa:", key="casa_v").strip()
        poderes = st.number_input("¿A cuántas casas representa?", 1, 10, 1, key="podes_v")
        if st.button("Entrar a Votar", type="primary", use_container_width=True):
            if c_in:
                st.session_state.mi_casa = c_in
                st.session_state.num_votos = poderes
                servidor['conectados'][c_in] = poderes
                st.rerun()
    else:
        casa, repre = st.session_state.mi_casa, st.session_state.num_votos
        
        # PLANILLA EN EL LATERAL
        st.sidebar.markdown(f"### 📋 Su Planilla\n**Casa:** {casa}\n**Representa:** {repre} votos")
        if st.sidebar.button("Salir"):
            del st.session_state.mi_casa
            st.rerun()

        if not servidor["asamblea_iniciada"]:
            st.warning("⏳ Esperando inicio...")
            time.sleep(3); st.rerun()
        
        fase, p_id = servidor['fase'], servidor['p_idx']
        
        if fase == "espera":
            st.info("⌛ El administrador está preparando la pregunta...")
            time.sleep(3); st.rerun()
        else:
            # PREGUNTA GIGANTE
            st.markdown(f"<div class='titulo-pregunta'>{preguntas[p_id]}</div>", unsafe_allow_html=True)
            
            reloj_area = st.empty()
            df = servidor['votos']
            ya_voto = not df[(df['casa'] == casa) & (df['p_id'] == p_id)].empty
            
            res = (servidor['tiempo_cierre'] - datetime.now()).total_seconds() if fase == "votacion" and servidor['tiempo_cierre'] else 0

            if fase == "resultados":
                v_p = df[df['p_id'] == p_id]
                if not v_p.empty:
                    res_s = v_p.groupby('voto')['representa'].sum()
                    fig, ax = plt.subplots()
                    if p_id == 8:
                        res_s = res_s.reindex(opciones_p9).fillna(0)
                        ax.pie(res_s, labels=opciones_p9, autopct='%1.1f%%', colors=['#2ecc71', '#3498db', '#e74c3c'])
                    else:
                        res_s = res_s.sort_index(); l = res_s.index.tolist()
                        ax.pie(res_s, labels=l, autopct='%1.1f%%', colors=[{'SÍ':'#2ecc71','NO':'#e74c3c'}[i] for i in l])
                    st.pyplot(fig)
                st.button("🔄 Actualizar")

            elif ya_voto:
                st.success("✅ Voto registrado. Espere la siguiente instrucción.")
                time.sleep(5); st.rerun()

            elif fase == "votacion" and res > 0:
                reloj_area.error(f"⏱️ CIERRE EN: {int(res)} segundos")
                if p_id == 8: # Pregunta 9
                    for op in opciones_p9:
                        if st.button(f"VOTAR: {op}", use_container_width=True, key=f"p9_{op}"):
                            servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": op}])], ignore_index=True)
                            st.rerun()
                else: 
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ SÍ", use_container_width=True, key="btn_si"):
                            servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "SÍ"}])], ignore_index=True)
                            st.balloons(); st.rerun()
                    with c2:
                        if st.button("❌ NO", use_container_width=True, key="btn_no"):
                            servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "NO"}])], ignore_index=True)
                            st.rerun()
                time.sleep(1); st.rerun()
            else:
                st.warning("⌛ Tiempo terminado."); time.sleep(3); st.rerun()
