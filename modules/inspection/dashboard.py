import streamlit as st
import plotly.graph_objects as go
from modules.inspection.mechanical import MechanicalInspector
from modules.inspection.electrical import ElectricalInspector
from modules.inspection.visual import VisualInspector

def run():
    st.header("🛠️ DASHBOARD INSPEKSI RUTIN")
    st.caption("Standards: ISO 20816, IEC 60034, ISO 4406, OSHA 1910, API 610")
    
    # --- TAB SETUP ---
    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ MECHANICAL (ISO/API)", "⚡ ELECTRICAL (IEC)", "👁️ VISUAL & SAFETY (OSHA)", "📝 REPORT"])
    
    # --- INSTANTIATE CLASSES ---
    # (Nilai limit bisa diambil dari database aset nantinya)
    mech_inspector = MechanicalInspector(limit_vib=4.5)
    elec_inspector = ElectricalInspector()
    vis_inspector = VisualInspector()

    # =======================================================
    # TAB 1: MEKANIKAL
    # =======================================================
    with tab1:
        st.subheader("Vibration (ISO 20816) & Pump Perf. (API 610)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**(1) Data Vibrasi (mm/s)**")
            # ... (Buat input form seperti sebelumnya disini) ...
            # Biar ringkas, saya hardcode contoh input dictionary
            # Nanti Bapak copas input form dari main.py lama ke sini
            inputs_vib = {
                'm_de_h': st.number_input("M-DE H", 0.8), 'm_de_v': 0.2, 'm_de_a': 0.5,
                'm_nde_h': 1.5, 'm_nde_v': 1.0, 'm_nde_a': 1.3,
                'p_de_h': 1.6, 'p_de_v': 1.5, 'p_de_a': 1.2,
                'p_nde_h': 0.9, 'p_nde_v': 0.5, 'p_nde_a': 0.8
            }
            st.markdown("**(2) Data Hidrolik**")
            p_in = st.number_input("P In (Bar)", 0.5)
            p_out = st.number_input("P Out (Bar)", 4.5)
            
            btn_mech = st.button("Analisa Mekanikal")

        with c2:
            if btn_mech:
                # Panggil Logic dari mechanical.py
                df_vib, status_vib, causes_vib, max_vib = mech_inspector.analyze_vibration(inputs_vib)
                head, status_hydro, note_hydro = mech_inspector.analyze_pump_hydraulic(p_in, p_out, 0.74, 60.0)
                
                st.info(f"Vibrasi Status: **{status_vib}** | Max: {max_vib} mm/s")
                st.dataframe(df_vib, use_container_width=True)
                
                st.info(f"Hydraulic Status: **{status_hydro}** | Head: {head:.1f} m")
                st.caption(note_hydro)

    # =======================================================
    # TAB 2: ELEKTRIKAL
    # =======================================================
    with tab2:
        st.subheader("Power Quality (IEC 60034-1)")
        # ... (Buat input Volt/Ampere disini) ...
        btn_elec = st.button("Analisa Elektrikal")
        
        if btn_elec:
            # Contoh Data Dummy
            res_elec = elec_inspector.analyze_health([380, 375, 382], [50, 52, 49], 60)
            st.write(res_elec)

    # =======================================================
    # TAB 3: VISUAL & SAFETY
    # =======================================================
    with tab3:
        st.subheader("Oil (ISO 4406) & Safety (OSHA 1910)")
        c_vis1, c_vis2 = st.columns(2)
        with c_vis1:
            oil_cond = st.selectbox("Kondisi Oli (Visual)", ["Clear & Bright", "Cloudy/Hazy", "Milky", "Dark/Black"])
            chk_guard = st.checkbox("Coupling Guard Terpasang? (OSHA 1910.219)", value=True)
            chk_ground = st.checkbox("Grounding Terhubung? (OSHA 1910.304)", value=True)
            chk_leak = st.checkbox("Ada Kebocoran Cairan? (ISO 14001)", value=False)
            
            btn_vis = st.button("Cek Visual & Safety")
            
        with c_vis2:
            if btn_vis:
                # Panggil Logic dari visual.py
                status_oil, std_oil = vis_inspector.analyze_oil_condition(oil_cond)
                safety_violations = vis_inspector.analyze_safety({
                    'guard_installed': chk_guard,
                    'grounding_ok': chk_ground,
                    'leakage_visible': chk_leak
                })
                
                st.markdown(f"**Analisa Oli:** {status_oil}")
                st.caption(std_oil)
                
                st.markdown("**Analisa Safety:**")
                if safety_violations:
                    for v in safety_violations:
                        st.error(f"❌ {v}")
                else:
                    st.success("✅ Compliant with ISO 45001 / OSHA")

    # =======================================================
    # TAB 4: REPORT
    # =======================================================
    with tab4:
        st.write("Disini nanti akan muncul rangkuman dari Tab 1, 2, dan 3 untuk dicetak PDF.")
