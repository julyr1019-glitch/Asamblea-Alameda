import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Asamblea Alameda 7 PRO", page_icon="🏢", layout="centered")

# --- 2. MEMORIA GLOBAL (Sincronizada) ---
@st.cache_resource
def iniciar_servidor():
    return {
        "asamblea_iniciada": False,
        "fase": "espera", # espera, votacion, resultados
        "p_idx": 0,
        "votos": pd.DataFrame(columns=["casa", "representa", "p_id", "voto"]),
        "conectados": {}, # {casa: num_votos_que_representa}
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
    "9. ¿De estas tres opciones de cuota de administración está de acuerdo?"
]
opciones_p9 = ["70.000", "75.000", "85.000"]

# --- 4. LOGO ---
if os.path.exists("image_f94506.jpg"):
    st.image("image_f94506.jpg", use_container_width=True)

st.divider()

# --- 5. NAVEGACIÓN ---
rol = st.sidebar.radio("MENÚ", ["Votante", "Administrador"])

# --- VISTA ADMINISTRADOR ---
if rol == "Administrador":
    st.header("👨‍💼 Panel de Alta Gerencia")
    clave = st.text_input("Contraseña:", type="password")
    
    if clave == "Alameda2026*":
        # MONITOR DE QUÓRUM
        casas_presentes = sum(servidor["conectados"].values())
        porcentaje_quorum = (casas_presentes / TOTAL_CASAS) * 100
        
        st.subheader(f"📊 Estado del Quórum: {porcentaje_quorum:.1f}%")
        st.progress(min(porcentaje_quorum / 100, 1.0))
        st.write(f"Casas representadas: {casas_presentes} de {TOTAL_CASAS}")
        
        if porcentaje_quorum < 51:
            st.warning("⚠️ Aún no hay quórum legal (mínimo 51%)")
        else:
            st.success("✅ Quórum legal alcanzado")

        st.divider()
        
        # CONTROL DE ASAMBLEA
        if not servidor["asamblea_iniciada"]:
            if st.button("🚀 INICIAR ASAMBLEA", type="primary", use_container_width=True):
                servidor["asamblea_iniciada"] = True
                st.rerun()
        else:
            sel_p = st.selectbox("Gestionar Pregunta:", range(len(preguntas)), 
                                 index=servidor['p_idx'], format_func=lambda x: preguntas[x])
            
            # Temporizador
            segundos = st.slider("Tiempo de votación (segundos):", 30, 300, 60)
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("📢 LANZAR PREGUNTA", type="primary", use_container_width=True):
                    servidor['p_idx'] = sel_p
                    servidor['fase'] = "votacion"
                    servidor['tiempo_cierre'] = datetime.now() + timedelta(seconds=segundos)
                    st.rerun()
            with col_b:
                if st.button("📊 PUBLICAR RESULTADOS", use_container_width=True):
                    servidor['fase'] = "resultados"
                    st.rerun()

            # MONITOR EN VIVO
            st.divider()
            df_votos = servidor['votos']
            votos_p = df_votos[df_votos['p_id'] == sel_p]
            if not votos_p.empty:
                # Sumar por representación (poderes)
                res_sum = votos_p.groupby('voto')['representa'].sum()
                fig, ax = plt.subplots(figsize=(6,4))
                col = ['#2ecc71', '#e74c3c', '#3498db'] if sel_p == 8 else ['#2ecc71', '#e74c3c']
                ax.pie(res_sum, labels=res_sum.index, autopct='%1.1f%%', startangle=90, colors=col)
                st.pyplot(fig)
                
            # EXPORTAR
            csv = df_votos.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Acta de Votos (Excel)", data=csv, file_name="acta_alameda7.csv")

# --- VISTA VOTANTE ---
else:
    if 'mi_casa' not in st.session_state:
        st.subheader("Registro de Ingreso")
        c_in = st.text_input("🏠 Número de su Casa:").strip()
        poderes = st.number_input("¿A cuántas casas representa incluyendo la suya?", 1, 10, 1)
        
        if st.button("Ingresar a la Asamblea", use_container_width=True):
            if c_in:
                st.session_state.mi_casa = c_in
                st.session_state.num_votos = poderes
                servidor['conectados'][c_in] = poderes
                st.rerun()
    else:
        casa = st.session_state.mi_casa
        repre = st.session_state.num_votos
        
        st.sidebar.info(f"Casa: {casa} | Votos: {repre}")
        if st.sidebar.button("Soporte Técnico 🛠️"):
            st.sidebar.write("📞 Contacte al Administrador: 300 XXX XXXX")

        if not servidor["asamblea_iniciada"]:
            st.warning("⏳ Esperando inicio de la sesión...")
            if st.button("🔄 Actualizar"): st.rerun()
        else:
            p_id = servidor['p_idx']
            fase = servidor['fase']
            
            # Lógica de Timer
            if fase == "votacion" and servidor['tiempo_cierre']:
                restante = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()
                if restante > 0:
                    st.error(f"⏱️ Tiempo restante para votar: {int(restante)} segundos")
                else:
                    st.warning("⌛ El tiempo de votación ha terminado. Espere resultados.")

            st.subheader(f"Pregunta {p_id + 1}")
            st.info(preguntas[p_id])

            df = servidor['votos']
            ya_voto = not df[(df['casa'] == casa) & (df['p_id'] == p_id)].empty

            if fase == "resultados":
                st.success("📊 RESULTADOS FINALES (%)")
                votos_p = df[df['p_id'] == p_id]
                if not votos_p.empty:
                    res_sum = votos_p.groupby('voto')['representa'].sum()
                    fig, ax = plt.subplots()
                    col = ['#2ecc71', '#e74c3c', '#3498db'] if p_id == 8 else ['#2ecc71', '#e74c3c']
                    ax.pie(res_sum, labels=res_sum.index, autopct='%1.1f%%', startangle=90, colors=col)
                    st.pyplot(fig)
                if st.button("🔄 Refrescar"): st.rerun()

            elif ya_voto:
                st.warning("✅ Voto registrado. Espere la siguiente pregunta.")
                if st.button("🔄 Buscar Nueva Pregunta"): st.rerun()

            elif fase == "votacion":
                # Votación especial P9
                if p_id == 8:
                    for op in opciones_p9:
                        if st.button(f"Opción: {op}", use_container_width=True):
                            nuevo = pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": op}])
                            servidor['votos'] = pd.concat([servidor['votos'], nuevo], ignore_index=True)
                            st.rerun()
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ SÍ", use_container_width=True):
                            nuevo = pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "SÍ"}])
                            servidor['votos'] = pd.concat([servidor['votos'], nuevo], ignore_index=True)
                            st.rerun()
                    with c2:
                        if st.button("❌ NO", use_container_width=True):
                            nuevo = pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "NO"}])
                            servidor['votos'] = pd.concat([servidor['votos'], nuevo], ignore_index=True)
                            st.rerun()
