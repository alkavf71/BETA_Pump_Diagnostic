import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- IMPORT MODULES (Hanya Logic & Database) ---
# Pastikan file modules/asset_database.py sudah ada isinya sesuai diskusi sebelumnya
# Pastikan file modules/inspection/mechanical.py sudah ada isinya
from modules.asset_database import get_asset_list, get_asset_details
from modules.inspection.mechanical import MechanicalInspector

# --- PAGE CONFIG ---
st.set_page_config(page_title="Reliability Pro Enterprise", layout="wide", page_icon="🏭")

# --- CSS UTILS (Agar Tabel Cantik) ---
def highlight_row(row):
    if "ZONE D" in row['Remark']: 
        return ['background-color: #ffebee; color: #b71c1c']*len(row) # Merah Pucat
    elif "ZONE C" in row['Remark']: 
        return ['background-color: #fffde7; color: #f57f17']*len(row) # Kuning Pucat
    elif "ZONE A" in row['Remark']: 
        return ['background-color: #e8f5e9; color: #1b5e20; font-weight: bold']*len(row) # Hijau Pucat
    else: 
        return ['background-color: #ffffff; color: #212529']*len(row) # Putih

# ==============================================================================
# SIDEBAR: PILIH ASET
# ==============================================================================
st.sidebar.title("🏭 Reliability Pro")
st.sidebar.subheader("Asset Selection")

# 1. Load Database
asset_names = get_asset_list()
selected_tag = st.sidebar.selectbox("Pilih Aset / Tag Number:", asset_names)
asset = get_asset_details(selected_tag)

# 2. Tampilkan Info Aset
with st.sidebar.expander("ℹ️ Spesifikasi Aset", expanded=True):
    st.markdown(f"**Nama:** {asset.name}")
    st.markdown(f"**Type:** {asset.pump_type}")
    st.markdown(f"**Power:** {asset.power_kw} kW")
    st.markdown(f"**RPM:** {asset.rpm}")
    st.markdown(f"**Mounting:** {asset.mount_type}")
    st.markdown("---")
    st.markdown(f"**ISO Limit (Warn):** `{asset.vib_limit_warning} mm/s`")
    st.markdown(f"**ISO Limit (Trip):** `{asset.vib_limit_alarm} mm/s`")

mode = st.sidebar.radio("Mode Aplikasi:", ["🛠️ INSPEKSI RUTIN", "🚀 COMMISSIONING"])

# ==============================================================================
# MODE 1: INSPEKSI RUTIN
# ==============================================================================
if mode == "🛠️ INSPEKSI RUTIN":
    st.title(f"🛠️ Inspeksi Rutin: {asset.tag}")
    
    # Inisialisasi Logic Inspector dengan Limit dari Database Aset
    mech_inspector = MechanicalInspector(vib_limit_warn=asset.vib_limit_warning)

    # Tab Menu
    tab1, tab2, tab3 = st.tabs(["⚙️ MEKANIKAL (ISO 20816)", "⚡ ELEKTRIKAL (IEC)", "👁️ VISUAL (OSHA)"])

    # --- TAB 1: MEKANIKAL ---
    with tab1:
        st.info(f"Limit vibrasi otomatis diset ke **{asset.vib_limit_warning} mm/s** (ISO 20816 Group 2/3 Based on {asset.power_kw} kW).")
        
        with st.form("mech_form"):
            col1, col2 = st.columns(2)
            
            # --- INPUT DRIVER (MOTOR) ---
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

            # --- INPUT DRIVEN (POMPA) ---
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
            
            # Tambahan Noise
            st.markdown("---")
            noise_obs = st.selectbox("Noise Check (Pendengaran):", ["Normal / Halus", "Kavitasi / Kerikil", "Bearing Defect / Gemuruh", "High Pitch / Desing"])
            
            submit_mech = st.form_submit_button("🔍 ANALISA VIBRASI & SUHU")

        # --- HASIL ANALISA MEKANIKAL ---
        if submit_mech:
            # 1. Siapkan Data Input
            inputs_vib = {
                'm_de_h': m_de_h, 'm_de_v': m_de_v, 'm_de_a': m_de_a,
                'm_nde_h': m_nde_h, 'm_nde_v': m_nde_v, 'm_nde_a': m_nde_a,
                'p_de_h': p_de_h, 'p_de_v': p_de_v, 'p_de_a': p_de_a,
                'p_nde_h': p_nde_h, 'p_nde_v': p_nde_v, 'p_nde_a': p_nde_a
            }
            inputs_temp = {
                'Motor DE': t_m_de, 'Motor NDE': t_m_nde,
                'Pump DE': t_p_de, 'Pump NDE': t_p_nde
            }

            # 2. Panggil Logic Module (Otak Perhitungan)
            result = mech_inspector.analyze_full_health(inputs_vib, inputs_temp, noise_obs)
            
            df_report = result['dataframe']
            faults = result['faults']
            max_vib = result['max_vib']
            
            st.divider()
            
            # Layout Hasil
            res_c1, res_c2 = st.columns([2, 1])
            
            with res_c1:
                st.subheader("📋 Tabel Laporan Vibrasi")
                st.dataframe(
                    df_report.style.apply(highlight_row, axis=1)
                    .format({"DE": "{:.2f}", "NDE": "{:.2f}", "Avr": "{:.2f}", "Limit": "{:.2f}"}),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Tampilkan Diagnosa (Jika Ada)
                if faults:
                    st.error("🚨 **DIAGNOSA KERUSAKAN TERDETEKSI:**")
                    for f in faults:
                        with st.expander(f"⚠️ {f['desc']} (Klik Detail)", expanded=True):
                            st.markdown(f"**Penyebab:** {f['desc']}")
                            st.markdown(f"**Rekomendasi:** {f['action']}")
                            st.caption(f"Ref: {f['std']}")
                else:
                    st.success("✅ **Kondisi Mekanikal NORMAL.** Tidak ditemukan indikasi misalignment atau bearing defect.")

            with res_c2:
                st.subheader("Indikator")
                # Gauge
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = max_vib,
                    title = {'text': "Max Vib (mm/s)"},
                    gauge = {
                        'axis': {'range': [0, asset.vib_limit_alarm * 1.2]}, # Range dinamis ikut database
                        'bar': {'color': "black"},
                        'steps': [
                            {'range': [0, asset.vib_limit_warning], 'color': "#e8f5e9"}, # Aman
                            {'range': [asset.vib_limit_warning, asset.vib_limit_alarm], 'color': "#fffde7"}, # Warning
                            {'range': [asset.vib_limit_alarm, asset.vib_limit_alarm * 1.5], 'color': "#ffebee"} # Bahaya
                        ],
                        'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': asset.vib_limit_warning}
                    }
                ))
                fig.update_layout(height=200, margin=dict(t=30,b=20,l=20,r=20))
                st.plotly_chart(fig, use_container_width=True)

    # --- TAB 2: ELEKTRIKAL ---
    with tab2:
        st.subheader("Analisa Kualitas Daya (IEC 60034)")
        st.info("Form input elektrikal akan muncul disini...")
        # (Anda bisa copy-paste kode input elektrikal dari file lama ke sini)

    # --- TAB 3: VISUAL ---
    with tab3:
        st.subheader("Visual & Safety Check (OSHA/ISO)")
        st.info("Checklist visual akan muncul disini...")


# ==============================================================================
# MODE 2: COMMISSIONING
# ==============================================================================
elif mode == "🚀 COMMISSIONING":
    st.title(f"🚀 Commissioning Check: {asset.tag}")
    st.warning("Modul Commissioning sedang dalam tahap pengembangan.")
