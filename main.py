# --- DI BAGIAN ATAS MAIN.PY (IMPORT) ---
from modules.inspection.electrical import ElectricalInspector

# ... (Di dalam if mode == "INSPEKSI":) ...

    # --- TAB 2: ELEKTRIKAL ---
    with tab2:
        st.info(f"Analisa Elektrikal untuk Motor: **{asset.name}** | Rated: **{asset.volt_rated}V / {asset.fla_rated}A**")
        
        with st.form("elec_form"):
            ce1, ce2 = st.columns(2)
            
            with ce1:
                st.subheader("1. Input Tegangan (Volt)")
                st.caption("Ukur antar fasa (Phase-to-Phase)")
                v_rs = st.number_input("Voltage R-S", value=float(asset.volt_rated), step=1.0)
                v_st = st.number_input("Voltage S-T", value=float(asset.volt_rated), step=1.0)
                v_tr = st.number_input("Voltage T-R", value=float(asset.volt_rated), step=1.0)
            
            with ce2:
                st.subheader("2. Input Arus (Ampere)")
                st.caption(f"Rated FLA: {asset.fla_rated} A")
                i_r = st.number_input("Current R", value=float(asset.fla_rated)*0.8, step=0.1)
                i_s = st.number_input("Current S", value=float(asset.fla_rated)*0.8, step=0.1)
                i_t = st.number_input("Current T", value=float(asset.fla_rated)*0.8, step=0.1)
                
            submit_elec = st.form_submit_button("⚡ ANALISA KUALITAS DAYA")

        # --- HASIL ANALISA ELEKTRIKAL ---
        if submit_elec:
            # Init Inspector
            elec_inspector = ElectricalInspector()
            
            # Panggil Logic
            vol_inputs = [v_rs, v_st, v_tr]
            amp_inputs = [i_r, i_s, i_t]
            
            df_elec, elec_faults, elec_status, load_pct = elec_inspector.analyze_health(
                vol_inputs, amp_inputs, asset.volt_rated, asset.fla_rated
            )
            
            st.divider()
            
            col_e1, col_e2 = st.columns([1.5, 1])
            
            with col_e1:
                st.subheader("📋 Tabel Parameter Listrik")
                # Highlight baris Unbalance jika tinggi
                st.dataframe(df_elec, use_container_width=True, hide_index=True)
                
                if elec_faults:
                    st.error("🚨 **TEMUAN ISU ELEKTRIKAL:**")
                    for f in elec_faults:
                         with st.expander(f"⚡ {f['name']}: {f['val']}", expanded=True):
                            st.markdown(f"**Analisa:** {f['desc']}")
                            st.markdown(f"**Action:** {f['action']}")
                else:
                    st.success("✅ **Kondisi Elektrikal SEHAT (Good Health).**")

            with col_e2:
                st.subheader("Motor Load Profile")
                
                # Gauge Load %
                fig_load = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = load_pct,
                    title = {'text': "Motor Load (%)"},
                    gauge = {
                        'axis': {'range': [0, 125]},
                        'bar': {'color': "black"},
                        'steps': [
                            {'range': [0, 80], 'color': "#e8f5e9"},  # Underload/Normal
                            {'range': [80, 100], 'color': "#a5d6a7"}, # Full Load
                            {'range': [100, 125], 'color': "#ffcdd2"} # Overload
                        ],
                        'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 100}
                    }
                ))
                fig_load.update_layout(height=250, margin=dict(t=30,b=20,l=20,r=20))
                st.plotly_chart(fig_load, use_container_width=True)
                
                # Info tambahan
                if load_pct < 40.0:
                    st.warning("⚠️ **Underload:** Motor bekerja terlalu ringan (Boros energi/Pf rendah).")
