import streamlit as st
from modules.inspection import mechanical

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Digital Reliability Assistant",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed" # Sidebar disembunyikan agar fokus
)

# --- CSS AGAR TAMPILAN LEBIH BERSIH ---
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 5rem;}
    h1 {color: #2c3e50;}
    div[data-testid="stMetricValue"] {font-size: 1.2rem;}
    </style>
    """, unsafe_allow_html=True)

# --- LOGIKA UTAMA ---
# Langsung memanggil modul mechanical tanpa if/else menu
try:
    # Header Aplikasi Kecil di Atas
    st.markdown("### 🏭 PT Pertamina Patra Niaga - Reliability App")
    
    # Render Halaman Diagnosa
    mechanical.render_mechanical_page()
    
    # Footer
    st.markdown("---")
    st.caption("© 2026 Infrastructure Management & Project | Digital Reliability Assistant v1.0")

except Exception as e:
    st.error(f"Terjadi kesalahan sistem: {e}")
    st.info("Pastikan file 'modules/inspection/mechanical.py' sudah di-save dengan benar.")
