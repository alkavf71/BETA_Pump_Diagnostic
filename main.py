import streamlit as st
from modules.inspection import mechanical

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Digital Reliability Assistant",
    page_icon="🔧",
    layout="wide"
)

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("🔧 Reliability Menu")
st.sidebar.markdown("---")

# Pilihan Menu
menu_options = [
    "🏠 Dashboard Home", 
    "🔍 Mechanical Inspection", 
    "📊 History & Trending", 
    "⚙️ Settings"
]

selected_menu = st.sidebar.radio("Pilih Modul:", menu_options)

# --- LOGIKA TAMPILAN HALAMAN ---
if selected_menu == "🏠 Dashboard Home":
    st.title("🏭 Digital Reliability Dashboard")
    st.info("Selamat datang di Sistem Diagnosa Pompa & Motor.")
    st.markdown("""
    **Fitur Utama:**
    * **Mechanical Inspection:** Input data vibrasi, spektrum, dan hidrolik.
    * **Auto-Diagnosis:** Deteksi Unbalance, Misalignment, Bearing, & Kavitasi.
    * **ISO 10816-3:** Evaluasi otomatis sesuai standar internasional.
    """)
    
elif selected_menu == "🔍 Mechanical Inspection":
    # INI BAGIAN PENTING: Memanggil fungsi dari modul mechanical.py
    mechanical.render_mechanical_page()

elif selected_menu == "📊 History & Trending":
    st.title("📊 Trending Data")
    st.warning("Fitur Trending akan segera hadir (Database Integration).")

elif selected_menu == "⚙️ Settings":
    st.title("⚙️ Pengaturan Aplikasi")
    st.write("Konfigurasi User & Parameter Default.")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 PT Pertamina Patra Niaga")
st.sidebar.caption("Infrastructure Management & Project")
