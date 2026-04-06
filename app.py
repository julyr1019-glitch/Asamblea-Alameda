import streamlit as st
import pandas as pd
import os
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Asamblea Alameda 7", page_icon="🏢")
DB_VOTOS = "votos_asamblea.csv"
ARCHIVO_ESTADO = "estado.txt" # Aquí guardamos qué pregunta está activa

# Funciones de lectura/escritura de estado
def set_estado(pregunta_id, mostrar_res):
    with open(ARCHIVO_ESTADO, "w") as f:
        f.write(f"{pregunta_id}|{mostrar_res}")

def get_estado():
    if not os.path.exists(ARCHIVO_ESTADO):
        return 0, False
    with open(ARCHIVO_ESTADO, "r") as f:
        data = f.read().split("|")
        return int(data[0]), data[1] == "True"

# Inicializar archivo de votos
if not os.path.exists(DB_VOTOS):
    pd.DataFrame(columns=["casa", "pregunta", "voto"]).to_csv(DB_VOTOS, index=False)

# --- PREGUNTAS ---
preguntas = [
    "1. ¿Aprueba la elección del Consejo de Administración por planchas?",
    "2. ¿Aprueba la elección del Comité de Convivencia por planchas?",
    "3. ¿Autoriza la pintura de la fachada de ladrillo?",
    "4. ¿Está de acuerdo con la 'cerca viva'?",
    "5. ¿Aprueba el nuevo Manual de Convivencia?",
    "6. ¿Aprueba el decomiso preventivo de objetos?",
    "7. ¿Aprueba cuota extraordinaria para canales?",
    "8. ¿Acuerda el encerramiento de la malla del parqueadero?"
]

# --- LOGO ---
if os.path.exists("image_f94506.jpg"):
    st.image("image_f94506.jpg", use_container_width=True)

# --- NAVEGACIÓN ---
rol = st.sidebar.radio("Rol:", ["Votante", "Administrador"])

# --- MODO ADMINISTRADOR ---
if rol == "Administrador":
    st.header("👨‍💼 Panel de Control")
    clave = st.text_input("Contraseña:", type="password")
    
    if clave == "Alameda2026*":
        p_activa_actual, res_actual = get_estado()
        
        nueva_p = st.selectbox("Pregunta a lanzar:", range(len(preguntas)), index=p_activa_actual, format_func=lambda x: preguntas[x])
        ver_res = st.checkbox("Mostrar resultados a todos", value=res_actual)
        
        if st.button("🚀 ACTUALIZAR PARA TODOS LOS CELULARES"):
            set_estado(nueva_p, ver_res)
            st.success(f"Lanzada: Pregunta {nueva_p + 1}")
            time.sleep(1)
            st.rerun()

        st.divider()
        if st.button("🗑️ Borrar todos los votos (Reiniciar Asamblea)"):
            pd.DataFrame(columns=["casa", "pregunta", "voto"]).to_csv(DB_VOTOS, index=False)
            st.warning("Votos eliminados.")

# --- MODO VOTANTE ---
else:
    # 1. Leer estado del servidor
    p_idx, ver_grafico = get_estado()
    
    # Identificación persistente en la sesión del celular
    if 'mi_casa' not in st.session_state:
        st.subheader("Identificación")
        casa_input = st.text_input("Número de Casa (1-184):").strip()
        if st.button("Entrar"):
            if casa_input:
                st.session_state.mi_casa = casa_input
                st.rerun()
    else:
        casa = st.session_state.mi_casa
        st.sidebar.write(f"🏠 Casa: {casa}")
        
        st.subheader(f"Pregunta {p_idx + 1}")
        st.markdown(f"**{preguntas[p_idx]}**")
        
        # Leer votos reales del archivo
        df_votos = pd.read_csv(DB_VOTOS)
        ya_voto = not df_votos[(df_votos['casa'].astype(str) == casa) & (df_votos['pregunta'] == preguntas[p_idx])].empty
        
        if ver_grafico:
            st.success("📊 Resultados en tiempo real:")
            conteo = df_votos[df_votos['pregunta'] == preguntas[p_idx]]['voto'].value_counts()
            if not conteo.empty:
                st.bar_chart(conteo)
            else:
                st.write("No hay votos aún.")
            if st.button("🔄 Actualizar Resultados"): st.rerun()
            
        elif ya_voto:
            st.warning("Voto registrado. Esperando siguiente pregunta...")
            if st.button("🔄 Buscar nueva pregunta"): st.rerun()
            
        else:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ SÍ", use_container_width=True):
                    nuevo = pd.DataFrame([{"casa": casa, "pregunta": preguntas[p_idx], "voto": "SÍ"}])
                    nuevo.to_csv(DB_VOTOS, mode='a', header=False, index=False)
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
            with c2:
                if st.button("❌ NO", use_container_width=True):
                    nuevo = pd.DataFrame([{"casa": casa, "pregunta": preguntas[p_idx], "voto": "NO"}])
                    nuevo.to_csv(DB_VOTOS, mode='a', header=False, index=False)
                    time.sleep(1)
                    st.rerun()
