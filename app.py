import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Asamblea Alameda 7", 
    page_icon="🏢", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. MEMORIA GLOBAL (SERVIDOR) ---
@st.cache_resource
def iniciar_servidor():
    return {
        "asamblea_iniciada": False,
        "asamblea_cerrada": False,
        "fase": "espera", 
        "p_idx": 0,
        "votos": pd.DataFrame(columns=["casa", "representa", "casas_detalle", "p_id", "voto"]),
        "conectados": {}, 
        "tiempo_cierre": None
    }

servidor = iniciar_servidor()
TOTAL_CASAS = 184

# --- 3. CSS PARA INTERFAZ MÓVIL Y BLINDAJE ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    [data-testid="stHeader"] {display:none !important;}
    [data-testid="sidebar-button"] {display: none !important;}
    
    .titulo-v { 
        font-size: 36px !important; 
        font-weight: bold; 
        text-align: center; 
        color: #1E1E1E;
        padding: 15px 0;
        line-height: 1.2;
    }
    
    div.row-widget.stRadio > div{
        flex-direction:row;
        justify-content: center;
        gap: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LISTADO DE PREGUNTAS ---
preguntas = [
    "¿Logró revisar el contenido de la cartilla para la Asamblea del 19 de Abril de 2026?",
    "¿Delegará poder a un tercero que asista a la Asamblea General?",
    "¿Cuenta con dispositivo móvil para asistir a la asamblea General?",
    "¿Cuenta ud con datos móviles para la participación en la Asamblea General?",
    "¿Tiene dudas acerca de la votación electrónica?",
    "¿Desea que la administración se contacte con ud para resolver sus inquietudes?"
]

# --- 5. LOGO ---
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if os.path.exists("image_f94506.jpg"):
        st.image("image_f94506.jpg", use_container_width=True)
    else:
        st.title("🏢 Alameda 7")

st.divider()

# --- 6. INTERFAZ DE ACCESO ---
if 'mi_casa' not in st.session_state and 'admin_logueado' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>Bienvenido</h2>", unsafe_allow_html=True)
    rol = st.radio("Identifíquese:", ["Votante", "Administrador"], horizontal=True, label_visibility="collapsed")
    
    if rol == "Votante":
        with st.form("login_v"):
            c_in = st.text_input("🏠 Su número de casa principal:")
            podes = st.number_input("Total de votos (incluido el suyo):", 1, 10, 1)
            detalle_c = st.text_input("Detalle de casas representadas:", placeholder="Ej: 101, 202")
            if st.form_submit_button("INGRESAR A VOTAR", use_container_width=True):
                if c_in and detalle_c:
                    st.session_state.mi_casa = c_in
                    st.session_state.num_votos = podes
                    st.session_state.detalle_votos = detalle_c
                    servidor['conectados'][c_in] = [podes, detalle_c]
                    st.rerun()
                else:
                    st.error("Por favor complete todos los campos.")
    else:
        with st.form("login_a"):
            clave = st.text_input("Contraseña Admin:", type="password")
            if st.form_submit_button("ACCEDER AL PANEL", use_container_width=True):
                if clave == "Alameda2026*":
                    st.session_state.admin_logueado = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta.")
    st.stop()

# --- 7. VISTA ADMINISTRADOR ---
if 'admin_logueado' in st.session_state:
    st.subheader("👨‍💼 Panel Administrativo")
    
    c_t = st.columns(3)
    if c_t[0].button("🔄 Actualizar"): st.rerun()
    if c_t[1].button("🧹 Reset Total"): 
        servidor["votos"] = pd.DataFrame(columns=["casa", "representa", "casas_detalle", "p_id", "voto"])
        servidor["conectados"] = {}
        servidor["asamblea_iniciada"] = False
        servidor["asamblea_cerrada"] = False
        st.rerun()
    if c_t[2].button("🚪 Salir"): 
        del st.session_state.admin_logueado
        st.rerun()

    casas_p = sum(v[0] for v in servidor["conectados"].values())
    st.metric("Quórum", f"{(casas_p / TOTAL_CASAS) * 100:.1f}%", f"{casas_p} votos")
    
    with st.expander("🏠 Ver Asistencia"):
        if servidor["conectados"]:
            df_a = pd.DataFrame([{"Casa Líder": k, "No. Votos": v[0], "Representadas": v[1]} for k, v in servidor["conectados"].items()]).sort_values("Casa Líder")
            st.table(df_a)

    if servidor["asamblea_cerrada"]:
        st.error("ASAMBLEA FINALIZADA")
    elif not servidor["asamblea_iniciada"]:
        if st.button("🚀 ABRIR ASAMBLEA", type="primary", use_container_width=True):
            servidor["asamblea_iniciada"] = True
            st.rerun()
    
    if servidor["asamblea_iniciada"]:
        sel_p = st.selectbox("Pregunta:", range(len(preguntas)), index=servidor['p_idx'], format_func=lambda x: preguntas[x])
        if not servidor["asamblea_cerrada"]:
            seg = st.slider("Segundos:", 30, 300, 60)
            cl, cr = st.columns(2)
            if cl.button("📢 LANZAR", type="primary", use_container_width=True):
                servidor['p_idx'], servidor['fase'] = sel_p, "votacion"
                servidor['tiempo_cierre'] = datetime.now() + timedelta(seconds=seg)
                st.rerun()
            if cr.button("📊 RESULTADOS", use_container_width=True):
                servidor['fase'] = "resultados"
                st.rerun()
            if st.button("🔴 CERRAR ASAMBLEA", use_container_width=True):
                servidor["asamblea_cerrada"] = True
                st.rerun()

        v_p = servidor['votos'][servidor['votos']['p_id'] == sel_p]
        if not v_p.empty:
            res = v_p.groupby('voto')['representa'].sum()
            fig, ax = plt.subplots(figsize=(4, 2))
            ax.pie(res, labels=res.index, autopct='%1.1f%%', startangle=90, colors=[('#2ecc71' if i=='SÍ' else '#e74c3c') for i in res.index])
            st.pyplot(fig)
            st.download_button("📥 Excel", data=servidor['votos'].to_csv(index=False).encode('utf-8'), file_name="resultados.csv", use_container_width=True)

# --- 8. VISTA VOTANTE ---
else:
    if servidor["asamblea_cerrada"]:
        st.success("🏁 LA ASAMBLEA HA FINALIZADO")
        st.markdown("<div class='titulo-v'>¡Muchas gracias!</div>", unsafe_allow_html=True)
        if st.button("Cerrar Sesión"):
            del st.session_state.mi_casa
            st.rerun()
        st.stop()

    st.info(f"🏠 Casa: **{st.session_state.mi_casa}** | 🗳️ Votos: **{st.session_state.num_votos}**")
    
    if not servidor["asamblea_iniciada"]:
        st.warning("⏳ Esperando al administrador..."); time.sleep(3); st.rerun()
    
    fase, p_id = servidor['fase'], servidor['p_idx']
    
    if fase == "espera":
        st.info("⌛ Preparando pregunta..."); time.sleep(3); st.rerun()
    else:
        st.markdown(f"<div class='titulo-v'>{preguntas[p_id]}</div>", unsafe_allow_html=True)
        v_hecho = not servidor['votos'][(servidor['votos']['casa'] == st.session_state.mi_casa) & (servidor['votos']['p_id'] == p_id)].empty
        
        if fase == "resultados":
            st.write("📊 Resultados en pantalla principal.")
            if st.button("Actualizar"): st.rerun()
        elif v_hecho:
            st.success("✅ Voto registrado correctamente."); time.sleep(5); st.rerun()
        elif fase == "votacion":
            t_r = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()
            if t_r > 0:
                st.error(f"⏱️ CIERRE EN: {int(t_r)} seg")
                c_si, c_no = st.columns(2)
                if c_si.button("✅ SÍ", use_container_width=True, key="si_f"):
                    servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{
                        "casa": st.session_state.mi_casa, "representa": st.session_state.num_votos, 
                        "casas_detalle": st.session_state.detalle_votos, "p_id": p_id, "voto": "SÍ"
                    }])], ignore_index=True)
                    st.rerun()
                if c_no.button("❌ NO", use_container_width=True, key="no_f"):
                    servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{
                        "casa": st.session_state.mi_casa, "representa": st.session_state.num_votos, 
                        "casas_detalle": st.session_state.detalle_votos, "p_id": p_id, "voto": "NO"
                    }])], ignore_index=True)
                    st.rerun()
                time.sleep(1); st.rerun()
            else:
                st.warning("⌛ Tiempo terminado."); time.sleep(3); st.rerun()

    # --- EL BOTÓN FINAL CORREGIDO ---
    if st.button("Cerrar Sesión"):
        del st.session_state.mi_casa
        st.rerun()
