import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Asamblea Alameda 7", page_icon="🏢")

# --- 2. MEMORIA CENTRAL (Sincroniza a todos los usuarios) ---
@st.cache_resource
def obtener_estado_asamblea():
    return {
        "asamblea_iniciada": False,
        "pregunta_actual_idx": 0,
        "mostrar_graficos": False,
        "votos_db": pd.DataFrame(columns=["casa", "pregunta_id", "voto"])
    }

estado = obtener_estado_asamblea()

# --- 3. PREGUNTAS ---
preguntas = [
    "1. ¿Aprueba la elección del Consejo de Administración por planchas?",
    "2. ¿Aprueba la elección del Comité de Convivencia por planchas?",
    "3. ¿Autoriza la pintura de la fachada de ladrillo (sujeto a recursos)?",
    "4. ¿Está de acuerdo con la 'cerca viva' entre etapas?",
    "5. ¿Aprueba el contenido del nuevo Manual de Convivencia?",
    "6. ¿Aprueba el decomiso preventivo de objetos en zonas comunes?",
    "7. ¿Aprueba la cuota extraordinaria para canales de desagüe?",
    "8. ¿Acuerda el encerramiento de la malla del parqueadero?"
]

# --- 4. LOGO ---
logo_path = "image_f94506.jpg"
if os.path.exists(logo_path):
    st.image(logo_path, use_container_width=True)
else:
    st.title("🏢 Asamblea Alameda 7")

st.divider()

# --- 5. NAVEGACIÓN ---
rol = st.sidebar.radio("ACCESO", ["Votante (Copropietario)", "Administrador"])

# --- MODO ADMINISTRADOR ---
if rol == "Administrador":
    st.header("👨‍💼 Panel de Administración")
    clave = st.text_input("Contraseña Maestro:", type="password")
    
    if clave == "Alameda2026*":
        st.success("Control de Asamblea Activado")
        
        # BOTÓN INICIAR ASAMBLEA
        if not estado["asamblea_iniciada"]:
            if st.button("🚀 INICIAR VOTACIÓN GENERAL", type="primary", use_container_width=True):
                estado["asamblea_iniciada"] = True
                st.rerun()
        else:
            st.info("Asamblea en curso...")
            
            # Control de Preguntas
            idx = st.selectbox("Lanzar Pregunta:", range(len(preguntas)), 
                               index=estado["pregunta_actual_idx"],
                               format_func=lambda x: preguntas[x])
            
            ver_res = st.toggle("Publicar Gráficos de Resultados a los Copropietarios", value=estado["mostrar_graficos"])
            
            if st.button("📢 ACTUALIZAR PREGUNTA PARA TODOS", use_container_width=True):
                estado["pregunta_actual_idx"] = idx
                estado["mostrar_graficos"] = ver_res
                st.toast("Sincronización enviada!")
            
            st.divider()
            # Exportar Excel
            st.subheader("📊 Consolidado de Votos")
            if not estado["votos_db"].empty:
                st.dataframe(estado["votos_db"])
                csv = estado["votos_db"].to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Reporte Excel (CSV)", data=csv, file_name="resultados_asamblea.csv")
            else:
                st.write("Esperando votos...")

# --- MODO VOTANTE ---
else:
    # PASO 1: Identificación (Se pide una sola vez)
    if 'mi_casa' not in st.session_state:
        st.subheader("Registro de Entrada")
        casa_input = st.text_input("🏠 Ingrese su Número de Casa (1-184):").strip()
        if st.button("Ingresar a Votar", use_container_width=True):
            if casa_input:
                st.session_state.mi_casa = casa_input
                st.rerun()
            else:
                st.error("Por favor ingrese su casa.")
    
    # PASO 2: Flujo de Votación
    else:
        casa = st.session_state.mi_casa
        st.sidebar.write(f"Conectado: Casa **{casa}**")
        
        if not estado["asamblea_iniciada"]:
            st.warning("⏳ La asamblea aún no ha iniciado. Por favor, espere indicaciones del administrador.")
            if st.button("🔄 Actualizar estado"): st.rerun()
        else:
            p_id = estado["pregunta_actual_idx"]
            texto_pregunta = preguntas[p_id]
            
            st.subheader(f"Pregunta {p_id + 1}")
            st.info(texto_pregunta)
            
            # Verificar si ya votó en esta pregunta específica
            df = estado["votos_db"]
            ya_voto = not df[(df['casa'] == casa) & (df['pregunta_id'] == p_id)].empty
            
            # MOSTRAR RESULTADOS EN TORTA
            if estado["mostrar_graficos"]:
                st.success("📊 Resultados en Tiempo Real")
                conteo = df[df['pregunta_id'] == p_id]['voto'].value_counts()
                
                if not conteo.empty:
                    # Crear Gráfico de Torta (Pie Chart)
                    fig, ax = plt.subplots()
                    colors = ['#2ecc71', '#e74c3c'] # Verde para SÍ, Rojo para NO
                    ax.pie(conteo, labels=conteo.index, autopct='%1.1f%%', startangle=90, colors=colors)
                    ax.axis('equal') 
                    st.pyplot(fig)
                else:
                    st.write("Aún no hay votos para graficar.")
                
                if st.button("🔄 Actualizar Resultados"): st.rerun()
            
            elif ya_voto:
                st.warning("✅ Voto registrado. Espere a la siguiente pregunta.")
                if st.button("🔄 Buscar Nueva Pregunta"): st.rerun()
            
            else:
                # Botones de Votación
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ SÍ", use_container_width=True):
                        nuevo = pd.DataFrame([{"casa": casa, "pregunta_id": p_id, "voto": "SÍ"}])
                        estado["votos_db"] = pd.concat([estado["votos_db"], nuevo], ignore_index=True)
                        st.balloons()
                        st.rerun()
                with c2:
                    if st.button("❌ NO", use_container_width=True):
                        nuevo = pd.DataFrame([{"casa": casa, "pregunta_id": p_id, "voto": "NO"}])
                        estado["votos_db"] = pd.concat([estado["votos_db"], nuevo], ignore_index=True)
                        st.rerun()
