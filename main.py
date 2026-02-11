import streamlit as st
from PIL import Image

# Import module mechanical yang sudah dibuat
# Pastikan ada file __init__.py kosong di dalam folder modules/ dan modules/inspection/
try:
    from modules.inspection import mechanical
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Reliability Assistant",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1546/1546130.png", width=80) # Placeholder Logo
    st.title("Pump Diagnostic")
    st.caption("v1.0.0 - OJT Project")
    
    st.markdown("---")
    
    # Menu Navigasi
    menu = st.radio(
        "Main Menu",
        ["Dashboard", "🔍 Mechanical Inspection", "⚡ Electrical Inspection", "📝 Report History"]
    )
    
    st.markdown("---")
    st.info("User: Inspector 01\nSite: IT Makassar")

# --- 3. MAIN CONTENT ROUTING ---

if menu == "Dashboard":
    # Halaman Depan (Landing Page)
    st.title("📊 Reliability Dashboard")
    st.markdown("Selamat datang di **Digital Reliability Assistant**.")
    
    # Kpi Summary (Placeholder)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Equipment", "12 Unit")
    c2.metric("Healthy", "8 Unit")
    c3.metric("Warning (Alert)", "3 Unit", delta="-1")
    c4.metric("Danger (Trip)", "1 Unit", delta="-1", delta_color="inverse")
    
    st.markdown("### Quick Actions")
    col_a, col_b = st.columns(2)
    with col_a:
        st.info("Untuk memulai inspeksi Vibrasi & Pressure, silakan pilih menu **Mechanical Inspection** di sebelah kiri.")
    with col_b:
        st.warning("Pastikan Anda membawa alat APD dan **ADASH 4900** sebelum ke lapangan.")

elif menu == "🔍 Mechanical Inspection":
    # Memanggil fungsi render dari file mechanical.py
    mechanical.render_mechanical_page()

elif menu == "⚡ Electrical Inspection":
    st.title("⚡ Electrical Diagnostics")
    st.warning("Modul ini sedang dalam pengembangan (Coming Soon).")
    st.write("Fitur yang akan datang: Motor Current Signature Analysis (MCSA), Voltage Unbalance, dll.")

elif menu == "📝 Report History":
    st.title("📝 Inspection History")
    st.write("Belum ada data history tersimpan.")
    # Nanti di sini kita bisa load database hasil simpanan

# --- 4. FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey; font-size: 0.8em;'>"
    "Developed for OJT Project PT Pertamina Patra Niaga | 2026"
    "</div>", 
    unsafe_allow_html=True
)
