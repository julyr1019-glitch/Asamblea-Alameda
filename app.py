# --- VISTA VOTANTE (CON RELOJ ANIMADO) ---
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
        
        # --- LÓGICA DE SINCRONIZACIÓN Y RELOJ ---
        fase = servidor['fase']
        p_id = servidor['p_idx']

        if not servidor["asamblea_iniciada"]:
            st.warning("⏳ Esperando inicio de la sesión...")
            time.sleep(2) # Espera un poco antes de refrescar
            st.rerun()
        
        elif fase == "espera":
            st.info("⌛ El administrador está preparando la siguiente pregunta...")
            time.sleep(3)
            st.rerun()
            
        else:
            st.subheader(f"Pregunta {p_id + 1}")
            st.info(preguntas[p_id])

            # CONTENEDOR PARA EL RELOJ DINÁMICO
            placeholder_reloj = st.empty()

            df = servidor['votos']
            ya_voto = not df[(df['casa'] == casa) & (df['p_id'] == p_id)].empty

            # Si está en fase de votación y NO ha votado, calculamos el tiempo
            if fase == "votacion" and not ya_voto:
                restante = (servidor['tiempo_cierre'] - datetime.now()).total_seconds()
                
                if restante > 0:
                    placeholder_reloj.error(f"⏱️ TIEMPO RESTANTE: {int(restante)} segundos")
                    # Esto hace que la página se refresque sola cada 1 segundo para mover el reloj
                    time.sleep(1)
                    st.rerun()
                else:
                    placeholder_reloj.warning("⌛ El tiempo de votación ha terminado.")
                    fase = "espera" # Bloquea visualmente

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
                st.success("✅ Voto registrado. Espere la siguiente instrucción.")
                time.sleep(5) # Refresco lento mientras espera
                st.rerun()

            elif fase == "votacion":
                # --- BOTONES DE VOTACIÓN ---
                if p_id == 8: # Pregunta 9
                    for op in opciones_p9:
                        if st.button(f"Opción: {op}", use_container_width=True):
                            nuevo = pd.DataFrame([{"casa": casa, "representa": repre, "p_id": p_id, "voto": op}])
                            servidor['votos'] = pd.concat([servidor['votos'], nuevo], ignore_index=True)
                            st.balloons()
                            st.rerun()
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
