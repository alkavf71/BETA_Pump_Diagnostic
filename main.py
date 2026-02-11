import streamlit as st
from modules.inspection import mechanical

# --- KONFIGURASI HALAMAN (WAJIB PALING ATAS) ---
st.set_page_config(
    page_title="Digital Reliability Assistant",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS CUSTOM UNTUK TAMPILAN PROFESIONAL ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    h1 {
        color: #2c3e50;
    }
    h2, h3 {
        color: #34495e;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR NAVIGASI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1541/1541416.png", width=50)
    st.title("Reliability App")
    st.caption("PT Pertamina Patra Niaga")
    st.caption("Infra. Mgmt & Project")
    st.markdown("---")
    
    # Menu Navigasi
    selected_menu = st.radio(
        "Navigasi Modul:", 
        ["🏠 Dashboard", "🔍 Mechanical Inspection", "📊 History & Trend", "⚙️ Settings"]
    )
    
    st.markdown("---")
    st.info("Status: **Online** 🟢")

# --- LOGIKA KONTEN HALAMAN ---

if selected_menu == "🏠 Dashboard":
    st.title("🏭 Dashboard Reliability")
    st.markdown("### Selamat Datang, Inspector!")
    st.write("Silakan pilih menu **Mechanical Inspection** di samping untuk memulai input data sesuai Form Pertamina.")
    
    # Menampilkan ringkasan cepat (Opsional)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Equipment", "14 Unit")
    col2.metric("Status Normal", "12 Unit")
    col3.metric("Status Warning", "2 Unit", delta="-2", delta_color="inverse")

elif selected_menu == "🔍 Mechanical Inspection":
    # --- INILAH KUNCI UTAMANYA ---
    # Kode ini memanggil fungsi render_mechanical_page() 
    # yang ada di dalam file modules/inspection/mechanical.py yang baru saja Anda edit.
    try:
        mechanical.render_mechanical_page()
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat modul: {e}")
        st.warning("Pastikan file 'modules/inspection/mechanical.py' sudah disimpan.")

elif selected_menu == "📊 History & Trend":
    st.title("📊 History Data")
    st.write("Fitur database historis sedang dalam pengembangan.")

elif selected_menu == "⚙️ Settings":
    st.title("⚙️ Pengaturan")
    st.write("Konfigurasi parameter user.")
