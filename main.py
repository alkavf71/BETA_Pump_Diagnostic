import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- IMPORT MODULES ---
from modules.asset_database import get_asset_list, get_asset_details
from modules.inspection.mechanical import MechanicalInspector
from modules.inspection.electrical import ElectricalInspector
# (Jika Anda sudah buat file noise_quantitative.py, import di sini. Jika belum, pakai logic sederhana di bawah)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Reliability Pro Enterprise", layout="wide", page_icon="🏭")

# --- CSS UTILS ---
def highlight_row(row):
    if "ZONE D" in row.get('Remark', ''): 
        return ['background-color: #ffebee; color: #b71c1c']*len(row)
    elif "ZONE C" in row.get('Remark', ''): 
        return ['background-color: #fffde7; color: #f57f17']*len(row)
    elif "ZONE A" in row.get('Remark', ''): 
        return ['background-color: #e8f5e9; color: #1b5e20; font-weight: bold']*len(row)
    else: 
        return ['background-color: #ffffff; color: #212529']*len(row)

# ==============================================================================
# SIDEBAR: ASSET SELECTION
# ==============================================================================
st.sidebar.title("🏭 Reliability Pro")
st.sidebar.subheader("Asset Selection")

asset_names = get_asset_list()
selected_tag = st.sidebar.selectbox("Pilih Aset / Tag Number:", asset_names)
asset = get_asset_details(selected_tag)

with st.sidebar.expander("ℹ️ Spesifikasi Aset", expanded=True):
    st.markdown(f"**Nama:** {asset.name}")
    st.markdown(f"**Type:** {asset.pump_type}")
    st.markdown(f"**Power:** {asset.power_kw} kW")
    st.markdown(f"**RPM:** {asset.rpm}")
    st.markdown(f"**Elec:** {asset.volt_rated}V / {asset.fla_rated}A")
    st.markdown("---")
    st.markdown(f"**ISO Limit:** `{asset.vib_limit_warning} / {asset.vib_limit_alarm} mm/s`")

mode = st.sidebar.radio("Mode Aplikasi:", ["🛠️ INSPEKSI RUTIN", "🚀 COMMISSIONING"])

# ==============================================================================
# MODE 1: INSPEKSI RUTIN
# ==============================================================================
if mode == "🛠️ INSPEKSI RUTIN":
    st.title(f"🛠️ Inspeksi Rutin: {asset.tag}")

    # Init Inspectors
    mech_inspector = MechanicalInspector(vib_limit_warn=asset.vib_limit_warning)
    elec_inspector = ElectricalInspector()

    # Tab Menu
    tab1, tab2, tab3 = st.tabs(["⚙️ MEKANIKAL & NOISE", "⚡ ELEKTRIKAL", "👁️ VISUAL"])

    # --- TAB 1: MEKANIKAL (VIBRASI + SUHU + NOISE) ---
    with tab1:
        st.info(f"Limit vibrasi: **{asset.vib_limit_warning} mm/s** (ISO 20816).")
        
        with st.form("mech_form"):
            col1, col2 = st.columns(2)
            
            # INPUT DRIVER
            with col1:
                st.subheader("1. Driver (Motor)")
                c1a, c1b = st.columns(2)
                with c1a:
                    st.caption("Drive End (DE)")
                    m_de_h = st.number_input("M-DE Horiz", 0.8)
                    m_de_v = st.number_input("M-DE Vert", 0.2)
                    m_de_a = st.number_input("M-DE Axial", 0.5)
                    t_m_de = st.number_input("Temp M-DE (°C)", 45.0)
                with c1b:
                    st.caption("Non-Drive End (NDE)")
                    m_nde_h = st.number_input("M-NDE Horiz", 0.9)
                    m_nde_v = st.number_input("M-NDE Vert", 0.3)
                    m_nde_a = st.number_input("M-NDE Axial", 0.4)
                    t_m_nde = st.number_input("Temp M-NDE (°C)", 42.0)

            # INPUT DRIVEN
            with col2:
                st.subheader("2. Driven (Pump)")
                c2a, c2b = st.columns(2)
                with c2a:
                    st.caption("Drive End (DE)")
                    p_de_h = st.number_input("P-DE Horiz", 1.2)
                    p_de_v = st.number_input("P-DE Vert", 0.8)
                    p_de_a = st.number_input("P-DE Axial", 0.6)
                    t_p_de = st.number_input("Temp P-DE (°C)", 40.0)
                with c2b:
                    st.caption("Non-Drive End (NDE)")
                    p_nde_h = st.number_input("P-NDE Horiz", 0.7)
                    p_nde_v = st.number_input("P-NDE Vert", 0.4)
                    p_nde_a = st.number_input("P-NDE Axial", 0.3)
                    t_p_nde = st.number_input("Temp P-NDE (°C)", 38.0)
            
            st.markdown("---")
            st.subheader("3. Pengecekan Suara (Noise)")
            nc1, nc2 = st.columns(2)
            with nc1:
                current_dba = st.number_input("Sound Level (dBA):", value=80.0, step=0.1)
            with nc2:
                baseline_dba = st.number_input("Baseline (dBA):", value=78.0, step=0.1, help="Nilai referensi mesin normal")
                
            # Input tambahan untuk diagnosa suara spesifik
            noise_type = st.selectbox("Jenis Suara (Jika Abnormal):", 
                                      ["Normal / Halus", "Kavitasi / Kerikil", "Bearing Defect / Gemuruh", "Mencicit / Squealing"])

            submit_mech = st.form_submit_button("🔍 ANALISA MEKANIKAL")

        # HASIL MEKANIKAL
        if submit_mech:
            inputs_vib = {
                'm_de_h': m_de_h, 'm_de_v': m_de_v, 'm_de_a': m_de_a,
                'm_nde_h': m_nde_h, 'm_nde_v': m_nde_v, 'm_nde_a': m_nde_a,
                'p_de_h': p_de_h, 'p_de_v': p_de_v, 'p_de_a': p_de_a,
                'p_nde_h': p_nde_h, 'p_nde_v': p_nde_v, 'p_nde_a': p_nde_a
            }
            inputs_temp = {'Motor DE': t_m_de, 'Motor NDE': t_m_nde, 'Pump DE': t_p_de, 'Pump NDE': t_p_nde}

            # Panggil Logic Inspector
            result = mech_inspector.analyze_full_health(inputs_vib, inputs_temp, noise_type)
            
            st.divider()
            res_c1, res_c2 = st.columns([2, 1])
            
            with res_c1:
                st.subheader("📋 Laporan Kondisi Mesin")
                st.dataframe(result['dataframe'].style.apply(highlight_row, axis=1), use_container_width=True, hide_index=True)
                
                # Logic Noise (Simple Check di Main)
                delta_db = current_dba - baseline_dba
                if delta_db >= 6.0:
                    st.warning(f"🔊 **NOISE WARNING:** Naik +{delta_db:.1f} dB. Indikasi degradasi mekanis.")
                elif current_dba > 85.0:
                    st.error(f"🔊 **SAFETY:** {current_dba} dBA (Wajib Earplug - OSHA).")

                if result['faults']:
                    st.error("🚨 **DIAGNOSA KERUSAKAN:**")
                    for f in result['faults']:
                        with st.expander(f"⚠️ {f['name']} (Detail)", expanded=True):
                            st.info(f"**Pemicu:** {f.get('trigger', '-')}")
                            st.markdown(f"**Analisa:** {f['desc']}")
                            st.markdown(f"**Action:** {f['action']}")
                else:
                    st.success("✅ Mekanikal Sehat (Vibrasi & Suhu Normal).")

            with res_c2:
                # Gauge Vibrasi
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number", value = result['max_vib'], title = {'text': "Max Vib (mm/s)"},
                    gauge = {
                        'axis': {'range': [0, asset.vib_limit_alarm * 1.5]},
                        'bar': {'color': "black"},
                        'steps': [
                            {'range': [0, asset.vib_limit_warning], 'color': "#e8f5e9"},
                            {'range': [asset.vib_limit_warning, asset.vib_limit_alarm], 'color': "#fffde7"},
                            {'range': [asset.vib_limit_alarm, asset.vib_limit_alarm * 1.5], 'color': "#ffebee"}
                        ],
                        'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': asset.vib_limit_warning}
                    }
                ))
                fig.update_layout(height=250, margin=dict(t=30,b=20,l=20,r=20))
                st.plotly_chart(fig, use_container_width=True)

    # --- TAB 2: ELEKTRIKAL (IEC 60034) ---
    with tab2:
        st.info(f"Analisa Elektrikal untuk Motor: **{asset.name}** | Rated: **{asset.volt_rated}V / {asset.fla_rated}A**")
        
        with st.form("elec_form"):
            ce1, ce2 = st.columns(2)
            with ce1:
                st.subheader("1. Input Tegangan (Volt)")
                v_rs = st.number_input("Voltage R-S", value=float(asset.volt_rated), step=1.0)
                v_st = st.number_input("Voltage S-T", value=float(asset.volt_rated), step=1.0)
                v_tr = st.number_input("Voltage T-R", value=float(asset.volt_rated), step=1.0)
            with ce2:
                st.subheader("2. Input Arus (Ampere)")
                i_r = st.number_input("Current R", value=float(asset.fla_rated)*0.8, step=0.1)
                i_s = st.number_input("Current S", value=float(asset.fla_rated)*0.8, step=0.1)
                i_t = st.number_input("Current T", value=float(asset.fla_rated)*0.8, step=0.1)
                
            submit_elec = st.form_submit_button("⚡ ANALISA KUALITAS DAYA")

        if submit_elec:
            # Panggil Logic Inspector
            vol_inputs = [v_rs, v_st, v_tr]
            amp_inputs = [i_r, i_s, i_t]
            
            df_elec, elec_faults, elec_status, load_pct = elec_inspector.analyze_health(
                vol_inputs, amp_inputs, asset.volt_rated, asset.fla_rated
            )
            
            st.divider()
            col_e1, col_e2 = st.columns([1.5, 1])
            
            with col_e1:
                st.subheader("📋 Parameter Listrik")
                st.dataframe(df_elec, use_container_width=True, hide_index=True)
                
                if elec_faults:
                    st.error("🚨 **TEMUAN ISU ELEKTRIKAL:**")
                    for f in elec_faults:
                         with st.expander(f"⚡ {f['name']}: {f['val']}", expanded=True):
                            st.markdown(f"**Analisa:** {f['desc']}")
                            st.markdown(f"**Action:** {f['action']}")
                else:
                    st.success("✅ Kondisi Elektrikal SEHAT (Good Health).")

            with col_e2:
                # Gauge Load
                fig_load = go.Figure(go.Indicator(
                    mode = "gauge+number", value = load_pct, title = {'text': "Motor Load (%)"},
                    gauge = {
                        'axis': {'range': [0, 125]}, 'bar': {'color': "black"},
                        'steps': [{'range': [0, 100], 'color': "#e8f5e9"}, {'range': [100, 125], 'color': "#ffcdd2"}],
                        'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 100}
                    }
                ))
                fig_load.update_layout(height=250, margin=dict(t=30,b=20,l=20,r=20))
                st.plotly_chart(fig_load, use_container_width=True)

    # --- TAB 3: VISUAL ---
    with tab3:
        st.info("Fitur Visual & Safety Check (Segera Hadir)")

# ==============================================================================
# MODE 2: COMMISSIONING
# ==============================================================================
elif mode == "🚀 COMMISSIONING":
    st.title(f"🚀 Commissioning Check: {asset.tag}")
    st.warning("Modul Commissioning sedang dalam tahap pengembangan.")
