import streamlit as st
from modules.asset_database import get_asset_list, get_asset_details
# Import Modules UI
from modules.inspection import dashboard as inspection_dashboard
# from modules.commissioning import dashboard as commissioning_dashboard # (Nanti dibuat)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Reliability Pro Enterprise", layout="wide", page_icon="🏭")

# --- SIDEBAR: ASSET SELECTION ---
st.sidebar.title("🏭 Reliability Pro")
st.sidebar.subheader("Asset Selection")

# 1. Pilih Aset dari Database
selected_tag = st.sidebar.selectbox("Pilih Aset / Tag Number:", get_asset_list())
asset_data = get_asset_details(selected_tag)

# Tampilkan Info Aset di Sidebar (Biar user yakin)
with st.sidebar.expander("ℹ️ Spesifikasi Aset", expanded=True):
    st.write(f"**Nama:** {asset_data.name}")
    st.write(f"**Type:** {asset_data.pump_type}")
    st.write(f"**Power:** {asset_data.power_kw} kW")
    st.write(f"**RPM:** {asset_data.rpm}")
    st.markdown(f"**Vib Limit:** `{asset_data.vib_limit_warning} mm/s`")

st.sidebar.markdown("---")

# --- MAIN MODE SELECTION ---
app_mode = st.sidebar.radio("Pilih Mode Aplikasi:", ["🛠️ INSPEKSI RUTIN", "🚀 COMMISSIONING"])

if app_mode == "🛠️ INSPEKSI RUTIN":
    # Jalankan Dashboard Inspeksi dengan membawa data aset
    inspection_dashboard.run(asset_data)

elif app_mode == "🚀 COMMISSIONING":
    st.title(f"🚀 Commissioning Mode: {asset_data.name}")
    st.info("Modul Commissioning (API 676 / API 610 Check) akan dibangun selanjutnya.")
    # commissioning_dashboard.run(asset_data)
