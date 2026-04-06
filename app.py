import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Asamblea Alameda 7", page_icon="🏢")

# --- 2. MEMORIA GLOBAL (Sincroniza a los 184 usuarios) ---
@st.cache_resource
def iniciar_servidor():
    return {
        "fase": "espera", 
        "p_idx": 0,
        "votos": pd.DataFrame(columns=["casa", "p_id", "voto"]),
        "conectados": set() 
    }

servidor = iniciar_servidor()

# --- 3. LISTADO DE PREGUNTAS ---
preguntas = [
    "1. ¿Aprueba la elección del Consejo de Administración por planchas?",
    "2. ¿Aprueba la elección del Comité de Convivencia por planchas?",
    "3. ¿Autoriza la pintura de la fachada de ladrillo?",
    "4. ¿Está de acuerdo con la 'cerca viva' entre etapas?",
    "5. ¿Aprueba el nuevo Manual de Convivencia?",
    "6. ¿Aprueba el decomiso preventivo de objetos en zonas comunes?",
    "7. ¿Aprueba la cuota extraordinaria para canales de desagüe?",
    "8. ¿Acuerda el encerramiento de la malla del parqueadero?",
    "9. ¿De estas tres opciones de cuota de administración está de acuerdo?"
]

# Opciones para la pregunta 9
opciones_p9 = ["70.000", "75.000", "85.000"]

# --- 4. LOGO ---
logo = "image_f94506.jpg"
if os.path.exists(logo):
    st.image(logo, use_container_width=True)
else:
    st.title("🏢 Asamblea Alameda 7")

st.divider()

# --- 5. NAVEGACIÓN ---
rol = st.sidebar.radio("SISTEMA DE ASAMBLEA", ["Votante", "Administrador"])

# --- VISTA ADMINISTRADOR ---
if rol == "Administrador":
    st.header("👨‍💼 Panel de Mando (Admin)")
    clave = st.text_input("Contraseña:", type="password")
    
    if clave == "Alameda2026*":
        st.success("Control Maestro Activo")
        
        # MONITOR DE CONECTADOS
        st.subheader(f"👥 En línea: {len(servidor['conectados'])} casas")
        with st.expander("Ver lista de casas conectadas"):
            st.write(", ".join(sorted(list(servidor['conectados']))))
        
        st.divider()
        
        # CONTROL DE FLUJO
        st.subheader("Control de Preguntas")
        sel_p = st.selectbox("Seleccione Pregunta para gestionar:", range(len(preguntas)), 
                             index=servidor['p_idx'], format_func=lambda x: preguntas[x])
        
        col_admin1, col_admin2 = st.columns(2)
        with col_admin1:
            if st.button("🚀 LANZAR PREGUNTA", type="primary", use_container_width=True):
                servidor['p_idx'] = sel_p
                servidor['fase'] = "votacion"
                st.rerun()
        with col_admin2:
            if st.button("📊 PUBLICAR RESULTADOS", use_container_width=True):
                servidor['fase'] = "resultados"
                st.rerun()

        # MONITOR DE GRÁFICAS PARA EL ADMIN
        st.divider()
        st.subheader(f"📈 Gráfica en Vivo (Pregunta {sel_p + 1})")
        df_admin = servidor['votos']
        res_admin = df_admin[df_admin['p_id'] == sel_p]['voto'].value_counts()
        
        if not res_admin.empty:
            fig_admin, ax_admin = plt.subplots(figsize=(6, 4))
            # Colores dinámicos (Verde/Rojo para Si/No, o Colores Variados para P9)
            colores = ['#2ecc71', '#e74c3c', '#3498db'] if sel_p == 8 else ['#2ecc71', '#e74c3c']
            ax_admin.pie(res_admin, labels=res_admin.index, autopct='%1.1f%%', startangle=90, colors=colores[:len(res_admin)])
            ax_admin.axis('equal')
            st.pyplot(fig_admin)
            st.write(f"Total votos recibidos: {res_admin.sum()}")
        else:
            st.info("Esperando votos para mostrar gráfica...")

        # EXPORTAR EXCEL
        if not servidor['votos'].empty:
            csv = servidor['votos'].to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Reporte de Votos (CSV/Excel)", data=csv, file_name="reporte_asamblea.csv")

# --- VISTA VOTANTE ---
else:
    if 'mi_casa' not in st.session_state:
        st.subheader("Registro de Ingreso")
        c_in = st.text_input("Número de Casa (1-184):").strip()
        if st.button("Entrar"):
            if c_in:
                st.session_state.mi_casa = c_in
                servidor['conectados'].add(c_in)
                st.rerun()
    else:
        casa = st.session_state.mi_casa
        fase = servidor['fase']
        p_id = servidor['p_idx']
        
        st.sidebar.info(f"Casa: {casa}")
        if st.sidebar.button("Cerrar Sesión"):
            del st.session_state.mi_casa
            st.rerun()

        if fase == "espera":
            st.warning("⏳ Esperando que la Administración lance la pregunta...")
            if st.button("🔄 Actualizar"): st.rerun()
            
        else:
            st.subheader(f"Pregunta {p_id + 1}")
            st.info(preguntas[p_id])
            
            df = servidor['votos']
            ya_voto = not df[(df['casa'] == casa) & (df['p_id'] == p_id)].empty
            
            if fase == "resultados":
                st.success("📊 RESULTADOS CONSOLIDADOS")
                res = df[df['p_id'] == p_id]['voto'].value_counts()
                if not res.empty:
                    fig, ax = plt.subplots()
                    colores = ['#2ecc71', '#e74c3c', '#3498db'] if p_id == 8 else ['#2ecc71', '#e74c3c']
                    ax.pie(res, labels=res.index, autopct='%1.1f%%', startangle=90, colors=colores[:len(res)])
                    ax.axis('equal')
                    st.pyplot(fig)
                else:
                    st.write("No hubo votos.")
                if st.button("🔄 Actualizar"): st.rerun()

            elif ya_voto:
                st.warning("✅ Voto registrado. Espere la siguiente instrucción.")
                if st.button("🔄 Buscar nueva pregunta"): st.rerun()
            
            elif fase == "votacion":
                # --- LÓGICA DIFERENTE PARA PREGUNTA 9 ---
                if p_id == 8: # Índice 8 es la Pregunta 9
                    st.write("Elija una de las tres opciones:")
                    for opcion in opciones_p9:
                        if st.button(f"Opción: {opcion}", use_container_width=True):
                            nueva_fila = pd.DataFrame([{"casa": casa, "p_id": p_id, "voto": opcion}])
                            servidor['votos'] = pd.concat([servidor['votos'], nueva_fila], ignore_index=True)
                            st.balloons()
                            st.rerun()
                # --- LÓGICA NORMAL (SÍ/NO) PARA 1-8 ---
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ SÍ", use_container_width=True):
                            nueva_fila = pd.DataFrame([{"casa": casa, "p_id": p_id, "voto": "SÍ"}])
                            servidor['votos'] = pd.concat([servidor['votos'], nueva_fila], ignore_index=True)
                            st.balloons()
                            st.rerun()
                    with c2:
                        if st.button("❌ NO", use_container_width=True):
                            nueva_fila = pd.DataFrame([{"casa": casa, "p_id": p_id, "voto": "NO"}])
                            servidor['votos'] = pd.concat([servidor['votos'], nueva_fila], ignore_index=True)
                            st.rerun()
