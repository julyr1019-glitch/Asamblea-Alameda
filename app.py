import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime, timedelta
from fpdf import FPDF

# --- 1. CONFIGURACION ---
st.set_page_config(page_title="Asamblea Alameda 7", page_icon="🏢", layout="centered", initial_sidebar_state="collapsed")

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

# --- 2. CUESTIONARIO ---
cuestionario = [
    {"p": "1. Aprueba usted el orden del dia?", "o": ["SI", "NO"]},
    {"p": "2. Aprueba la eleccion del presidente de la Asamblea?", "o": ["SI", "NO"]},
    {"p": "3. Aprueba la eleccion de la secretaria de la Asamblea?", "o": ["SI", "NO"]},
    {"p": "4. Aprueba la eleccion de consejo 2026?", "o": ["SI", "NO"]},
    {"p": "5. Aprueba la eleccion del comite de convivencia 2026?", "o": ["SI", "NO"]},
    {"p": "6. Aprueba el manual de convivencia propuesto?", "o": ["SI", "NO"]},
    {"p": "7. Aprueba los Estados Financieros 2025?", "o": ["SI", "NO"]},
    {"p": "8. Opcion a favor del incremento de la cuota de administracion:", "o": ["A. $104.000", "B. $75.000", "C. $78.000"]},
    {"p": "9. Aprueba los incrementos en valores de las zonas comunes?", "o": ["SI", "NO"]},
    {"p": "10. Aprueban el Presupuesto 2026?", "o": ["SI", "NO"]},
    {"p": "11. Aprueba las restricciones con las personas en mora?", "o": ["SI", "NO"]},
    {"p": "12. A partir de cuantos meses en mora se aplican restricciones?", "o": ["A. 3 Meses", "B. 4 Meses", "C. 5 Meses"]}
]

# --- 3. FUNCION PDF ---
def generar_pdf_quorum(datos_conectados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "REPORTE DE QUORUM - ALAMEDA 7", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(30, 10, "Registro", 1)
    pdf.cell(25, 10, "Votos", 1)
    pdf.cell(135, 10, "Detalle", 1)
    pdf.ln()
    pdf.set_font("Arial", size=10)
    for k, v in datos_conectados.items():
        pdf.cell(30, 10, str(k), 1)
        pdf.cell(25, 10, str(v[0]), 1)
        pdf.cell(135, 10, str(v[1]), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. CSS ---
st.markdown("<style>#MainMenu, footer, header, .stDeployButton, [data-testid='stHeader'], [data-testid='sidebar-button'] {visibility: hidden !important;} .titulo-v { font-size: 26px !important; font-weight: bold; text-align: center; color: #1E1E1E; padding: 10px 0; }</style>", unsafe_allow_html=True)

# --- 5. LOGO ---
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if os.path.exists("image_f94506.jpg"): st.image("image_f94506.jpg", use_container_width=True)
    else: st.title("ALAMEDA 7")
st.divider()

# --- 6. ACCESO ---
if 'mi_casa' not in st.session_state and 'admin_logueado' not in st.session_state:
    rol = st.radio("Acceso:", ["Votante", "Administrador"], horizontal=True, label_visibility="collapsed")
    if rol == "Votante":
        with st.form("login_v"):
            casa_lider_n = st.number_input("Su Casa Principal:", min_value=1, max_value=500, step=1, value=None)
            detalle_c = st.text_input("Otras casas que representa (Separadas por coma):")
            if st.form_submit_button("INGRESAR A VOTAR", use_container_width=True):
                if casa_lider_n:
                    casa_lider = str(int(casa_lider_n))
                    # CONTEO SIMPLE SIN RESTRICCIONES
                    adicionales = [x.strip() for x in detalle_c.replace('.',',').split(',') if x.strip()]
                    podes_calc = 1 + len(adicionales)
                    texto_final = casa_lider + (f", {', '.join(adicionales)}" if adicionales else "")
                    
                    st.session_state.update({"mi_casa": casa_lider, "num_votos": podes_calc, "detalle_votos": texto_final, "id_sesion": time.time()})
                    # Usamos un ID de sesión único para evitar choques en el diccionario global
                    servidor['conectados'][f"{casa_lider}_{st.session_state.id_sesion}"] = [podes_calc, texto_final]
                    st.rerun()
                else: st.error("Ingrese su casa.")
    else:
        with st.form("login_a"):
            clave = st.text_input("Clave Admin:", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
                if clave == "Alameda2026*": st.session_state.admin_logueado = True; st.rerun()
    st.stop()

# --- 7. VISTA ADMINISTRADOR ---
if 'admin_logueado' in st.session_state:
    c_t = st.columns([1, 1, 1, 1.5])
    if c_t[0].button("Refrescar"): st.rerun()
    if c_t[1].button("Reset"): 
        servidor.update({"votos": pd.DataFrame(columns=["casa", "representa", "casas_detalle", "p_id", "voto"]), "conectados": {}, "asamblea_iniciada": False, "asamblea_cerrada": False, "fase": "espera"})
        st.rerun()
    if c_t[2].button("Salir"): del st.session_state.admin_logueado; st.rerun()
    if not servidor["asamblea_cerrada"] and c_t[3].button("CERRAR ASAMBLEA"): servidor["asamblea_cerrada"] = True; st.rerun()

    votos_totales = sum(v[0] for v in servidor["conectados"].values())
    st.metric("Quorum Actual", f"{(votos_totales/TOTAL_CASAS)*100:.1f}%", f"{votos_totales} votos")
    
    with st.expander("Lista de Asistentes"):
        if servidor["conectados"]:
            st.table(pd.DataFrame([{"ID": k, "Votos": v[0], "Detalle": v[1]} for k, v in servidor['conectados'].items()]))
            pdf_bytes = generar_pdf_quorum(servidor["conectados"])
            st.download_button("Exportar Quorum PDF", data=pdf_bytes, file_name="Quorum.pdf")

    if not servidor["asamblea_cerrada"]:
        if not servidor["asamblea_iniciada"]:
            if st.button("ABRIR ASAMBLEA", type="primary"): servidor["asamblea_iniciada"] = True; st.rerun()
        else:
            sel_p = st.selectbox("Pregunta:", range(len(cuestionario)), format_func=lambda x: cuestionario[x]["p"])
            seg = st.slider("Segundos:", 30, 300, 60)
            cl, cr = st.columns(2)
            if cl.button("LANZAR", type="primary"): servidor.update({'p_idx': sel_p, 'fase': "votacion", 'tiempo_cierre': datetime.now() + timedelta(seconds=seg)}); st.rerun()
            if cr.button("RESULTADOS"): servidor['fase'] = "resultados"; st.rerun()

    v_p = servidor['votos'][servidor['votos']['p_id'] == servidor['p_idx']]
    if not v_p.empty:
        res = v_p.groupby('voto')['representa'].sum()
        fig, ax = plt.subplots(figsize=(4, 2)); ax.pie(res, labels=res.index, autopct='%1.1f%%'); st.pyplot(fig)
        st.dataframe(v_p[['casa', 'representa', 'voto']], hide_index=True)
        st.download_button("Descargar Excel", data=servidor['votos'].to_csv(index=False).encode('utf-8'), file_name="Reporte.csv")

# --- 8. VISTA VOTANTE ---
else:
    if servidor["asamblea_cerrada"]:
        st.success("🏁 ASAMBLEA FINALIZADA"); st.button("Salir")
        st.stop()

    st.info(f"🏠 Casa: {st.session_state.mi_casa} | 🗳️ Votos: {st.session_state.num_votos}")
    if not servidor["asamblea_iniciada"]:
        st.warning("⏳ Esperando inicio..."); time.sleep(2); st.rerun()
    
    fase, p_id = servidor['fase'], servidor['p_idx']
    pregunta_actual = cuestionario[p_id]
    
    if fase == "espera": st.info("⌛ Esperando pregunta..."); time.sleep(2); st.rerun()
    else:
        st.markdown(f"<div class='titulo-v'>{pregunta_actual['p']}</div>", unsafe_allow_html=True)
        ya_voto = not servidor['votos'][(servidor['votos']['casa'] == st.session_state.mi_casa) & (servidor['votos']['p_id'] == p_id)].empty
        
        if fase == "resultados":
            v_v = servidor['votos'][servidor['votos']['p_id'] == p_id]
            if not v_v.empty:
                res_v = v_v.groupby('voto')['representa'].sum()
                fig2, ax2 = plt.subplots(figsize=(4, 3)); ax2.pie(res_v, labels=res_v.index, autopct='%1.1f%%'); st.pyplot(fig2)
            st.button("Actualizar")
        elif ya_voto: st.success("✅ Voto recibido."); time.sleep(3); st.rerun()
        elif fase == "votacion":
            t_r = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()
            if t_r > 0:
                st.error(f"TIEMPO: {int(t_r)} seg")
                opciones = pregunta_actual["o"]
                cols = st.columns(len(opciones))
                for i, opcion in enumerate(opciones):
                    if cols[i].button(opcion, use_container_width=True, key=f"v_{i}"):
                        servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": st.session_state.mi_casa, "representa": st.session_state.num_votos, "casas_detalle": st.session_state.detalle_votos, "p_id": p_id, "voto": opcion}])], ignore_index=True)
                        st.rerun()
                time.sleep(1); st.rerun()
            else: st.warning("Tiempo agotado."); time.sleep(2); st.rerun()
    if st.button("Cerrar Sesion"): del st.session_state.mi_casa; st.rerun()
