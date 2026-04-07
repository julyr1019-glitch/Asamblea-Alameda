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

# --- 4. LOGO (TAMAÑO DISMINUIDO) ---
c_logo1, c_logo2, c_logo3 = st.columns([1, 2, 1])
with c_logo2: # Centramos el logo pequeño
    if os.path.exists("image_f94506.jpg"):
        st.image("image_f94506.jpg", width=250)
    else:
        st.title("🏢 Asamblea Alameda 7")

st.divider()

# --- 5. NAVEGACIÓN ---
rol = st.sidebar.radio("SISTEMA DE ASAMBLEA", ["Votante", "Administrador"], key="nav_main_pro")

# --- VISTA ADMINISTRADOR ---
if rol == "Administrador":
    st.header("👨‍💼 Panel de Mando (Admin)")
    clave = st.text_input("Contraseña Maestro:", type="password", key="admin_pwd_matrix")
    
    if clave == "Alameda2026*":
        casas_presentes = sum(servidor["conectados"].values())
        porcentaje_quorum = (casas_presentes / TOTAL_CASAS) * 100
        st.subheader(f"📊 Quórum Actual: {porcentaje_quorum:.1f}%")
        st.progress(min(porcentaje_quorum / 100, 1.0))
        
        if not servidor["asamblea_iniciada"]:
            if st.button("🚀 INICIAR ASAMBLEA GENERAL", type="primary", use_container_width=True):
                servidor["asamblea_iniciada"] = True
                st.rerun()
        else:
            sel_p = st.selectbox("Gestionar Pregunta:", range(len(preguntas)), 
                                 index=servidor['p_idx'], format_func=lambda x: preguntas[x])
            segundos = st.slider("Segundos de votación:", 30, 300, 60)
            
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

            # MONITOR DE GRÁFICAS
            df_v = servidor['votos']
            votos_act = df_v[df_v['p_id'] == sel_p]
            if not votos_act.empty:
                res_sum = votos_act.groupby('voto')['representa'].sum()
                fig, ax = plt.subplots(figsize=(5,3))
                if sel_p == 8:
                    res_sum_ord = res_sum.reindex(opciones_p9).fillna(0)
                    labels, colors = opciones_p9, ['#2ecc71', '#3498db', '#e74c3c']
                else:
                    res_sum_ord = res_sum.sort_index()
                    labels = res_sum_ord.index.tolist()
                    colors = [{'SÍ': '#2ecc71', 'NO': '#e74c3c'}[l] for l in labels]
                
                ax.pie(res_sum_ord, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
                st.pyplot(fig)
                
                with st.expander("Ver Matriz de Votos Detallada"):
                    # Aquí se muestra la planilla con la representación
                    st.dataframe(df_v)
            
            csv = df_v.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Reporte", data=csv, file_name="resultados.csv")

# --- VISTA VOTANTE ---
else:
    if 'mi_casa' not in st.session_state:
        st.subheader("Registro de Copropietario")
        c_in = st.text_input("🏠 Número de Casa Principal:", key="input_casa_final").strip()
        poderes = st.number_input("¿A cuántas casas representa en total? (Incluyendo la suya)", 1, 10, 1, key="input_poder_final")
        
        if st.button("Entrar a la Asamblea", type="primary", use_container_width=True):
            if c_in:
                st.session_state.mi_casa = c_in
                st.session_state.num_votos = poderes
                servidor['conectados'][c_in] = poderes
                st.rerun()
    else:
        casa = st.session_state.mi_casa
        repre = st.session_state.num_votos
        
        # PLANILLA EN SIDEBAR
        st.sidebar.markdown(f"### 📋 Su Planilla")
        st.sidebar.info(f"🏠 **Casa Principal:** {casa}\n\n👥 **Representa a:** {repre} Casa(s)")
        
        if st.sidebar.button("Cerrar Sesión"):
            del st.session_state.mi_casa
            st.rerun()

        if not servidor["asamblea_iniciada"]:
            st.warning("⏳ Esperando inicio de la sesión...")
            time.sleep(3)
            st.rerun()
        
        fase, p_id = servidor['fase'], servidor['p_idx']
        
        if fase == "espera":
            st.info("⌛ Preparando siguiente votación...")
            time.sleep(3)
            st.rerun()
        else:
            # PREGUNTA CON LETRA GRANDE Y NEGRITA
            st.markdown(f"<h2 style='text-align: center; color: #31333F;'><b>{preguntas[p_id]}</b></h2>", unsafe_allow_html=True)
            
            reloj_area = st.empty()
            df = servidor['votos']
            ya_voto = not df[(df['casa'] == casa) & (df['p_id'] == p_id)].empty
            
            restante = 0
            if fase == "votacion" and servidor['tiempo_cierre']:
                restante = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()

            if fase == "resultados":
                st.success("📊 RESULTADOS CONSOLIDADOS")
                v_p = df[df['p_id'] == p_id]
                if not v_p.empty:
                    res_s = v_p.groupby('voto')['representa'].sum()
                    fig, ax = plt.subplots()
                    if p_id == 8:
                        res_s = res_s.reindex(opciones_p9).fillna(0)
                        ax.pie(res_s, labels=opciones_p9, autopct='%1.1f%%', colors=['#2ecc71', '#3498db', '#e74c3c'])
                    else:
                        res_s = res_s.sort_index()
                        l = res_s.index.tolist()
                        c = [{'SÍ': '#2ecc71', 'NO': '#e74c3c'}[i] for i in l]
                        ax.pie(res_s, labels=l, autopct='%1.1f%%', colors=c)
                    st.pyplot(fig)
                st.button("🔄 Actualizar")

            elif ya_voto:
                st.success(f"✅ Voto de la Casa {casa} (x{repre}) registrado.")
                time.sleep(5)
                st.rerun()

            elif fase == "votacion" and restante > 0:
                reloj_area.error(f"⏱️ CIERRE EN: {int(restante)} segundos")
                
                if p_id == 8: # Pregunta 9
                    for op in opciones_p9:
                        if st.button(f"VOTAR POR: {op}", use_container_width=True, key=f"btn_p9_{op}"):
                            nuevo = pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": op}])
                            servidor['votos'] = pd.concat([servidor['votos'], nuevo], ignore_index=True)
                            st.rerun()
                else: 
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ SÍ", use_container_width=True, key="btn_si_v"):
                            nuevo = pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "SÍ"}])
                            servidor['votos'] = pd.concat([servidor['votos'], nuevo], ignore_index=True)
                            st.balloons()
                            st.rerun()
                    with c2:
                        if st.button("❌ NO", use_container_width=True, key="btn_no_v"):
                            nuevo = pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "NO"}])
                            servidor['votos'] = pd.concat([servidor['votos'], nuevo], ignore_index=True)
                            st.rerun()
                
                time.sleep(1)
                st.rerun()
            else:
                st.warning("⌛ Tiempo de votación terminado.")
                time.sleep(3)
                st.rerun()
