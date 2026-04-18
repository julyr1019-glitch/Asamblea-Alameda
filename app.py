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
    /* Ocultar elementos nativos de Streamlit */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    [data-testid="stHeader"] {display:none !important;}
    [data-testid="sidebar-button"] {display: none !important;}
    
    /* Títulos y Preguntas Gigantes */
    .titulo-v { 
        font-size: 36px !important; 
        font-weight: bold; 
        text-align: center; 
        color: #1E1E1E;
        padding: 15px 0;
        line-height: 1.2;
    }
    
    /* Centrar selectores de rol */
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

# --- 6. INTERFAZ DE ACCESO (IDENTIFICACIÓN) ---
if 'mi_casa' not in st.session_state and 'admin_logueado' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>Bienvenido</h2>", unsafe_allow_html=True)
    rol = st.radio("Identifíquese para continuar:", ["Votante", "Administrador"], horizontal=True)
    
    if rol == "Votante":
        with st.form("login_votante"):
            c_in = st.text_input("🏠 Su número de casa principal:")
            podes = st.number_input("Total de votos que representa (incluido el suyo):", 1, 10, 1)
            detalle_c = st.text_input("Detalle de casas representadas:", placeholder="Ej: 101, 202, 305")
            
            if st.form_submit_button("INGRESAR A VOTAR", use_container_width=True):
                if c_in and detalle_c:
                    st.session_state.mi_casa = c_in
                    st.session_state.num_votos = podes
                    st.session_state.detalle_votos = detalle_c
                    servidor['conectados'][c_in] = [podes, detalle_c]
                    st.rerun()
                else:
                    st.error("Por favor complete todos los campos para ingresar.")
    else:
        with st.form("login_admin"):
            clave = st.text_input("Contraseña de Administrador:", type="password")
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
    
    # Herramientas Superiores
    col_tools = st.columns(3)
    if col_tools[0].button("🔄 Actualizar"): st.rerun()
    if col_tools[1].button("🧹 Reset Total"): 
        servidor["votos"] = pd.DataFrame(columns=["casa", "representa", "casas_detalle", "p_id", "voto"])
        servidor["conectados"] = {}
        servidor["asamblea_iniciada"] = False
        servidor["asamblea_cerrada"] = False
        st.rerun()
    if col_tools[2].button("🚪 Salir"): 
        del st.session_state.admin_logueado
        st.rerun()

    # Monitor de Quórum
    casas_p = sum(v[0] for v in servidor["conectados"].values())
    porcentaje = (casas_p / TOTAL_CASAS) * 100
    st.metric("Quórum Actual", f"{porcentaje:.1f}%", f"{casas_p} votos de {TOTAL_CASAS}")
    st.progress(min(porcentaje / 100, 1.0))
    
    with st.expander("🏠 Listado de Asistencia Detallado"):
        if servidor["conectados"]:
            df_a = pd.DataFrame([
                {"Casa Líder": k, "No. Votos": v[0], "Casas Representadas": v[1]} 
                for k, v in servidor["conectados"].items()
            ]).sort_values("Casa Líder")
            st.table(df_a)

    st.divider()

    if servidor["asamblea_cerrada"]:
        st.error("🚫 LA ASAMBLEA SE ENCUENTRA FINALIZADA")
    elif not servidor["asamblea_iniciada"]:
        if st.button("🚀 ABRIR ASAMBLEA PARA VOTANTES", type="primary", use_container_width=True):
            servidor["asamblea_iniciada"] = True
            st.rerun()
    
    if servidor["asamblea_iniciada"]:
        sel_p = st.selectbox("Seleccione Pregunta:", range(len(preguntas)), index=servidor['p_idx'], format_func=lambda x: preguntas[x])
        
        if not servidor["asamblea_cerrada"]:
            seg = st.slider("Duración (segundos):", 30, 300, 60)
            c_l, c_r = st.columns(2)
            if c_l.button("📢 LANZAR PREGUNTA", type="primary", use_container_width=True):
                servidor['p_idx'], servidor['fase'] = sel_p, "votacion"
                servidor['tiempo_cierre'] = datetime.now() + timedelta(seconds=seg)
                st.rerun()
            if c_r.button("📊 VER RESULTADOS", use_container_width=True):
                servidor['fase'] = "resultados"
                st.rerun()
            
            if st.button("🔴 CERRAR ASAMBLEA DEFINITIVAMENTE", use_container_width=True):
                servidor["asamblea_cerrada"] = True
                st.rerun()

        # Visualización de Resultados y Auditoría
        v_p = servidor['votos'][servidor['votos']['p_id'] == sel_p]
        if not v_p.empty:
            st.markdown("### 📊 Gráfica de Resultados")
            res = v_p.groupby('voto')['representa'].sum()
            fig, ax = plt.subplots(figsize=(4, 2.2))
            ax.pie(res, labels=res.index, autopct='%1.1f%%', startangle=90, colors=[('#2ecc71' if i=='SÍ' else '#e74c3c') for i in res.index], textprops={'fontsize': 8})
            st.pyplot(fig)
            
            st.markdown("### 📋 Detalle de esta votación")
            st.dataframe(v_p[['casa', 'representa', 'casas_detalle', 'voto']].sort_values("casa"), use_container_width=True, hide_index=True)
            
            # Exportar Excel
            df_export = servidor['votos'].copy()
            df_export['Pregunta'] = df_export['p_id'].apply(lambda x: preguntas[x])
            csv_data = df_export[['casa', 'representa', 'casas_detalle', 'Pregunta', 'voto']].to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Reporte Completo (Excel)", data=csv_data, file_name=f"Reporte_Alameda7_{datetime.now().strftime('%d_%m')}.csv", use_container_width=True)

# --- 8. VISTA VOTANTE ---
else:
    if servidor["asamblea_cerrada"]:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.success("🏁 LA ASAMBLEA HA FINALIZADO")
        st.markdown("<div class='titulo-v'>¡Muchas gracias por su participación!</div>", unsafe_allow_html=True)
        st.info("Ya puede cerrar esta ventana de su navegador.")
        if st.button("Cerrar Sesión"):
            del st.session_state.mi_casa
            st.rerun()
        st.stop()

    # Información de sesión
    st.info(f"🏠 Casa: **{st.session_state.mi_casa}** | 🗳️ Votos: **{st.session_state.num_votos}**\n\nCasas: {st.session_state.detalle_votos}")
    
    if not servidor["asamblea_iniciada"]:
        st.warning("⏳ Esperando a que el administrador abra el sistema..."); time.sleep(3); st.rerun()
    
    fase, p_id = servidor['fase'], servidor['p_idx']
    
    if fase == "espera":
        st.info("⌛ Preparando siguiente pregunta..."); time.sleep(3); st.rerun()
    else:
        st.markdown(f"<div class='titulo-v'>{preguntas[p_id]}</div>", unsafe_allow_html=True)
        v_hecho = not servidor['votos'][(servidor['votos']['casa'] == st.session_state.mi_casa) & (servidor['votos']['p_id'] == p_id)].empty
        
        if fase == "resultados":
            st.write("📊 Resultados parciales en pantalla principal.")
            if st.button("🔄 Actualizar"): st.rerun()
        elif v_hecho:
            st.success("✅ Su voto ha sido registrado correctamente."); time.sleep(5); st.rerun()
        elif fase == "votacion":
            t_restante = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()
            if t_restante > 0:
                st.error(f"⏱️ TIEMPO PARA VOTAR: {int(t_restante)} seg")
                c_si, c_no = st.columns(2)
                if c_si.button("✅ SÍ", use_container_width=True, key="btn_si"):
                    servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{
                        "casa": st.session_state.mi_casa, "representa": st.session_state.num_votos, 
                        "casas_detalle": st.session_state.detalle_votos, "p_id": p_id, "voto": "SÍ"
                    }])], ignore_index=True)
                    st.rerun()
                if c_no.button("❌ NO", use_container_width=True, key="btn_no"):
                    servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{
                        "casa": st.session_state.mi_casa, "representa": st.session_state.num_votos, 
                        "casas_detalle": st.session_state.detalle_votos, "p_id": p_id, "voto": "NO"
                    }])], ignore_index=True)
                    st.rerun()
                time.sleep(1); st.rerun()
            else:
                st.warning("⌛ El tiempo de votación ha terminado."); time.sleep(3); st.rerun()

    if st.button("Cerrar Sesión"):
        del st.session_state.mi_casa
        st.rerun()
