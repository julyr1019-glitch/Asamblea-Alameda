import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Asamblea Alameda 7 PRO", page_icon="🏢", layout="centered")

# --- 2. MEMORIA GLOBAL COMPARTIDA (Servidor Central) ---
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

# --- 3. LISTADO DE PREGUNTAS ---
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
logo_path = "image_f94506.jpg"
if os.path.exists(logo_path):
    st.image(logo_path, use_container_width=True)
else:
    st.title("🏢 Asamblea Alameda 7")

st.divider()

# --- 5. NAVEGACIÓN LATERAL ---
rol = st.sidebar.radio("SISTEMA DE ASAMBLEA", ["Votante (Copropietario)", "Administrador"])

# --- VISTA ADMINISTRADOR ---
if rol == "Administrador":
    st.header("👨‍💼 Panel de Mando (Admin)")
    clave = st.text_input("Contraseña Maestro:", type="password")
    
    if clave == "Alameda2026*":
        # --- MONITOR DE QUÓRUM ---
        casas_presentes = sum(servidor["conectados"].values())
        porcentaje_quorum = (casas_presentes / TOTAL_CASAS) * 100
        
        st.subheader(f"📊 Quórum Actual: {porcentaje_quorum:.1f}%")
        st.progress(min(porcentaje_quorum / 100, 1.0))
        st.write(f"**Casas representadas:** {casas_presentes} de {TOTAL_CASAS}")
        
        if porcentaje_quorum < 51:
            st.warning("⚠️ Sin quórum legal (mínimo 51%)")
        else:
            st.success("✅ Quórum legal alcanzado")

        st.divider()
        
        # --- CONTROL DE FLUJO ---
        if not servidor["asamblea_iniciada"]:
            if st.button("🚀 INICIAR ASAMBLEA GENERAL", type="primary", use_container_width=True):
                servidor["asamblea_iniciada"] = True
                st.rerun()
        else:
            sel_p = st.selectbox("Seleccione Pregunta:", range(len(preguntas)), 
                                 index=servidor['p_idx'], format_func=lambda x: preguntas[x])
            
            segundos = st.slider("Tiempo de votación (segundos):", 30, 300, 60)
            
            c_admin1, c_admin2 = st.columns(2)
            with c_admin1:
                if st.button("📢 LANZAR PREGUNTA", type="primary", use_container_width=True):
                    servidor['p_idx'] = sel_p
                    servidor['fase'] = "votacion"
                    servidor['tiempo_cierre'] = datetime.now() + timedelta(seconds=segundos)
                    st.rerun()
            with c_admin2:
                if st.button("📊 PUBLICAR RESULTADOS", use_container_width=True):
                    servidor['fase'] = "resultados"
                    st.rerun()

            # --- MONITOR EN VIVO (PARA EL ADMIN) ---
            st.divider()
            df_votos = servidor['votos']
            votos_actuales = df_votos[df_votos['p_id'] == sel_p]
            
            if not votos_actuales.empty:
                st.subheader(f"📈 Monitor Pregunta {sel_p + 1}")
                res_sum = votos_actuales.groupby('voto')['representa'].sum()
                fig_admin, ax_admin = plt.subplots(figsize=(6,4))
                colores = ['#2ecc71', '#e74c3c', '#3498db'] if sel_p == 8 else ['#2ecc71', '#e74c3c']
                ax_admin.pie(res_sum, labels=res_sum.index, autopct='%1.1f%%', startangle=90, colors=colores[:len(res_sum)])
                st.pyplot(fig_admin)
                
                # --- MATRIZ DE VOTOS ---
                st.subheader("📋 Matriz de Votos")
                pivot = df_votos.pivot(index='casa', columns='p_id', values='voto')
                pivot.columns = [f"P{i+1}" for i in pivot.columns]
                st.dataframe(pivot.fillna("-"))

            # EXPORTAR EXCEL
            csv = df_votos.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Reporte Final (CSV)", data=csv, file_name="reporte_asamblea.csv")

# --- VISTA VOTANTE ---
else:
    # Registro inicial
    if 'mi_casa' not in st.session_state:
        st.subheader("Registro de Ingreso")
        c_in = st.text_input("🏠 Número de Casa (1-184):").strip()
        poderes = st.number_input("¿A cuántas casas representa (incluida la suya)?", 1, 10, 1)
        
        if st.button("Entrar a la Asamblea", use_container_width=True):
            if c_in:
                st.session_state.mi_casa = c_in
                st.session_state.num_votos = poderes
                servidor['conectados'][c_in] = poderes
                st.rerun()
    else:
        casa = st.session_state.mi_casa
        repre = st.session_state.num_votos
        st.sidebar.info(f"Sesión: Casa {casa} | Votos: {repre}")
        
        # Sincronización de Fase
        fase = servidor['fase']
        p_id = servidor['p_idx']

        if not servidor["asamblea_iniciada"]:
            st.warning("⏳ Esperando inicio de la sesión...")
            time.sleep(2)
            st.rerun()
        
        elif fase == "espera":
            st.info("⌛ El administrador está preparando la siguiente pregunta...")
            time.sleep(3)
            st.rerun()
            
        else:
            st.subheader(f"Pregunta {p_id + 1}")
            st.info(preguntas[p_id])

            # --- RELOJ ANIMADO ---
            reloj_area = st.empty()
            df = servidor['votos']
            ya_voto = not df[(df['casa'] == casa) & (df['p_id'] == p_id)].empty

            if fase == "votacion" and not ya_voto:
                restante = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()
                if restante > 0:
                    reloj_area.error(f"⏱️ TIEMPO RESTANTE: {int(restante)} segundos")
                    time.sleep(1)
                    st.rerun()
                else:
                    reloj_area.warning("⌛ El tiempo de votación ha terminado.")

            # --- MOSTRAR RESULTADOS (GRÁFICA CIRCULAR) ---
            if fase == "resultados":
                st.success("📊 RESULTADOS CONSOLIDADOS (%)")
                votos_p = df[df['p_id'] == p_id]
                if not votos_p.empty:
                    res_sum = votos_p.groupby('voto')['representa'].sum()
                    fig, ax = plt.subplots()
                    colores = ['#2ecc71', '#e74c3c', '#3498db'] if p_id == 8 else ['#2ecc71', '#e74c3c']
                    ax.pie(res_sum, labels=res_sum.index, autopct='%1.1f%%', startangle=90, colors=colores[:len(res_sum)])
                    ax.axis('equal')
                    st.pyplot(fig)
                if st.button("🔄 Actualizar"): st.rerun()

            elif ya_voto:
                st.success("✅ Voto registrado con éxito.")
                time.sleep(5)
                st.rerun()

            elif fase == "votacion":
                # Botones Pregunta 9
                if p_id == 8:
                    for op in opciones_p9:
                        if st.button(f"Opción: {op}", use_container_width=True):
                            nuevo = pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": op}])
                            servidor['votos'] = pd.concat([servidor['votos'], nuevo], ignore_index=True)
                            st.balloons()
                            st.rerun()
                # Botones SÍ/NO
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ SÍ", use_container_width=True):
                            nuevo = pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "SÍ"}])
                            servidor['votos'] = pd.concat([servidor['votos'], nuevo], ignore_index=True)
                            st.balloons()
                            st.rerun()
                    with c2:
                        if st.button("❌ NO", use_container_width=True):
                            nuevo = pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "NO"}])
                            servidor['votos'] = pd.concat([servidor['votos'], nuevo], ignore_index=True)
                            st.rerun()
