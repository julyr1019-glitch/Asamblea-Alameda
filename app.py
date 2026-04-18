import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime, timedelta
from fpdf import FPDF

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

# --- 3. FUNCION PDF ---
def generar_pdf_quorum(datos_conectados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "REPORTE DE QUORUM - ALAMEDA 7", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Casa Lider", 1)
    pdf.cell(30, 10, "No. Votos", 1)
    pdf.cell(120, 10, "Detalle de Casas", 1)
    pdf.ln()
    pdf.set_font("Arial", size=10)
    for k, v in sorted(datos_conectados.items(), key=lambda x: int(x[0])):
        pdf.cell(40, 10, str(k), 1)
        pdf.cell(30, 10, str(v[0]), 1)
        pdf.cell(120, 10, str(v[1]), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    [data-testid="stHeader"] {display:none !important;}
    [data-testid="sidebar-button"] {display: none !important;}
    .titulo-v { font-size: 30px !important; font-weight: bold; text-align: center; color: #1E1E1E; padding: 10px 0; }
    div.row-widget.stRadio > div{ flex-direction:row; justify-content: center; gap: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGO ---
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if os.path.exists("image_f94506.jpg"): st.image("image_f94506.jpg", use_container_width=True)
    else: st.title("ALAMEDA 7")

st.divider()

# --- 6. IDENTIFICACION ---
if 'mi_casa' not in st.session_state and 'admin_logueado' not in st.session_state:
    st.markdown("<h2 style='text-align: center;'>Bienvenido</h2>", unsafe_allow_html=True)
    rol = st.radio("Identifiquese:", ["Votante", "Administrador"], horizontal=True, label_visibility="collapsed")
    
    if rol == "Votante":
        with st.form("login_v"):
            casa_lider_n = st.number_input("Su Casa Principal (1-184):", min_value=1, max_value=TOTAL_CASAS, step=1)
            detalle_c = st.text_input("Otras casas que representa (Solo numeros):", placeholder="Ej: 20, 45")
            
            if st.form_submit_button("INGRESAR", use_container_width=True):
                casa_lider = str(int(casa_lider_n))
                # Censo Global para validación
                casas_ocupadas = set()
                for lider, data in servidor['conectados'].items():
                    for p in [x.strip() for x in data[1].split(',') if x.strip()]: casas_ocupadas.add(p)

                if casa_lider in casas_ocupadas:
                    st.error(f"La casa {casa_lider} ya esta registrada. Si se le cerro la sesion, pida al administrador que libere su casa.")
                else:
                    raw_others = [x.strip() for x in detalle_c.replace('.',',').split(',') if x.strip()]
                    unique_others, errores = [], []
                    for c in raw_others:
                        if not c.isdigit(): errores.append(f"'{c}' no es numero"); continue
                        num = int(c)
                        if num < 1 or num > TOTAL_CASAS: errores.append(f"Casa {num} fuera de rango"); continue
                        if str(num) == casa_lider: continue
                        if str(num) in casas_ocupadas: st.warning(f"Casa {num} ya esta registrada por otro."); continue
                        unique_others.append(str(num))
                    
                    if errores: st.error(f"Errores: {', '.join(errores)}")
                    else:
                        unique_others = sorted(list(set(unique_others)))
                        podes_calc = 1 + len(unique_others)
                        texto_final = casa_lider + (f", {', '.join(unique_others)}" if unique_others else "")
                        st.session_state.mi_casa, st.session_state.num_votos, st.session_state.detalle_votos = casa_lider, podes_calc, texto_final
                        servidor['conectados'][casa_lider] = [podes_calc, texto_final]
                        st.rerun()
    else:
        with st.form("login_a"):
            clave = st.text_input("Clave Admin:", type="password")
            if st.form_submit_button("ENTRAR AL PANEL", use_container_width=True):
                if clave == "Alameda2026*": st.session_state.admin_logueado = True; st.rerun()
                else: st.error("Clave incorrecta.")
    st.stop()

# --- 7. VISTA ADMINISTRADOR ---
if 'admin_logueado' in st.session_state:
    st.subheader("Panel Administrativo")
    
    c_t = st.columns([1, 1, 1, 1.5])
    if c_t[0].button("Actualizar"): st.rerun()
    if c_t[1].button("Reset"): 
        servidor.update({"votos": pd.DataFrame(columns=["casa", "representa", "casas_detalle", "p_id", "voto"]), "conectados": {}, "asamblea_iniciada": False, "asamblea_cerrada": False, "fase": "espera"})
        st.rerun()
    if c_t[2].button("Salir"): del st.session_state.admin_logueado; st.rerun()
    if not servidor["asamblea_cerrada"] and c_t[3].button("CERRAR ASAMBLEA"):
        servidor["asamblea_cerrada"] = True; st.rerun()

    votos_totales = sum(v[0] for v in servidor["conectados"].values())
    st.metric("Quorum", f"{(votos_totales/TOTAL_CASAS)*100:.1f}%", f"{votos_totales} de {TOTAL_CASAS} votos")
    
    # --- HERRAMIENTA LIBERAR CASA ---
    with st.expander("🏠 Gestion de Asistencia y Quorum"):
        if servidor["conectados"]:
            # LISTA PARA BORRAR
            st.markdown("### Liberar Casa Bloqueada")
            casa_a_liberar = st.selectbox("Seleccione casa para permitir re-ingreso:", [""] + list(servidor['conectados'].keys()))
            if st.button("🔓 LIBERAR CASA SELECCIONADA") and casa_a_liberar != "":
                del servidor['conectados'][casa_a_liberar]
                st.success(f"Casa {casa_a_liberar} liberada. El vecino ya puede volver a entrar.")
                st.rerun()
            
            st.divider()
            df_asist = pd.DataFrame([{"Casa Lider": k, "No. Votos": v[0], "Casas Detalle": v[1]} for k, v in servidor["conectados"].items()]).sort_values("Casa Lider", key=lambda x: x.astype(int))
            st.table(df_asist)
            
            pdf_bytes = generar_pdf_quorum(servidor["conectados"])
            st.download_button(label="📥 EXPORTAR QUORUM A PDF", data=pdf_bytes, file_name=f"Quorum_Alameda7.pdf", mime="application/pdf", use_container_width=True)

    if servidor["asamblea_cerrada"]: st.error("ASAMBLEA CERRADA DEFINITIVAMENTE")
    elif not servidor["asamblea_iniciada"]:
        if st.button("ABRIR PLATAFORMA", type="primary", use_container_width=True):
            servidor["asamblea_iniciada"] = True; st.rerun()
    
    if servidor["asamblea_iniciada"] or servidor["asamblea_cerrada"]:
        preguntas = ["Logro revisar el contenido de la cartilla...?", "Delegara poder a un tercero...?", "Cuenta con dispositivo movil...?", "Cuenta ud con datos moviles...?", "Tiene dudas acerca de la votacion...?", "Desea que la administracion se contacte...?"]
        sel_p = st.selectbox("Pregunta:", range(len(preguntas)), index=servidor['p_idx'], format_func=lambda x: preguntas[x])
        
        if not servidor["asamblea_cerrada"]:
            seg = st.slider("Segundos:", 30, 300, 60)
            cl, cr = st.columns(2)
            if cl.button("LANZAR", type="primary", use_container_width=True):
                servidor.update({'p_idx': sel_p, 'fase': "votacion", 'tiempo_cierre': datetime.now() + timedelta(seconds=seg)}); st.rerun()
            if cr.button("RESULTADOS", use_container_width=True):
                servidor['fase'] = "resultados"; st.rerun()

        v_p = servidor['votos'][servidor['votos']['p_id'] == sel_p]
        if not v_p.empty:
            res = v_p.groupby('voto')['representa'].sum()
            fig, ax = plt.subplots(figsize=(4, 2))
            ax.pie(res, labels=res.index, autopct='%1.1f%%', startangle=90, colors=[('#2ecc71' if i=='SI' else '#e74c3c') for i in res.index])
            st.pyplot(fig)
            st.dataframe(v_p[['casa', 'representa', 'casas_detalle', 'voto']].sort_values(by="casa", key=lambda x: x.astype(int)), use_container_width=True, hide_index=True)
            st.download_button("Descargar Reporte Excel", data=servidor['votos'].to_csv(index=False).encode('utf-8'), file_name="Reporte_Asamblea.csv", use_container_width=True)

# --- 8. VISTA VOTANTE ---
else:
    if servidor["asamblea_cerrada"]:
        st.success("ASAMBLEA FINALIZADA")
        if st.button("Cerrar Sesion"):
            if st.session_state.mi_casa in servidor['conectados']: del servidor['conectados'][st.session_state.mi_casa]
            del st.session_state.mi_casa; st.rerun()
        st.stop()

    st.info(f"Casa: {st.session_state.mi_casa} | Votos: {st.session_state.num_votos}")
    
    if not servidor["asamblea_iniciada"]:
        st.warning("Esperando apertura..."); time.sleep(2); st.rerun()
    
    fase, p_id = servidor['fase'], servidor['p_idx']
    preguntas = ["Logro revisar el contenido de la cartilla...?", "Delegara poder a un tercero...?", "Cuenta con dispositivo movil...?", "Cuenta ud con datos moviles...?", "Tiene dudas acerca de la votacion...?", "Desea que la administracion se contacte...?"]
    
    if fase == "espera": st.info("Preparando pregunta..."); time.sleep(2); st.rerun()
    else:
        st.markdown(f"<div class='titulo-v'>{preguntas[p_id]}</div>", unsafe_allow_html=True)
        ya_voto = not servidor['votos'][(servidor['votos']['casa'] == st.session_state.mi_casa) & (servidor['votos']['p_id'] == p_id)].empty
        
        if fase == "resultados":
            v_p_v = servidor['votos'][servidor['votos']['p_id'] == p_id]
            if not v_p_v.empty:
                res_v = v_p_v.groupby('voto')['representa'].sum()
                fig2, ax2 = plt.subplots(figsize=(4, 3))
                ax2.pie(res_v, labels=res_v.index, autopct='%1.1f%%', colors=[('#2ecc71' if i=='SI' else '#e74c3c') for i in res_v.index])
                st.pyplot(fig2)
            if st.button("Actualizar"): st.rerun()
        elif ya_voto: st.success("Voto registrado con exito."); time.sleep(3); st.rerun()
        elif fase == "votacion":
            t_r = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()
            if t_r > 0:
                st.error(f"⏱️ CIERRE EN: {int(t_r)} seg")
                c_si, c_no = st.columns(2)
                if c_si.button("SI", use_container_width=True, key="vs"):
                    servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": st.session_state.mi_casa, "representa": st.session_state.num_votos, "casas_detalle": st.session_state.detalle_votos, "p_id": p_id, "voto": "SI"}])], ignore_index=True)
                    st.rerun()
                if c_no.button("NO", use_container_width=True, key="vn"):
                    servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": st.session_state.mi_casa, "representa": st.session_state.num_votos, "casas_detalle": st.session_state.detalle_votos, "p_id": p_id, "voto": "NO"}])], ignore_index=True)
                    st.rerun()
                time.sleep(1); st.rerun()
            else: st.warning("Tiempo terminado."); time.sleep(2); st.rerun()

    if st.button("Cerrar Sesion"):
        if st.session_state.mi_casa in servidor['conectados']: del servidor['conectados'][st.session_state.mi_casa]
        del st.session_state.mi_casa
        st.rerun()
