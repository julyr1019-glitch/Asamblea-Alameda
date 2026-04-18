import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURACION ---
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

# --- 3. CSS PARA INTERFAZ LIMPIA ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    [data-testid="stHeader"] {display:none !important;}
    [data-testid="sidebar-button"] {display: none !important;}
    .titulo-v { 
        font-size: 32px !important; 
        font-weight: bold; 
        text-align: center; 
        color: #1E1E1E;
        padding: 10px 0;
    }
    div.row-widget.stRadio > div{
        flex-direction:row;
        justify-content: center;
        gap: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. PREGUNTAS (SIN TILDES PARA EXCEL) ---
preguntas = [
    "Logro revisar el contenido de la cartilla para la Asamblea del 19 de Abril de 2026?",
    "Delegara poder a un tercero que asista a la Asamblea General?",
    "Cuenta con dispositivo movil para asistir a la asamblea General?",
    "Cuenta ud con datos moviles para la participacion en la Asamblea General?",
    "Tiene dudas acerca de la votacion electronica?",
    "Desea que la administracion se contacte con ud para resolver sus inquietudes?"
]

# --- 5. LOGO ---
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if os.path.exists("image_f94506.jpg"):
        st.image("image_f94506.jpg", use_container_width=True)
    else:
        st.title("ALAMEDA 7")

st.divider()

# --- 6. IDENTIFICACION ---
if 'mi_casa' not in st.session_state and 'admin_logueado' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>Bienvenido</h2>", unsafe_allow_html=True)
    rol = st.radio("Identifiquese:", ["Votante", "Administrador"], horizontal=True)
    
    if rol == "Votante":
        with st.form("login_v"):
            c_in = st.text_input("Casa Principal (Ej: 101):").strip()
            detalle_c = st.text_input("Otras casas que representa (Separadas por coma):", placeholder="Ej: 202, 305 (Deje vacio si solo representa la suya)")
            
            if st.form_submit_button("INGRESAR A LA ASAMBLEA", use_container_width=True):
                if c_in:
                    # CALCULO AUTOMATICO: 1 + numero de elementos en la lista de adicionales
                    adicionales = [x.strip() for x in detalle_c.split(',') if x.strip()]
                    podes_calc = 1 + len(adicionales)
                    texto_detalle = f"{c_in}, " + ", ".join(adicionales) if adicionales else c_in
                    
                    st.session_state.mi_casa = c_in
                    st.session_state.num_votos = podes_calc
                    st.session_state.detalle_votos = texto_detalle
                    
                    servidor['conectados'][c_in] = [podes_calc, texto_detalle]
                    st.rerun()
                else: st.error("Debe ingresar su Casa Principal.")
    else:
        with st.form("login_a"):
            clave = st.text_input("Clave Admin:", type="password")
            if st.form_submit_button("ENTRAR AL PANEL", use_container_width=True):
                if clave == "Alameda2026*":
                    st.session_state.admin_logueado = True
                    st.rerun()
                else: st.error("Clave incorrecta.")
    st.stop()

# --- 7. VISTA ADMINISTRADOR ---
if 'admin_logueado' in st.session_state:
    st.subheader("Panel Administrativo")
    
    c_t = st.columns(3)
    if c_t[0].button("Actualizar"): st.rerun()
    if c_t[1].button("Reset Total"): 
        servidor.update({"votos": pd.DataFrame(columns=["casa", "representa", "casas_detalle", "p_id", "voto"]), "conectados": {}, "asamblea_iniciada": False, "asamblea_cerrada": False, "fase": "espera"})
        st.rerun()
    if c_t[2].button("Salir"): del st.session_state.admin_logueado; st.rerun()

    votos_totales = sum(v[0] for v in servidor["conectados"].values())
    st.metric("Quorum", f"{(votos_totales/TOTAL_CASAS)*100:.1f}%", f"{votos_totales} de {TOTAL_CASAS} votos")
    
    with st.expander("Ver Listado de Asistencia"):
        if servidor["conectados"]:
            st.table(pd.DataFrame([{"Casa Lider": k, "Votos": v[0], "Casas Detalle": v[1]} for k, v in servidor["conectados"].items()]))

    if servidor["asamblea_cerrada"]:
        st.error("ASAMBLEA CERRADA DEFINITIVAMENTE")
    elif not servidor["asamblea_iniciada"]:
        if st.button("ABRIR PLATAFORMA", type="primary", use_container_width=True):
            servidor["asamblea_iniciada"] = True; st.rerun()
    
    if servidor["asamblea_iniciada"] or servidor["asamblea_cerrada"]:
        sel_p = st.selectbox("Pregunta:", range(len(preguntas)), index=servidor['p_idx'], format_func=lambda x: preguntas[x])
        
        if not servidor["asamblea_cerrada"]:
            seg = st.slider("Segundos:", 30, 300, 60)
            cl, cr = st.columns(2)
            if cl.button("LANZAR PREGUNTA", type="primary", use_container_width=True):
                servidor.update({'p_idx': sel_p, 'fase': "votacion", 'tiempo_cierre': datetime.now() + timedelta(seconds=seg)})
                st.rerun()
            if cr.button("VER RESULTADOS", use_container_width=True):
                servidor['fase'] = "resultados"; st.rerun()
            if st.button("CERRAR ASAMBLEA", use_container_width=True):
                servidor["asamblea_cerrada"] = True; st.rerun()

        # TABLA DE REPORTES (Siempre visible tras lanzar pregunta)
        v_p = servidor['votos'][servidor['votos']['p_id'] == sel_p]
        if not v_p.empty:
            st.markdown("### Resultados y Auditoria")
            res = v_p.groupby('voto')['representa'].sum()
            fig, ax = plt.subplots(figsize=(4, 2))
            ax.pie(res, labels=res.index, autopct='%1.1f%%', startangle=90, colors=[('#2ecc71' if i=='SI' else '#e74c3c') for i in res.index])
            st.pyplot(fig)
            
            # Tabla detallada para el Admin
            st.dataframe(v_p[['casa', 'representa', 'casas_detalle', 'voto']].sort_values(by="casa"), use_container_width=True, hide_index=True)
            
            # Exportacion sin tildes
            df_export = servidor['votos'].copy()
            df_export['Pregunta'] = df_export['p_id'].apply(lambda x: preguntas[x])
            st.download_button("Descargar Excel (CSV)", data=df_export[['casa', 'representa', 'casas_detalle', 'Pregunta', 'voto']].to_csv(index=False).encode('utf-8'), file_name="Reporte_Asamblea.csv", use_container_width=True)

# --- 8. VISTA VOTANTE ---
else:
    if servidor["asamblea_cerrada"]:
        st.success("ASAMBLEA FINALIZADA"); st.markdown("<div class='titulo-v'>¡Gracias por su participacion!</div>", unsafe_allow_html=True)
        if st.button("Cerrar Sesion"): del st.session_state.mi_casa; st.rerun()
        st.stop()

    st.info(f"Casa: {st.session_state.mi_casa} | Votos: {st.session_state.num_votos}")
    st.caption(f"Representa a: {st.session_state.detalle_votos}")
    
    if not servidor["asamblea_iniciada"]:
        st.warning("Esperando apertura..."); time.sleep(2); st.rerun()
    
    fase, p_id = servidor['fase'], servidor['p_idx']
    
    if fase == "espera":
        st.info("Preparando pregunta..."); time.sleep(2); st.rerun()
    else:
        st.markdown(f"<div class='titulo-v'>{preguntas[p_id]}</div>", unsafe_allow_html=True)
        df_v = servidor['votos']
        ya_voto = not df_v[(df_v['casa'] == st.session_state.mi_casa) & (df_v['p_id'] == p_id)].empty
        
        if fase == "resultados":
            v_p_v = df_v[df_v['p_id'] == p_id]
            if not v_p_v.empty:
                st.markdown("### Resultados Parciales:")
                res_v = v_p_v.groupby('voto')['representa'].sum()
                fig2, ax2 = plt.subplots(figsize=(4, 3))
                ax2.pie(res_v, labels=res_v.index, autopct='%1.1f%%', colors=[('#2ecc71' if i=='SI' else '#e74c3c') for i in res_v.index])
                st.pyplot(fig2)
            if st.button("Actualizar"): st.rerun()
        
        elif ya_voto:
            st.success("Voto registrado. Espere los resultados..."); time.sleep(3); st.rerun()
            
        elif fase == "votacion":
            t_r = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()
            if t_r > 0:
                st.error(f"CIERRE EN: {int(t_r)} seg")
                c_si, c_no = st.columns(2)
                if c_si.button("SI", use_container_width=True, key="vs"):
                    servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": st.session_state.mi_casa, "representa": st.session_state.num_votos, "casas_detalle": st.session_state.detalle_votos, "p_id": p_id, "voto": "SI"}])], ignore_index=True)
                    st.rerun()
                if c_no.button("NO", use_container_width=True, key="vn"):
                    servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": st.session_state.mi_casa, "representa": st.session_state.num_votos, "casas_detalle": st.session_state.detalle_votos, "p_id": p_id, "voto": "NO"}])], ignore_index=True)
                    st.rerun()
                time.sleep(1); st.rerun()
            else: st.warning("Tiempo terminado."); time.sleep(2); st.rerun()

    if st.button("Cerrar Sesion"): del st.session_state.mi_casa; st.rerun()
