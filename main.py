
import streamlit as st
from modules.inspection import dashboard as inspection_dashboard
# from modules.commissioning import dashboard as comm_dashboard # (Nanti diaktifkan)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Reliability Pro Enterprise", layout="wide", page_icon="🏭")

# --- SIDEBAR MENU UTAMA ---
st.sidebar.title("🏭 Reliability Pro")
st.sidebar.caption("Enterprise Asset Management")

mode = st.sidebar.radio("Pilih Mode Kerja:", ["🛠️ INSPEKSI RUTIN", "🚀 COMMISSIONING"])

st.sidebar.markdown("---")

# --- ROUTING LOGIC ---
if mode == "🛠️ INSPEKSI RUTIN":
    # Jalankan Module Inspeksi
    inspection_dashboard.run()

elif mode == "🚀 COMMISSIONING":
    st.title("🚀 Mode Commissioning")
    st.info("Modul Commissioning sedang dalam pengembangan (Next Step).")
    # comm_dashboard.run() # (Nanti diaktifkan)
