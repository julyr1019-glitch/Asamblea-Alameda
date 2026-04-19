import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime, timedelta
from fpdf import FPDF

# --- 1. CONFIGURACION ---
st.set_page_config(page_title="Asamblea Alameda 7", layout="centered")

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

# --- 3. LOGO ---
st.markdown("<style>#MainMenu, footer, header, .stDeployButton {visibility: hidden !important;}</style>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if os.path.exists("image_f94506.jpg"): st.image("image_f94506.jpg", use_container_width=True)
    else: st.title("ALAMEDA 7")
st.divider()

# --- 4. ACCESO ---
if 'mi_casa' not in st.session_state and 'admin_logueado' not in st.session_state:
    rol = st.radio("Acceso:", ["Votante", "Administrador"], horizontal=True)
    if rol == "Votante":
        with st.form("login"):
            c_in = st.text_input("Numero de Casa:")
            v_in = st.number_input("Total Votos:", 1, 10, 1)
            det = st.text_input("Detalle (Opcional):")
            if st.form_submit_button("ENTRAR"):
                if c_in:
                    st.session_state.update({"mi_casa": c_in, "num_votos": v_in, "detalle": det})
                    servidor['conectados'][f"{c_in}_{time.time()}"] = [v_in, det]
                    st.rerun()
    else:
        with st.form("admin"):
            clave = st.text_input("Clave:", type="password")
            if st.form_submit_button("ENTRAR"):
                if clave == "Alameda2026*": st.session_state.admin_logueado = True; st.rerun()
    st.stop()

# --- 5. VISTA ADMINISTRADOR ---
if 'admin_logueado' in st.session_state:
    st.subheader("Panel Admin")
    cols = st.columns(4)
    if cols[0].button("Refrescar"): st.rerun()
    if cols[1].button("Reset"): servidor.update({"votos": pd.DataFrame(columns=["casa", "representa", "casas_detalle", "p_id", "voto"]), "conectados": {}, "asamblea_iniciada": False, "asamblea_cerrada": False, "fase": "espera"}); st.rerun()
    if cols[2].button("Salir"): del st.session_state.admin_logueado; st.rerun()
    if cols[3].button("CERRAR"): servidor["asamblea_cerrada"] = True; st.rerun()

    v_tot = sum(v[0] for v in servidor["conectados"].values())
    st.metric("Quorum", f"{v_tot} votos")

    if not servidor["asamblea_cerrada"]:
        if not servidor["asamblea_iniciada"]:
            if st.button("ABRIR ASAMBLEA", type="primary"): servidor["asamblea_iniciada"] = True; st.rerun()
        else:
            sel = st.selectbox("Pregunta:", range(len(cuestionario)), format_func=lambda x: cuestionario[x]["p"])
            seg = st.number_input("Segundos:", 30, 600, 60)
            c1, c2 = st.columns(2)
            if c1.button("LANZAR", type="primary"): servidor.update({'p_idx': sel, 'fase': "votacion", 'tiempo_cierre': datetime.now() + timedelta(seconds=seg)}); st.rerun()
            if c2.button("RESULTADOS"): servidor['fase'] = "resultados"; st.rerun()

    v_act = servidor['votos'][servidor['votos']['p_id'] == servidor['p_idx']]
    if not v_act.empty:
        res = v_act.groupby('voto')['representa'].sum()
        fig, ax = plt.subplots(figsize=(4, 2)); ax.pie(res, labels=res.index, autopct='%1.1f%%'); st.pyplot(fig)
        st.dataframe(v_act[['casa', 'voto']], hide_index=True)
        st.download_button("Excel", data=servidor['votos'].to_csv(index=False).encode('utf-8'), file_name="Reporte.csv")

# --- 6. VISTA VOTANTE ---
else:
    if servidor["asamblea_cerrada"]:
        st.success("FINALIZADO"); st.stop()

    st.write(f"Casa: {st.session_state.mi_casa} | Votos: {st.session_state.num_votos}")
    if not servidor["asamblea_iniciada"]:
        st.warning("Esperando inicio..."); time.sleep(5); st.rerun()
    
    fase, p_id = servidor['fase'], servidor['p_idx']
    p_txt = cuestionario[p_id]
    
    if fase == "espera": st.info("Esperando pregunta..."); time.sleep(5); st.rerun()
    else:
        st.subheader(p_txt['p'])
        v_hecho = not servidor['votos'][(servidor['votos']['casa'] == st.session_state.mi_casa) & (servidor['votos']['p_id'] == p_id)].empty
        
        if fase == "resultados":
            v_v = servidor['votos'][servidor['votos']['p_id'] == p_id]
            if not v_v.empty:
                res_v = v_v.groupby('voto')['representa'].sum()
                fig2, ax2 = plt.subplots(figsize=(4, 2)); ax2.pie(res_v, labels=res_v.index, autopct='%1.1f%%'); st.pyplot(fig2)
            st.button("Actualizar")
        elif v_hecho: st.success("Voto OK. Espere resultados."); time.sleep(10); st.rerun()
        elif fase == "votacion":
            t_r = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()
            if t_r > 0:
                st.error(f"CIERRE EN: {int(t_r)}s")
                opc = p_txt["o"]
                for i, o in enumerate(opc):
                    if st.button(o, key=f"v_{i}", use_container_width=True):
                        servidor['votos'] = pd.concat([servidor['votos'], pd.DataFrame([{"casa": st.session_state.mi_casa, "representa": st.session_state.num_votos, "p_id": p_id, "voto": o}])], ignore_index=True)
                        st.rerun()
                time.sleep(5); st.rerun()
            else: st.warning("Fin del tiempo."); time.sleep(5); st.rerun()
    if st.button("Salir"): del st.session_state.mi_casa; st.rerun()
