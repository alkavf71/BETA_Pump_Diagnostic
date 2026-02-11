import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- IMPORT MODULES ---
# Pastikan struktur folder Anda:
# modules/asset_database.py
# modules/inspection/mechanical.py
# modules/inspection/electrical.py
# modules/inspection/hydraulic.py
# modules/health_logic.py (atau sesuaikan lokasi fungsi assess_overall_health)

from modules.asset_database import get_asset_list, get_asset_details
from modules.inspection.mechanical import MechanicalInspector
from modules.inspection.electrical import ElectricalInspector
from modules.inspection.hydraulic import HydraulicInspector

# Jika file health_logic ada di folder modules langsung:
try:
    from modules.health_logic import assess_overall_health
except ImportError:
    # Fallback function jika file belum ada/path beda
    def assess_overall_health(vib_stat, elec_stat, temp, phys, diags):
        return {"status": "UNKNOWN", "color": "#ccc", "desc": "Logic belum terhubung", "action": "-", "reasons": [], "standards": []}

# --- PAGE CONFIG ---
st.set_page_config(page_title="Reliability Pro Enterprise", layout="wide", page_icon="🏭")

# --- CSS UTILS ---
def highlight_row(row):
    remark = row.get('Remark', '')
    if "ZONE D" in remark: 
        return ['background-color: #ffebee; color: #b71c1c']*len(row)
    elif "ZONE C" in remark: 
        return ['background-color: #fffde7; color: #f57f17']*len(row)
    elif "ZONE A" in remark: 
        return ['background-color: #e8f5e9; color: #1b5e20; font-weight: bold']*len(row)
    else: 
        return ['background-color: #ffffff; color: #212529']*len(row)

# --- SESSION STATE ---
if 'mech_result' not in st.session_state: st.session_state.mech_result = None
if 'elec_result' not in st.session_state: st.session_state.elec_result = None
if 'hydro_result' not in st.session_state: st.session_state.hydro_result = None
if 'health_result' not in st.session_state: st.session_state.health_result = None

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.title("🏭 Reliability Pro")
    st.caption("Standard: ISO 20816, IEC 60034, API 610")
    
    activity_type = st.radio("Jenis Aktivitas:", ["🛠️ INSPEKSI RUTIN", "🚀 COMMISSIONING"])
    is_comm = "COMMISSIONING" in activity_type.upper()
    
    st.divider()
    selected_tag = st.selectbox("Pilih Aset (Tag No):", get_asset_list())
    asset = get_asset_details(selected_tag)
    
    with st.expander("ℹ️ Spesifikasi Aset", expanded=True):
        st.markdown(f"**Nama:** {asset.name}")
        st.markdown(f"**Type:** {asset.pump_type}")
        st.markdown(f"**Power:** {asset.power_kw} kW")
        st.markdown(f"**RPM:** {asset.rpm}")
        st.markdown(f"**Elec:** {asset.volt_rated}V / {asset.fla_rated}A")
        st.markdown("---")
        st.markdown(f"**Limit (Warn):** `{asset.vib_limit_warning} mm/s`")

# ==============================================================================
# MAIN CONTENT
# ==============================================================================
st.title(f"Diagnosa Aset: {asset.tag}")

if activity_type == "🛠️ INSPEKSI RUTIN":
    
    # Init Inspectors
    mech_inspector = MechanicalInspector(vib_limit_warn=asset.vib_limit_warning)
    elec_inspector = ElectricalInspector()
    hydro_inspector = HydraulicInspector()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ MEKANIKAL", "⚡ ELEKTRIKAL", "🌊 HIDROLIK", "🏥 KESIMPULAN"])

    # --------------------------------------------------------------------------
    # TAB 1: MEKANIKAL
    # --------------------------------------------------------------------------
    with tab1:
        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            st.info(f"Limit ISO 20816: **{asset.vib_limit_warning} mm/s** (Berdasarkan Power {asset.power_kw} kW).")
            
            # Gambar Peta (Optional)
            with st.expander("ℹ️ Lihat Peta Titik Pengukuran", expanded=False):
                try:
                    st.image("titik_ukur.png", use_container_width=True)
                except:
                    st.caption("Gambar titik_ukur.png tidak ditemukan.")

            with st.form("mech_form"):
                st.subheader("1. Data Vibrasi (mm/s)")
                c1a, c1b = st.columns(2)
                with c1a:
                    st.markdown("**DRIVER (Motor)**")
                    m_de_h = st.number_input("M-DE H", value=0.8, step=0.01, min_value=0.0)
                    m_de_v = st.number_input("M-DE V", value=0.2, step=0.01, min_value=0.0)
                    m_de_a = st.number_input("M-DE A", value=0.5, step=0.01, min_value=0.0)
                    t_m_de = st.number_input("Temp M-DE (°C)", value=45.0, step=1.0, min_value=0.0)
                with c1b:
                    st.markdown("**DRIVER (Motor NDE)**")
                    m_nde_h = st.number_input("M-NDE H", value=0.9, step=0.01, min_value=0.0)
                    m_nde_v = st.number_input("M-NDE V", value=0.3, step=0.01, min_value=0.0)
                    m_nde_a = st.number_input("M-NDE A", value=0.4, step=0.01, min_value=0.0)
                    t_m_nde = st.number_input("Temp M-NDE (°C)", value=42.0, step=1.0, min_value=0.0)

                st.markdown("---")
                c2a, c2b = st.columns(2)
                with c2a:
                    st.markdown("**DRIVEN (Pompa)**")
                    p_de_h = st.number_input("P-DE H", value=1.2, step=0.01, min_value=0.0)
                    p_de_v = st.number_input("P-DE V", value=0.8, step=0.01, min_value=0.0)
                    p_de_a = st.number_input("P-DE A", value=0.6, step=0.01, min_value=0.0)
                    t_p_de = st.number_input("Temp P-DE (°C)", value=40.0, step=1.0, min_value=0.0)
                with c2b:
                    st.markdown("**DRIVEN (Pompa NDE)**")
                    p_nde_h = st.number_input("P-NDE H", value=0.7, step=0.01, min_value=0.0)
                    p_nde_v = st.number_input("P-NDE Vert", value=0.4, step=0.01, min_value=0.0)
                    p_nde_a = st.number_input("P-NDE Axial", value=0.3, step=0.01, min_value=0.0)
                    t_p_nde = st.number_input("Temp P-NDE (°C)", value=38.0, step=1.0, min_value=0.0)

                st.markdown("---")
                st.subheader("2. Inspeksi Fisik & Noise")
                
                cn1, cn2 = st.columns(2)
                with cn1:
                    noise_type = st.selectbox("Karakter Suara:", ["Normal / Halus", "Kavitasi / Kerikil", "Bearing Defect / Gemuruh", "Mencicit / Squealing"])
                    noise_loc = st.selectbox("Lokasi Suara:", ["-", "Motor DE", "Motor NDE", "Pump DE", "Pump NDE", "Casing"])
                with cn2:
                    dba_val = st.number_input("Level Suara (dBA):", value=80.0, step=0.1)
                    valve_test = st.radio("Valve Test:", ["Tidak Dilakukan", "Suara Stabil", "Berubah Drastis"], horizontal=True)

                st.caption("Checklist Fisik:")
                chk_seal = st.checkbox("MAJOR: Seal Bocor / Rembes")
                chk_guard = st.checkbox("MAJOR: Guard Hilang")
                chk_baut = st.checkbox("MINOR: Baut Kendor")
                
                submit_mech = st.form_submit_button("🔍 ANALISA MEKANIKAL")

        if submit_mech:
            # Prepare Inputs
            inputs_vib = {
                'm_de_h': m_de_h, 'm_de_v': m_de_v, 'm_de_a': m_de_a,
                'm_nde_h': m_nde_h, 'm_nde_v': m_nde_v, 'm_nde_a': m_nde_a,
                'p_de_h': p_de_h, 'p_de_v': p_de_v, 'p_de_a': p_de_a,
                'p_nde_h': p_nde_h, 'p_nde_v': p_nde_v, 'p_nde_a': p_nde_a
            }
            inputs_temp = {'Motor DE': t_m_de, 'Motor NDE': t_m_nde, 'Pump DE': t_p_de, 'Pump NDE': t_p_nde}

            # Call Logic
            df_report, faults, max_vib = mech_inspector.analyze_vibration(inputs_vib)
            
            # Logic Tambahan (Suhu & Noise yang terintegrasi di MechanicalInspector atau manual disini)
            # Agar konsisten dengan file mechanical.py terakhir, kita gunakan fungsi analyze_full_health jika ada
            # Jika tidak, kita gunakan logic manual disini:
            
            full_res = mech_inspector.analyze_full_health(inputs_vib, inputs_temp, noise_type)
            
            # Tambahkan Logic Fisik ke list Faults agar masuk laporan
            phys_list = []
            if chk_seal: phys_list.append("MAJOR: Seal Bocor")
            if chk_guard: phys_list.append("MAJOR: Guard Hilang")
            if chk_baut: phys_list.append("MINOR: Baut Kendor")

            st.session_state.mech_result = {
                "df": full_res['dataframe'],
                "max_vib": full_res['max_vib'],
                "faults": full_res['faults'],
                "status": full_res['status'],
                "temps": inputs_temp,
                "phys": phys_list,
                "noise": f"{noise_type} ({dba_val} dBA)"
            }

        # OUTPUT MEKANIKAL
        with col2:
            if st.session_state.mech_result:
                res = st.session_state.mech_result
                
                st.subheader("📋 Laporan Vibrasi")
                st.dataframe(res['df'].style.apply(highlight_row, axis=1).format({"DE": "{:.2f}", "NDE": "{:.2f}", "Avr": "{:.2f}", "Limit": "{:.2f}"}), use_container_width=True, hide_index=True)
                
                c_g1, c_g2 = st.columns([1, 2])
                with c_g1:
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number", value=res['max_vib'], title={'text': "Max Avr"},
                        gauge={'axis': {'range': [0, 10]}, 'bar': {'color': "black"}, 'steps': [{'range': [0, asset.vib_limit_warning], 'color': '#e8f5e9'}, {'range': [asset.vib_limit_warning, 7.1], 'color': '#fffde7'}, {'range': [7.1, 10], 'color': '#ffebee'}]}
                    ))
                    fig.update_layout(height=180, margin=dict(t=30,b=20,l=20,r=20))
                    st.plotly_chart(fig, use_container_width=True)
                
                with c_g2:
                    st.info(f"**STATUS: {res['status']}**")
                    if res['faults']:
                        for f in res['faults']:
                            with st.expander(f"⚠️ {f['name']}", expanded=True):
                                st.write(f"**Analisa:** {f['desc']}")
                                st.write(f"**Action:** {f['action']}")
                    if res['phys']:
                         st.warning("⚠️ **FISIK:** " + ", ".join(res['phys']))

    # --------------------------------------------------------------------------
    # TAB 2: ELEKTRIKAL
    # --------------------------------------------------------------------------
    with tab2:
        with st.form("elec_form"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Voltase ({asset.volt_rated}V)**")
                v_rs = st.number_input("R-S", value=float(asset.volt_rated), step=1.0)
                v_st = st.number_input("S-T", value=float(asset.volt_rated), step=1.0)
                v_tr = st.number_input("T-R", value=float(asset.volt_rated), step=1.0)
                t_body = st.number_input("Temp Body Motor (°C)", value=55.0, step=1.0)
            with c2:
                st.markdown(f"**Ampere ({asset.fla_rated}A)**")
                i_r = st.number_input("Phase R", value=float(asset.fla_rated)*0.8, step=0.1)
                i_s = st.number_input("Phase S", value=float(asset.fla_rated)*0.8, step=0.1)
                i_t = st.number_input("Phase T", value=float(asset.fla_rated)*0.8, step=0.1)
            
            submit_elec = st.form_submit_button("⚡ ANALISA ELEKTRIKAL")

        if submit_elec:
            vol_inputs = [v_rs, v_st, v_tr]
            amp_inputs = [i_r, i_s, i_t]
            
            df_elec, elec_faults, elec_status, load_pct = elec_inspector.analyze_health(
                vol_inputs, amp_inputs, asset.volt_rated, asset.fla_rated
            )
            
            # Logic Tambahan Suhu Body
            if t_body > 90.0:
                elec_faults.append({"name": "OVERHEAT BODY", "val": f"{t_body}C", "desc": "Suhu body tinggi.", "action": "Cek Pendinginan."})
            
            st.session_state.elec_result = {"df": df_elec, "faults": elec_faults, "status": elec_status, "load": load_pct}

        if st.session_state.elec_result:
            res = st.session_state.elec_result
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.dataframe(res['df'], use_container_width=True, hide_index=True)
            with col_m2:
                fig_load = go.Figure(go.Indicator(mode="gauge+number", value=res['load'], title={'text':"Load %"}, gauge={'axis':{'range':[0,120]}, 'bar':{'color':'black'}, 'steps':[{'range':[0,100], 'color':'#e8f5e9'}, {'range':[100,120], 'color':'#ffebee'}]}))
                fig_load.update_layout(height=200, margin=dict(t=30,b=20,l=20,r=20))
                st.plotly_chart(fig_load, use_container_width=True)
            
            if res['faults']:
                for f in res['faults']: st.error(f"🚨 **{f['name']}:** {f['desc']} -> {f['action']}")

    # --------------------------------------------------------------------------
    # TAB 3: HIDROLIK
    # --------------------------------------------------------------------------
    with tab3:
        with st.form("hydro_form"):
            c1, c2, c3 = st.columns(3)
            p_in = c1.number_input("Suction (Bar)", value=0.5, step=0.1)
            p_out = c2.number_input("Discharge (Bar)", value=4.5, step=0.1)
            sg = c3.number_input("SG Fluid", value=0.85, step=0.01)
            head_des = st.number_input("Design Head (m)", value=50.0, step=1.0)
            submit_hydro = st.form_submit_button("🌊 ANALISA HIDROLIK")
        
        if submit_hydro:
            res_hydro = hydro_inspector.analyze_performance(p_in, p_out, sg, head_des)
            st.session_state.hydro_result = res_hydro

        if st.session_state.hydro_result:
            res = st.session_state.hydro_result
            c1, c2 = st.columns(2)
            c1.metric("Actual Head", f"{res['actual_head']:.1f} m", f"{res['deviation']:.1f}%")
            if "NORMAL" in res['status']:
                c2.success(f"**{res['status']}**")
            else:
                c2.error(f"**{res['status']}**\n\n{res['desc']}")

    # --------------------------------------------------------------------------
    # TAB 4: KESIMPULAN
    # --------------------------------------------------------------------------
    with tab4:
        if st.button("GENERATE FINAL REPORT"):
            if st.session_state.mech_result:
                mech = st.session_state.mech_result
                elec = st.session_state.elec_result
                
                # Mapping data ke format Health Logic
                vib_status = "ZONE D" if "D:" in mech['status'] else "ZONE C" if "C:" in mech['status'] else "ZONE A"
                elec_status = "TRIP" if (elec and elec['faults']) else "NORMAL"
                
                # Gabung semua diagnosa teknis
                all_diags = [f['name'] for f in mech['faults']]
                if elec and elec['faults']: all_diags += [f['name'] for f in elec['faults']]
                
                health = assess_overall_health(
                    vib_status, 
                    elec_status, 
                    max(mech['temps'].values()), 
                    mech['phys'], 
                    all_diags
                )
                st.session_state.health_result = health
            else:
                st.warning("Jalankan Mekanikal Dulu.")

        if st.session_state.health_result:
            hr = st.session_state.health_result
            st.markdown(f"""<div style="background:{'#d4edda' if 'GOOD' in hr['status'] else '#f8d7da'};padding:20px;border-radius:10px;text-align:center;border:2px solid {hr['color']};"><h1 style='color:{hr['color']}'>{hr['status']}</h1><h3>{hr['desc']}</h3><hr>{hr['action']}</div>""", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.error("### ROOT CAUSE")
                for r in hr['reasons']: st.write(f"❌ {r}")
            with c2:
                st.warning("### REKOMENDASI")
                for rec in hr['recommendations']: st.write(f"🔧 {rec}")
            
            st.caption("Standards: " + ", ".join(hr['standards']))

# ==============================================================================
# MODE 2: COMMISSIONING
# ==============================================================================
elif mode == "🚀 COMMISSIONING":
    st.title("🚀 Commissioning Mode")
    st.info("Modul Commissioning (API 686 / 676 Check) akan diimplementasikan selanjutnya.")
