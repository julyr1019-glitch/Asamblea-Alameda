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
        "fase": "espera", 
        "p_idx": 0,
        "votos": pd.DataFrame(columns=["casa", "representa", "p_id", "voto"]),
        "conectados": {}, 
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
    "9. ¿De estas tres opciones de cuota de administración está de acuerdo?",
    "10. ¿Aprueban la App para la votación en la Asamblea General de Alameda 7?"
]
opciones_p9 = ["70.000", "75.000", "85.000"]

# --- 4. LOGO ---
if os.path.exists("image_f94506.jpg"):
    st.image("image_f94506.jpg", use_container_width=True)
else:
    st.title("🏢 Asamblea Alameda 7")

st.divider()

# --- 5. NAVEGACIÓN LATERAL ---
# Usamos un ID único para que no se pierda al recargar
rol = st.sidebar.radio("SISTEMA DE ASAMBLEA", ["Votante", "Administrador"], key="main_nav_radio")

# --- VISTA ADMINISTRADOR ---
if rol == "Administrador":
    st.header("👨‍💼 Panel de Mando (Admin)")
    clave = st.text_input("Contraseña Maestro:", type="password", key="admin_pass_input")
    
    if clave == "Alameda2026*":
        # MONITOR DE QUÓRUM
        casas_presentes = sum(servidor["conectados"].values())
        porcentaje_quorum = (casas_presentes / TOTAL_CASAS) * 100
        st.subheader(f"📊 Quórum Actual: {porcentaje_quorum:.1f}%")
        st.progress(min(porcentaje_quorum / 100, 1.0))
        st.write(f"Casas representadas: {casas_presentes} de {TOTAL_CASAS}")
        
        if not servidor["asamblea_iniciada"]:
            st.info("La asamblea está detenida.")
            if st.button("🚀 INICIAR ASAMBLEA GENERAL", type="primary", use_container_width=True):
                servidor["asamblea_iniciada"] = True
                st.success("¡Asamblea Iniciada!")
                st.rerun()
        else:
            st.success("✅ Asamblea en curso")
            sel_p = st.selectbox("Gestionar Pregunta:", range(len(preguntas)), 
                                 index=servidor['p_idx'], format_func=lambda x: preguntas[x])
            segundos = st.slider("Segundos de votación:", 30, 300, 60)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📢 LANZAR PREGUNTA", type="primary", use_container_width=True):
                    servidor['p_idx'] = sel_p
                    servidor['fase'] = "votacion"
                    servidor['tiempo_cierre'] = datetime.now() + timedelta(seconds=segundos)
                    st.rerun()
            with c2:
                if st.button("📊 VER RESULTADOS", use_container_width=True):
                    servidor['fase'] = "resultados"
                    st.rerun()

            # MONITOR DE GRÁFICAS Y MATRIZ
            df_v = servidor['votos']
            votos_act = df_v[df_v['p_id'] == sel_p]
            if not votos_act.empty:
                res_sum = votos_act.groupby('voto')['representa'].sum()
                fig, ax = plt.subplots(figsize=(5,3))
                
                # Lógica de colores fija
                if sel_p == 8:
                    # Orden fijo para Pregunta 9: Verde, Azul, Rojo
                    res_sum_ord = res_sum.reindex(opciones_p9).fillna(0)
                    labels = opciones_p9
                    colors = ['#2ecc71', '#3498db', '#e74c3c']
                else:
                    # Orden para Si/No: Rojo para NO, Verde para SI
                    res_sum_ord = res_sum.sort_index()
                    labels = res_sum_ord.index.tolist()
                    color_map = {'SÍ': '#2ecc71', 'NO': '#e74c3c'}
                    colors = [color_map[l] for l in labels]
                
                ax.pie(res_sum_ord, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
                ax.axis('equal')
                st.pyplot(fig)
                
                with st.expander("Ver Matriz de Votos Detallada"):
                    pivot = df_v.pivot(index='casa', columns='p_id', values='voto')
                    pivot.columns = [f"P{i+1}" for i in pivot.columns]
                    st.dataframe(pivot.fillna("-"))
            
            csv = df_v.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Reporte Final", data=csv, file_name="resultados.csv")

# --- VISTA VOTANTE ---
else:
    # 1. Registro (Aparece siempre si no hay sesión)
    if 'mi_casa' not in st.session_state:
        st.subheader("Registro de Copropietario")
        casa_input = st.text_input("🏠 Número de Casa:", key="voter_casa_id").strip()
        poderes_input = st.number_input("¿Cuántas casas representa?", 1, 10, 1, key="voter_poderes")
        
        if st.button("Entrar a la Asamblea", type="primary", use_container_width=True):
            if casa_input:
                st.session_state.mi_casa = casa_input
                st.session_state.num_votos = poderes_input
                servidor['conectados'][casa_input] = poderes_input
                st.rerun()
            else:
                st.error("Por favor, ingrese el número de casa.")
    
    # 2. Pantalla de Asamblea (Si ya está registrado)
    else:
        casa = st.session_state.mi_casa
        repre = st.session_state.num_votos
        st.sidebar.info(f"Sesión: Casa {casa} | Votos: {repre}")
        
        if st.sidebar.button("Cerrar Sesión / Cambiar Casa"):
            del st.session_state.mi_casa
            st.rerun()

        # Chequeo de Inicio
        if not servidor["asamblea_iniciada"]:
            st.warning("⏳ La Asamblea aún no ha sido iniciada por el Administrador. Por favor, espere...")
            time.sleep(3)
            st.rerun()
        
        # Lógica de fases
        fase = servidor['fase']
        p_id = servidor['p_idx']
        
        if fase == "espera":
            st.info("⌛ El Administrador está preparando la siguiente votación...")
            time.sleep(3)
            st.rerun()
            
        else:
            st.subheader(f"Pregunta {p_id + 1}")
            st.markdown(f"**{preguntas[p_id]}**")
            
            reloj_area = st.empty()
            df = servidor['votos']
            ya_voto = not df[(df['casa'] == casa) & (df['p_id'] == p_id)].empty
            
            restante = 0
            if fase == "votacion" and servidor['tiempo_cierre']:
                restante = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()

            if fase == "resultados":
                st.success("📊 RESULTADOS ACTUALES")
                v_p = df[df['p_id'] == p_id]
                if not v_p.empty:
                    res_s = v_p.groupby('voto')['representa'].sum()
                    fig, ax = plt.subplots()
                    if p_id == 8:
                        res_s = res_s.reindex(opciones_p9).fillna(0)
                        ax.pie(res_s, labels=opciones_p9, autopct='%1.1f%%', colors=['#2ecc71', '#3498db', '#e74c3c'])
                    else:
                        res_s = res_s.sort_index()
                        l = res_s.index.tolist()
                        c = [{'SÍ': '#2ecc71', 'NO': '#e74c3c'}[i] for i in l]
                        ax.pie(res_s, labels=l, autopct='%1.1f%%', colors=c)
                    st.pyplot(fig)
                st.button("🔄 Actualizar Resultados") # No necesita rerun manual por el flujo

            elif ya_voto:
                st.success("✅ Su voto ha sido recibido correctamente.")
                time.sleep(5)
                st.rerun()

            elif fase == "votacion" and restante > 0:
                reloj_area.error(f"⏱️ TIEMPO PARA VOTAR: {int(restante)} segundos")
                
                if p_id == 8: # Pregunta 9
                    for op in opciones_p9:
                        if st.button(f"Opción: {op}", use_container_width=True, key=f"btn_p9_{op}"):
                            nuevo = pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": op}])
                            servidor['votos'] = pd.concat([servidor['votos'], nuevo], ignore_index=True)
                            st.rerun()
                else: # Resto
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ SÍ", use_container_width=True, key="btn_si_voter"):
                            nuevo = pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "SÍ"}])
                            servidor['votos'] = pd.concat([servidor['votos'], nuevo], ignore_index=True)
                            st.balloons()
                            st.rerun()
                    with c2:
                        if st.button("❌ NO", use_container_width=True, key="btn_no_voter"):
                            nuevo = pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": "NO"}])
                            servidor['votos'] = pd.concat([servidor['votos'], nuevo], ignore_index=True)
                            st.rerun()
                
                time.sleep(1)
                st.rerun()
            
            else:
                st.warning("⌛ El tiempo de votación ha terminado.")
                time.sleep(3)
