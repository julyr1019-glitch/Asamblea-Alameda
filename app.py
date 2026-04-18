import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Asamblea Alameda 7", 
    page_icon="🏢", 
    layout="centered",
    initial_sidebar_state="collapsed" # La cortina inicia cerrada por defecto
)

# --- 2. MEMORIA GLOBAL ---
@st.cache_resource
def iniciar_servidor():
    return {
        "asamblea_iniciada": False,
        "asamblea_cerrada": False,
        "fase": "espera", 
        "p_idx": 0,
        "votos": pd.DataFrame(columns=["casa", "representa", "p_id", "voto"]),
        "conectados": {}, 
        "tiempo_cierre": None
    }

servidor = iniciar_servidor()
TOTAL_CASAS = 184

# --- 3. CSS PARA BLINDAJE Y BOTONES GIGANTES ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    [data-testid="stHeader"] {display:none !important;}
    
    /* Pregunta Gigante */
    .titulo-v { 
        font-size: 40px !important; 
        font-weight: bold; 
        text-align: center; 
        line-height: 1.2; 
        padding: 15px 0;
        color: #1E1E1E;
    }
    
    /* Ajuste para que los botones de radio se vean como botones reales */
    div.row-widget.stRadio > div{
        flex-direction:row;
        justify-content: center;
        gap: 20px;
    }
    
    /* Ocultar la flecha de la cortina lateral en móviles para no confundir */
    [data-testid="sidebar-button"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

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
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if os.path.exists("image_f94506.jpg"):
        st.image("image_f94506.jpg", use_container_width=True)
    else:
        st.title("🏢 Alameda 7")

st.divider()

# --- 6. SELECCIÓN DE ROL EN PANTALLA PRINCIPAL (NO SIDEBAR) ---
if 'mi_casa' not in st.session_state and 'admin_logueado' not in st.session_state:
    st.markdown("<h3 style='text-align: center;'>IDENTIFICACIÓN</h3>", unsafe_allow_html=True)
    rol_inicio = st.radio("SELECCIONE SU ROL:", ["Votante", "Administrador"], horizontal=True, label_visibility="collapsed")
    
    if rol_inicio == "Votante":
        with st.container(border=True):
            c_in = st.text_input("🏠 Número de Casa:", placeholder="Ej: 101").strip()
            podes = st.number_input("No. Casas Representadas:", min_value=1, max_value=10, value=1)
            if st.button("INGRESAR A LA ASAMBLEA", type="primary", use_container_width=True):
                if c_in:
                    st.session_state.mi_casa, st.session_state.num_votos = c_in, podes
                    servidor['conectados'][c_in] = podes
                    st.rerun()
                else:
                    st.error("Por favor ingrese su número de casa.")
    else:
        with st.container(border=True):
            clave = st.text_input("Contraseña Maestro:", type="password")
            if st.button("ACCEDER COMO ADMIN", use_container_width=True):
                if clave == "Alameda2026*":
                    st.session_state.admin_logueado = True
                    st.rerun()
                else:
                    st.error("Clave incorrecta.")
    st.stop()

# --- VISTA ADMINISTRADOR (LOGUEADO) ---
if 'admin_logueado' in st.session_state:
    st.header("👨‍💼 Panel de Control")
    
    # Herramientas rápidas arriba
    c_h1, c_h2, c_h3 = st.columns(3)
    if c_h1.button("🔄 Rerun"): st.rerun()
    if c_h2.button("🧹 Reset"): 
        servidor["votos"] = pd.DataFrame(columns=["casa", "representa", "p_id", "voto"])
        servidor["conectados"] = {}
        servidor["asamblea_iniciada"] = False
        servidor["asamblea_cerrada"] = False
        st.rerun()
    if c_h3.button("🚪 Salir"): 
        del st.session_state.admin_logueado
        st.rerun()

    casas_presentes = sum(servidor["conectados"].values())
    porcentaje_quorum = (casas_presentes / TOTAL_CASAS) * 100
    st.metric("Quórum Actual", f"{porcentaje_quorum:.1f}%", f"{casas_presentes} votos")
    st.progress(min(porcentaje_quorum / 100, 1.0))

    with st.expander("🏠 Listado de Asistencia Detallado"):
        if servidor["conectados"]:
            df_asistencia = pd.DataFrame([{"Casa": k, "No. Casas Representadas": v} for k, v in servidor["conectados"].items()]).sort_values(by="Casa")
            st.table(df_asistencia)

    if servidor["asamblea_cerrada"]:
        st.error("LA ASAMBLEA ESTÁ CERRADA")
    elif not servidor["asamblea_iniciada"]:
        if st.button("🚀 ABRIR PLATAFORMA", type="primary", use_container_width=True):
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
            if st.button("🔴 CERRAR ASAMBLEA DEFINITIVAMENTE", use_container_width=True):
                servidor["asamblea_cerrada"] = True
                st.rerun()

        # Resultados
        df_v = servidor['votos']
        v_act = df_v[df_v['p_id'] == sel_p]
        if not v_act.empty:
            res = v_act.groupby('voto')['representa'].sum()
            fig, ax = plt.subplots(figsize=(4, 2.2))
            ax.pie(res, labels=res.index, autopct='%1.1f%%', startangle=90, colors=[('#2ecc71' if i=='SÍ' else '#e74c3c') for i in res.index])
            st.pyplot(fig)
            st.dataframe(v_act[['casa', 'representa', 'voto']], use_container_width=True, hide_index=True)
            df_export = df_v.copy()
            df_export['Pregunta'] = df_export['p_id'].apply(lambda x: preguntas[x])
            st.download_button("📥 Bajar Excel", data=df_export[['casa', 'representa', 'Pregunta', 'voto']].to_csv(index=False).encode('utf-8'), file_name="resultados.csv")

# --- VISTA VOTANTE (LOGUEADO) ---
else:
    if servidor["asamblea_cerrada"]:
        st.success("🏁 LA ASAMBLEA HA FINALIZADO")
        st.markdown("<div class='titulo-v'>¡Muchas gracias por su participación!</div>", unsafe_allow_html=True)
        st.info("Ya puede cerrar esta ventana.")
        if st.button("Cerrar Sesión"):
            del st.session_state.mi_casa
            st.rerun()
        st.stop()

    casa, repre = st.session_state.mi_casa, st.session_state.num_votos
    st.markdown(f"<p style='text-align: center;'>🏠 Casa: <b>{casa}</b> | 🗳️ Votos: <b>{repre}</b></p>", unsafe_allow_html=True)

    if not servidor["asamblea_iniciada"]:
        st.warning("⏳ Esperando apertura del sistema...")
        time.sleep(3); st.rerun()
    
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
                if c1.button("✅ SÍ", use_container_width=True, key="v_si"):
                    servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "SÍ"}])], ignore_index=True)
                    st.rerun()
                if c2.button("❌ NO", use_container_width=True, key="v_no"):
                    servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "NO"}])], ignore_index=True)
                    st.rerun()
                time.sleep(1); st.rerun()
            else:
                st.warning("⌛ Tiempo terminado."); time.sleep(3); st.rerun()

    if st.button("Cerrar Sesión / Salir"):
        del st.session_state.mi_casa
        st.rerun()
