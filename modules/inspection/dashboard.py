# modules/inspection/dashboard.py

import streamlit as st
from modules.inspection.mechanical import MechanicalInspector
from modules.inspection.electrical import ElectricalInspector
from modules.inspection.visual import VisualInspector

def run(asset): # <--- MENERIMA DATA ASET DARI DATABASE
    st.title(f"🛠️ Inspeksi Rutin: {asset.name}")
    st.caption(f"Tag: {asset.tag} | Power: {asset.power_kw} kW | ISO Limit: {asset.vib_limit_warning} mm/s")
    
    # Init Inspector dengan Limit dari Database Aset!
    mech = MechanicalInspector(vib_limit_warn=asset.vib_limit_warning) 
    elec = ElectricalInspector()
    vis = VisualInspector()

    tab1, tab2, tab3 = st.tabs(["⚙️ MEKANIKAL", "⚡ ELEKTRIKAL", "👁️ VISUAL"])

    with tab1:
        st.info(f"Limit vibrasi otomatis diset ke **{asset.vib_limit_warning} mm/s** berdasarkan ISO 20816 (Power {asset.power_kw} kW).")
        # ... (lanjutkan kode input vibrasi seperti sebelumnya) ...
    
    with tab2:
        st.info(f"Analisa Elektrikal untuk Motor **{asset.volt_rated}V / {asset.fla_rated}A**.")
        # ... (lanjutkan kode input elektrikal) ...
