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
    initial_sidebar_state="collapsed"
)

# --- 2. MEMORIA GLOBAL ---
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

# --- 3. CSS PARA ELIMINAR LA CORTINA Y MOSTRAR BOTONES ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    [data-testid="stHeader"] {display:none !important;}
    [data-testid="sidebar-button"] {display: none !important;}
    
    .titulo-v { 
        font-size: 38px !important; 
        font-weight: bold; 
        text-align: center; 
        color: #1E1E1E;
        padding: 20px 0;
    }
    div.row-widget.stRadio > div{
        flex-direction:row;
        justify-content: center;
        gap: 15px;
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

# --- 6. INTERFAZ DE ENTRADA ---
if 'mi_casa' not in st.session_state and 'admin_logueado' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>Bienvenido</h2>", unsafe_allow_html=True)
    rol = st.radio("Identifíquese para continuar:", ["Votante", "Administrador"], horizontal=True)
    
    if rol == "Votante":
        with st.form("login_v"):
            c_in = st.text_input("🏠 Su número de casa principal:")
            podes = st.number_input("Total de casas que representa (incluida la suya):", 1, 10, 1)
            detalle_c = st.text_input("Escriba los números de las casas que representa:", placeholder="Ej: 101, 202, 305")
            
            if st.form_submit_button("INGRESAR A VOTAR", use_container_width=True):
                if c_in and detalle_c:
                    st.session_state.mi_casa = c_in
                    st.session_state.num_votos = podes
                    st.session_state.detalle_votos = detalle_c
                    # Guardamos en el servidor: {casa_principal: [cantidad, detalle_numeros]}
                    servidor['conectados'][c_in] = [podes, detalle_c]
                    st.rerun()
                else:
                    st.error("Por favor complete su casa y los números de las casas que representa.")
    else:
        with st.form("login_a"):
            clave = st.text_input("Contraseña Admin:", type="password")
            if st.form_submit_button("ACCEDER AL PANEL", use_container_width=True):
                if clave == "Alameda2026*":
                    st.session_state.admin_logueado = True
                    st.rerun()
    st.stop()

# --- VISTA ADMINISTRADOR ---
if 'admin_logueado' in st.session_state:
    st.subheader("👨‍💼 Panel Administrativo")
    
    col_h = st.columns(3)
    if col_h[0].button("🔄 Refrescar"): st.rerun()
    if col_h[1].button("🧹 Reset Total"): 
        servidor["votos"] = pd.DataFrame(columns=["casa", "representa", "casas_detalle", "p_id", "voto"])
        servidor["conectados"] = {}
        servidor["asamblea_iniciada"] = False
        servidor["asamblea_cerrada"] = False
        st.rerun()
    if col_h[2].button("🚪 Salir"): 
        del st.session_state.admin_logueado
        st.rerun()

    casas_p = sum(v[0] for v in servidor["conectados"].values())
    st.metric("Quórum Actual", f"{(casas_p/TOTAL_CASAS)*100:.1f}%", f"{casas_p} votos de {TOTAL_CASAS}")
    
    with st.expander("🏠 Ver Asistencia Detallada"):
        if servidor["conectados"]:
            df_a = pd.DataFrame([
                {"Casa Líder": k, "No. Votos": v[0], "Casas Representadas": v[1]} 
                for k, v in servidor["conectados"].items()
            ]).sort_values("Casa Líder")
            st.table(df_a)

    if servidor["asamblea_cerrada"]:
        st.error("LA ASAMBLEA ESTÁ CERRADA")
    elif not servidor["asamblea_iniciada"]:
        if st.button("🚀 ABRIR ASAMBLEA", type="primary", use_container_width=True):
            servidor["asamblea_iniciada"] = True
            st.rerun()
    else:
        sel_p = st.selectbox("Pregunta:", range(len(preguntas)), index=servidor['p_idx'], format_func=lambda x: preguntas[x])
        if not servidor["asamblea_cerrada"]:
            seg = st.slider("Tiempo de votación:", 30, 300, 60)
            c_l, c_r = st.columns(2)
            if c_l.button("📢 LANZAR", type="primary", use_container_width=True):
                servidor['p_idx'], servidor['fase'] = sel_p, "votacion"
                servidor['tiempo_cierre'] = datetime.now() + timedelta(seconds=seg)
                st.rerun()
            if c_r.button("📊 RESULTADOS", use_container_width=True):
                servidor['fase'] = "resultados"
                st.rerun()
            if st.button("🔴 CERRAR ASAMBLEA", use_container_width=True):
                servidor["asamblea_cerrada"] = True
                st.rerun()

        # Resultados visuales
        v_p = servidor['votos'][servidor['votos']['p_id'] == sel_p]
        if not v_p.empty:
            res = v_p.groupby('voto')['representa'].sum()
            fig, ax = plt.subplots(figsize=(4, 2))
            ax.pie(res, labels=res.index, autopct='%1.1f%%', colors=[('#2ecc71' if i=='SÍ' else '#e74c3c') for i in res.index])
            st.pyplot(fig)
            st.dataframe(v_p[['casa', 'representa', 'casas_detalle', 'voto']], hide_index=True)
            
            # Exportación
            df_export = servidor['votos'].copy()
            df_export['Pregunta'] = df_export['p_id'].apply(lambda x: preguntas[x])
            st.download_button("📥 Descargar Reporte Completo", data=df_export[['casa', 'representa', 'casas_detalle', 'Pregunta', 'voto']].to_csv(index=False).encode('utf-8'), file_name="resultados_alameda.csv")

# --- VISTA VOTANTE ---
else:
    if servidor["asamblea_cerrada"]:
        st.success("🏁 ASAMBLEA FINALIZADA. ¡Gracias por participar!")
        if st.button("Cerrar Sesión"):
            del st.session_state.mi_casa
            st.rerun()
        st.stop()

    # Mostrar info del votante
    st.info(f"🏠 Casa: **{st.session_state.mi_casa}** | 🗳️ Votos: **{st.session_state.num_votos}**\n\nCasas: {st.session_state.detalle_votos}")
    
    if not servidor["asamblea_iniciada"]:
        st.warning("⏳ Esperando apertura del sistema..."); time.sleep(3); st.rerun()
    
    fase, p_id = servidor['fase'], servidor['p_idx']
    
    if fase == "espera":
        st.info("⌛ Preparando pregunta..."); time.sleep(3); st.rerun()
    else:
        st.markdown(f"<div class='titulo-v'>{preguntas[p_id]}</div>", unsafe_allow_html=True)
        v_hecho = not servidor['votos'][(servidor['votos']['casa'] == st.session_state.mi_casa) & (servidor['votos']['p_id'] == p_id)].empty
        
        if fase == "resultados":
            st.write("📊 Resultados parciales en pantalla del Administrador.")
            st.button("Actualizar")
        elif v_hecho:
            st.success("✅ Su voto ha sido registrado correctamente."); time.sleep(5); st.rerun()
        elif fase == "votacion":
            t = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()
            if t > 0:
                st.error(f"⏱️ CIERRE EN: {int(t)} seg")
                c1, c2 = st.columns(2)
                if c1.button("✅ SÍ", use_container_width=True):
                    servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{
                        "casa": st.session_state.mi_casa, 
                        "representa": st.session_state.num_votos, 
                        "casas_detalle": st.session_state.detalle_votos,
                        "p_id": p_id, 
                        "voto": "SÍ"
                    }])], ignore_index=True)
                    st.rerun()
                if c2.button("❌ NO", use_container_width=True):
                    servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{
                        "casa": st.session_state.mi_casa, 
                        "representa": st.session_state.num_votos, 
                        "casas_detalle": st.session_state.detalle_votos,
                        "p_id": p_id, 
                        "voto": "NO"
                    }])], ignore_index=True)
                    st.rerun()
                time.sleep(1); st.rerun()
            else:
                st.warning("⌛ El tiempo terminó."); time.sleep(3); st.rerun()

    if st.button("Cerrar Sesión / Cambiar Datos"):
        del st.session_state.mi_casa
        st.rerun()
