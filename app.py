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

# --- 3. DEFINICION DE PREGUNTAS Y OPCIONES ---
# Estructura: "Texto de la pregunta": [Lista de opciones]
cuestionario = [
    {"p": "1. Aprueba usted el orden del dia?", "o": ["SI", "NO"]},
    {"p": "2. Aprueba la eleccion del presidente de la Asamblea?", "o": ["SI", "NO"]},
    {"p": "3. Aprueba la eleccion de la secretaria de la Asamblea?", "o": ["SI", "NO"]},
    {"p": "4. Aprueba esta eleccion de consejo del ano 2026?", "o": ["SI", "NO"]},
    {"p": "5. Aprueba esta eleccion del comite de convivencia del 2026?", "o": ["SI", "NO"]},
    {"p": "6. Aprueba el manual de convivencia propuesto?", "o": ["SI", "NO"]},
    {"p": "7. Aprueba los Estados Financieros del ano 2025?", "o": ["SI", "NO"]},
    {"p": "8. Por cual de siguientes opciones esta a favor del incremento de la cuota de administracion?", 
     "o": ["A. $104.000", "B. $75.000", "C. $78.000"]},
    {"p": "9. Aprueba los incrementos en los valores de las zonas comunes?", "o": ["SI", "NO"]},
    {"p": "10. Aprueban el Presupuesto de 2026?", "o": ["SI", "NO"]},
    {"p": "11. Aprueba las restricciones planteadas con las personas en mora?", "o": ["SI", "NO"]},
    {"p": "12. A partir de cuantos meses en mora se aplican restricciones?", 
     "o": ["A. 3 Meses", "B. 4 Meses", "C. 5 Meses"]}
]

# --- 4. FUNCION PDF ---
def generar_pdf_quorum(datos_conectados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "REPORTE DE QUORUM - ALAMEDA 7", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(30, 10, "Casa Lider", 1)
    pdf.cell(25, 10, "Votos", 1)
    pdf.cell(135, 10, "Detalle de Casas Representadas", 1)
    pdf.ln()
    pdf.set_font("Arial", size=10)
    for k, v in sorted(datos_conectados.items(), key=lambda x: int(x[0])):
        pdf.cell(30, 10, str(k), 1)
        pdf.cell(25, 10, str(v[0]), 1)
        pdf.cell(135, 10, str(v[1]), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 5. CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display:none !important;}
    [data-testid="stHeader"] {display:none !important;}
    [data-testid="sidebar-button"] {display: none !important;}
    .titulo-v { font-size: 26px !important; font-weight: bold; text-align: center; color: #1E1E1E; padding: 10px 0; }
    .stButton>button { border-radius: 10px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 6. IDENTIFICACION ---
if 'mi_casa' not in st.session_state and 'admin_logueado' not in st.session_state:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("image_f94506.jpg"): st.image("image_f94506.jpg", use_container_width=True)
        else: st.title("ALAMEDA 7")
    st.divider()
    rol = st.radio("Acceso:", ["Votante", "Administrador"], horizontal=True, label_visibility="collapsed")
    
    if rol == "Votante":
        with st.form("login_v"):
            casa_lider_n = st.number_input("Su Casa Principal (1-184):", min_value=1, max_value=TOTAL_CASAS, step=1)
            detalle_c = st.text_input("Otras casas que representa (Numeros separados por coma):")
            if st.form_submit_button("INGRESAR A VOTAR", use_container_width=True):
                casa_lider = str(int(casa_lider_n))
                casas_ocupadas = set()
                for lider, data in servidor['conectados'].items():
                    for p in [x.strip() for x in data[1].split(',') if x.strip()]: casas_ocupadas.add(p)

                if casa_lider in casas_ocupadas:
                    st.error(f"La casa {casa_lider} ya esta registrada. Pida al admin liberarla si cerro sesion por error.")
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
                        st.session_state.update({"mi_casa": casa_lider, "num_votos": podes_calc, "detalle_votos": texto_final})
                        servidor['conectados'][casa_lider] = [podes_calc, texto_final]
                        st.rerun()
    else:
        with st.form("login_a"):
            clave = st.text_input("Clave Admin:", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
                if clave == "Alameda2026*": st.session_state.admin_logueado = True; st.rerun()
                else: st.error("Invalida.")
    st.stop()

# --- 7. VISTA ADMINISTRADOR ---
if 'admin_logueado' in st.session_state:
    c_t = st.columns([1, 1, 1, 1.5])
    if c_t[0].button("Refrescar"): st.rerun()
    if c_t[1].button("Reset"): 
        servidor.update({"votos": pd.DataFrame(columns=["casa", "representa", "casas_detalle", "p_id", "voto"]), "conectados": {}, "asamblea_iniciada": False, "asamblea_cerrada": False, "fase": "espera"})
        st.rerun()
    if c_t[2].button("Salir"): del st.session_state.admin_logueado; st.rerun()
    if not servidor["asamblea_cerrada"] and c_t[3].button("CERRAR ASAMBLEA"):
        servidor["asamblea_cerrada"] = True; st.rerun()

    votos_totales = sum(v[0] for v in servidor["conectados"].values())
    st.metric("Quorum", f"{(votos_totales/TOTAL_CASAS)*100:.1f}%", f"{votos_totales} de {TOTAL_CASAS} votos")
    
    with st.expander("Gestion de Quorum y Asistencia"):
        if servidor["conectados"]:
            casa_a_liberar = st.selectbox("Liberar casa para re-ingreso:", [""] + list(servidor['conectados'].keys()))
            if st.button("LIBERAR") and casa_a_liberar:
                del servidor['conectados'][casa_a_liberar]; st.rerun()
            st.table(pd.DataFrame([{"Casa": k, "Votos": v[0], "Detalle": v[1]} for k, v in servidor['conectados'].items()]).sort_values("Casa", key=lambda x: x.astype(int)))
            pdf_bytes = generar_pdf_quorum(servidor["conectados"])
            st.download_button("Exportar Quorum PDF", data=pdf_bytes, file_name="Quorum_Alameda7.pdf", mime="application/pdf")

    if not servidor["asamblea_cerrada"]:
        if not servidor["asamblea_iniciada"]:
            if st.button("ABRIR ASAMBLEA", type="primary", use_container_width=True):
                servidor["asamblea_iniciada"] = True; st.rerun()
        else:
            sel_p = st.selectbox("Pregunta a lanzar:", range(len(cuestionario)), format_func=lambda x: cuestionario[x]["p"])
            seg = st.slider("Segundos:", 30, 300, 60)
            cl, cr = st.columns(2)
            if cl.button("LANZAR PREGUNTA", type="primary", use_container_width=True):
                servidor.update({'p_idx': sel_p, 'fase': "votacion", 'tiempo_cierre': datetime.now() + timedelta(seconds=seg)}); st.rerun()
            if cr.button("PUBLICAR RESULTADOS", use_container_width=True):
                servidor['fase'] = "resultados"; st.rerun()

    v_p = servidor['votos'][servidor['votos']['p_id'] == servidor['p_idx']]
    if not v_p.empty:
        st.markdown(f"### Resultados: {cuestionario[servidor['p_idx']]['p']}")
        res = v_p.groupby('voto')['representa'].sum()
        fig, ax = plt.subplots(figsize=(4, 2))
        ax.pie(res, labels=res.index, autopct='%1.1f%%', startangle=90)
        st.pyplot(fig)
        st.dataframe(v_p[['casa', 'representa', 'voto']].sort_values("casa", key=lambda x: x.astype(int)), hide_index=True)
        st.download_button("Descargar Excel", data=servidor['votos'].to_csv(index=False).encode('utf-8'), file_name="Reporte_Alameda7.csv")

# --- 8. VISTA VOTANTE ---
else:
    if servidor["asamblea_cerrada"]:
        st.success("ASAMBLEA FINALIZADA"); st.markdown("<div class='titulo-v'>¡Gracias por su participacion!</div>", unsafe_allow_html=True)
        if st.button("Cerrar Sesion"):
            if st.session_state.mi_casa in servidor['conectados']: del servidor['conectados'][st.session_state.mi_casa]
            del st.session_state.mi_casa; st.rerun()
        st.stop()

    st.info(f"Casa: {st.session_state.mi_casa} | Votos: {st.session_state.num_votos}")
    
    if not servidor["asamblea_iniciada"]:
        st.warning("Esperando apertura..."); time.sleep(2); st.rerun()
    
    fase, p_id = servidor['fase'], servidor['p_idx']
    pregunta_actual = cuestionario[p_id]
    
    if fase == "espera": st.info("Preparando siguiente votacion..."); time.sleep(2); st.rerun()
    else:
        st.markdown(f"<div class='titulo-v'>{pregunta_actual['p']}</div>", unsafe_allow_html=True)
        ya_voto = not servidor['votos'][(servidor['votos']['casa'] == st.session_state.mi_casa) & (servidor['votos']['p_id'] == p_id)].empty
        
        if fase == "resultados":
            v_v = servidor['votos'][servidor['votos']['p_id'] == p_id]
            if not v_v.empty:
                res_v = v_v.groupby('voto')['representa'].sum()
                fig2, ax2 = plt.subplots(figsize=(4, 3))
                ax2.pie(res_v, labels=res_v.index, autopct='%1.1f%%')
                st.pyplot(fig2)
            if st.button("Actualizar"): st.rerun()
        elif ya_voto: st.success("Voto registrado con exito."); time.sleep(3); st.rerun()
        elif fase == "votacion":
            t_r = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()
            if t_r > 0:
                st.error(f"TIEMPO: {int(t_r)} seg")
                # GENERACION DINAMICA DE BOTONES SEGUN LA PREGUNTA
                opciones = pregunta_actual["o"]
                cols = st.columns(len(opciones))
                for i, opcion in enumerate(opciones):
                    if cols[i].button(opcion, use_container_width=True, key=f"btn_{i}"):
                        servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": st.session_state.mi_casa, "representa": st.session_state.num_votos, "casas_detalle": st.session_state.detalle_votos, "p_id": p_id, "voto": opcion}])], ignore_index=True)
                        st.rerun()
                time.sleep(1); st.rerun()
            else: st.warning("Tiempo agotado."); time.sleep(2); st.rerun()

    if st.button("Cerrar Sesion"):
        if st.session_state.mi_casa in servidor['conectados']: del servidor['conectados'][st.session_state.mi_casa]
        del st.session_state.mi_casa; st.rerun()
