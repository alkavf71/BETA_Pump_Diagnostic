import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- IMPORT MODULES ---
from modules.asset_database import get_asset_list, get_asset_details
from modules.inspection.mechanical import MechanicalInspector
from modules.inspection.electrical import ElectricalInspector
from modules.inspection.hydraulic import HydraulicInspector
from modules.health_logic import assess_overall_health

# --- PAGE CONFIG ---
st.set_page_config(page_title="Reliability Pro Enterprise", layout="wide", page_icon="🏭")

# --- CSS UTILS ---
def highlight_row(row):
    remark = row.get('Remark', '')
    if "ZONE D" in remark: 
        return ['background-color: #ffebee; color: #b71c1c']*len(row) # Light Red
    elif "ZONE C" in remark: 
        return ['background-color: #fffde7; color: #f57f17']*len(row) # Light Yellow
    elif "ZONE A" in remark: 
        return ['background-color: #e8f5e9; color: #1b5e20; font-weight: bold']*len(row) # Light Green
    else: 
        return ['background-color: #ffffff; color: #212529']*len(row)

# --- SESSION STATE INIT ---
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
    is_comm = "COMMISSIONING" in activity_type
    
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
    # TAB 1: MEKANIKAL (UI Diperbaiki)
    # --------------------------------------------------------------------------
    with tab1:
        col1, col2 = st.columns([1.2, 1]) # Column untuk Input & Output
        
        with col1: # Bagian Input
            st.info(f"Limit ISO 20816: **{asset.vib_limit_warning} mm/s** (Berdasarkan Power {asset.power_kw} kW).")
            
            # Expander untuk Gambar Peta Titik Pengukuran
            with st.expander("🗺️ Lihat Peta Titik Pengukuran", expanded=False):
                try:
                    # Pastikan file titik_ukur.png ada di root folder aplikasi
                    st.image("titik_ukur.png", caption="Titik Pengukuran Vibrasi Motor-Pompa", use_container_width=True)
                except FileNotFoundError:
                    st.warning("⚠️ File 'titik_ukur.png' tidak ditemukan. Harap letakkan di root folder aplikasi.")
                except Exception as e:
                    st.error(f"Error memuat gambar: {e}")

            with st.form("mech_form"):
                st.subheader("1. Data Vibrasi (mm/s RMS)")
                c1a, c1b = st.columns(2)
                with c1a:
                    st.markdown("#### DRIVER (Motor DE)")
                    m_de_h = st.number_input("M-DE H", value=0.8, step=0.01, min_value=0.0, format="%.2f")
                    m_de_v = st.number_input("M-DE V", value=0.2, step=0.01, min_value=0.0, format="%.2f")
                    m_de_a = st.number_input("M-DE A", value=0.5, step=0.01, min_value=0.0, format="%.2f")
                    t_m_de = st.number_input("Temp M-DE (°C)", value=45.0, step=1.0, min_value=0.0, format="%.1f")
                with c1b:
                    st.markdown("#### DRIVER (Motor NDE)")
                    m_nde_h = st.number_input("M-NDE H", value=0.9, step=0.01, min_value=0.0, format="%.2f")
                    m_nde_v = st.number_input("M-NDE V", value=0.3, step=0.01, min_value=0.0, format="%.2f")
                    m_nde_a = st.number_input("M-NDE A", value=0.4, step=0.01, min_value=0.0, format="%.2f")
                    t_m_nde = st.number_input("Temp M-NDE (°C)", value=42.0, step=1.0, min_value=0.0, format="%.1f")

                st.markdown("---")
                c2a, c2b = st.columns(2)
                with c2a:
                    st.markdown("#### DRIVEN (Pompa DE)")
                    p_de_h = st.number_input("P-DE H", value=1.2, step=0.01, min_value=0.0, format="%.2f")
                    p_de_v = st.number_input("P-DE V", value=0.8, step=0.01, min_value=0.0, format="%.2f")
                    p_de_a = st.number_input("P-DE A", value=0.6, step=0.01, min_value=0.0, format="%.2f")
                    t_p_de = st.number_input("Temp P-DE (°C)", value=40.0, step=1.0, min_value=0.0, format="%.1f")
                with c2b:
                    st.markdown("#### DRIVEN (Pompa NDE)")
                    p_nde_h = st.number_input("P-NDE H", value=0.7, step=0.01, min_value=0.0, format="%.2f")
                    p_nde_v = st.number_input("P-NDE Vert", value=0.4, step=0.01, min_value=0.0, format="%.2f")
                    p_nde_a = st.number_input("P-NDE Axial", value=0.3, step=0.01, min_value=0.0, format="%.2f")
                    t_p_nde = st.number_input("Temp P-NDE (°C)", value=38.0, step=1.0, min_value=0.0, format="%.1f")

                st.markdown("---")
                st.subheader("2. Inspeksi Fisik & Noise")
                
                cn1, cn2 = st.columns(2)
                with cn1:
                    noise_type = st.selectbox("Karakter Suara:", ["Normal / Halus", "Kavitasi / Kerikil", "Bearing Defect / Gemuruh", "Mencicit / Squealing", "Benturan / Clanking"])
                    noise_loc = st.selectbox("Lokasi Suara:", ["-", "Motor DE", "Motor NDE", "Pompa DE", "Pompa NDE", "Casing Pompa", "Kopling"])
                with cn2:
                    dba_val = st.number_input("Level Suara (dBA):", value=80.0, step=0.1, min_value=0.0, format="%.1f")
                    valve_test = st.radio("Valve Test (perubahan suara saat valve ditutup):", ["Tidak Dilakukan", "Suara Stabil", "Berubah Drastis (Indikasi Kavitasi/Sirkulasi)"], horizontal=False)

                st.caption("Checklist Fisik Visual:")
                chk_seal = st.checkbox("MAJOR: Seal Bocor / Rembes Parah")
                chk_guard = st.checkbox("MAJOR: Guard Kopling Hilang / Rusak")
                chk_baut = st.checkbox("MINOR: Baut Pondasi / Kopling Kendor")
                chk_vibr = st.checkbox("FISIK: Getaran berlebih terasa di tangan")
                
                submit_mech = st.form_submit_button("🔍 ANALISA MEKANIKAL")

        if submit_mech:
            inputs_vib = {
                'm_de_h': m_de_h, 'm_de_v': m_de_v, 'm_de_a': m_de_a,
                'm_nde_h': m_nde_h, 'm_nde_v': m_nde_v, 'm_nde_a': m_nde_a,
                'p_de_h': p_de_h, 'p_de_v': p_de_v, 'p_de_a': p_de_a,
                'p_nde_h': p_nde_h, 'p_nde_v': p_nde_v, 'p_nde_a': p_nde_a
            }
            inputs_temp = {'Motor DE': t_m_de, 'Motor NDE': t_m_nde, 'Pompa DE': t_p_de, 'Pompa NDE': t_p_nde}

            result = mech_inspector.analyze_full_health(inputs_vib, inputs_temp, noise_type)
            
            phys_list = []
            if chk_seal: phys_list.append("MAJOR: Seal Bocor")
            if chk_guard: phys_list.append("MAJOR: Guard Hilang")
            if chk_baut: phys_list.append("MINOR: Baut Kendor")
            if chk_vibr: phys_list.append("FISIK: Getaran Berlebih")

            st.session_state.mech_result = {
                "df": result['dataframe'],
                "max_vib": result['max_vib'],
                "faults": result['faults'],
                "status": result['status'],
                "temps": inputs_temp,
                "phys": phys_list,
                "noise_char": noise_type,
                "noise_loc": noise_loc,
                "dba": dba_val
            }

        # Bagian Output Mekanikal
        with col2:
            if st.session_state.mech_result:
                res = st.session_state.mech_result
                
                st.subheader("📊 Laporan Diagnosa Vibrasi")
                st.dataframe(res['df'].style.apply(highlight_row, axis=1).format({"DE": "{:.2f}", "NDE": "{:.2f}", "Avr": "{:.2f}", "Limit": "{:.2f}"}), use_container_width=True, hide_index=True)
                
                # Gauge Maksimum Vibrasi
                c_g1, c_g2 = st.columns([1, 2])
                with c_g1:
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number", value=res['max_vib'], title={'text': "Max Avg Vib"},
                        gauge={'axis': {'range': [0, 10]}, 'bar': {'color': "black"}, 
                               'steps': [{'range': [0, asset.vib_limit_warning], 'color': '#e8f5e9'}, # Green
                                         {'range': [asset.vib_limit_warning, 7.1], 'color': '#fffde7'}, # Yellow (ISO Zone C)
                                         {'range': [7.1, 10], 'color': '#ffebee'}]} # Red (ISO Zone D)
                    ))
                    fig.update_layout(height=180, margin=dict(t=30,b=20,l=20,r=20))
                    st.plotly_chart(fig, use_container_width=True)
                
                # Status dan Faults
                with c_g2:
                    if "CRITICAL" in res['status'] or "DANGEROUS" in res['status']:
                        st.error(f"🚨 **STATUS: {res['status']}**")
                    elif "WARNING" in res['status']:
                        st.warning(f"⚠️ **STATUS: {res['status']}**")
                    else:
                        st.success(f"✅ **STATUS: {res['status']}**")

                    if res['faults']:
                        for f in res['faults']:
                            with st.expander(f"⚙️ {f['name']} ({f['val']})", expanded=True):
                                st.write(f"**Analisa:** {f['desc']}")
                                st.write(f"**Tindakan:** {f['action']}")
                    if res['phys']:
                         st.info("ℹ️ **TEMUAN FISIK:** " + ", ".join(res['phys']))
                    if res['noise_char'] != "Normal / Halus":
                        st.info(f"👂 **SUARA ANOMALI:** {res['noise_char']} di {res['noise_loc']} ({res['dba']} dBA)")

    # --------------------------------------------------------------------------
    # TAB 2: ELEKTRIKAL
    # --------------------------------------------------------------------------
    with tab2:
        with st.form("elec_form"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Voltase Supply ({asset.volt_rated}V)**")
                v_rs = st.number_input("R-S (V)", value=float(asset.volt_rated), step=1.0, format="%.1f")
                v_st = st.number_input("S-T (V)", value=float(asset.volt_rated), step=1.0, format="%.1f")
                v_tr = st.number_input("T-R (V)", value=float(asset.volt_rated), step=1.0, format="%.1f")
                t_body = st.number_input("Temp Body Motor (°C)", value=55.0, step=1.0, min_value=0.0, format="%.1f")
            with c2:
                st.markdown(f"**Arus Beban ({asset.fla_rated}A)**")
                i_r = st.number_input("R (A)", value=float(asset.fla_rated)*0.8, step=0.1, format="%.1f")
                i_s = st.number_input("S (A)", value=float(asset.fla_rated)*0.8, step=0.1, format="%.1f")
                i_t = st.number_input("T (A)", value=float(asset.fla_rated)*0.8, step=0.1, format="%.1f")
                i_g = st.number_input("Ground Fault (A)", value=0.0, step=0.1, min_value=0.0, format="%.1f")
            
            submit_elec = st.form_submit_button("⚡ ANALISA ELEKTRIKAL")

        if submit_elec:
            vol_inputs = [v_rs, v_st, v_tr]
            amp_inputs = [i_r, i_s, i_t]
            
            df_elec, elec_faults, elec_status, load_pct = elec_inspector.analyze_health(
                vol_inputs, amp_inputs, asset.volt_rated, asset.fla_rated
            )
            
            # Logic Tambahan Suhu Body
            if t_body > 90.0:
                elec_faults.append({"name": "OVERHEAT BODY", "val": f"{t_body}C", "desc": "Suhu body motor tinggi. Cek pendinginan/fan.", "action": "Bersihkan sirip pendingin / cek kipas."})
                if elec_status != "CRITICAL": elec_status = "WARNING"
            elif t_body > 75.0:
                if not any("OVERHEAT BODY" in f['name'] for f in elec_faults): # Jangan duplikat jika sudah ada warning
                    elec_faults.append({"name": "HIGH BODY TEMP", "val": f"{t_body}C", "desc": "Suhu body motor sedikit tinggi.", "action": "Monitoring berkala."})

            # Ground Fault
            if i_g > elec_inspector.limit_ground_fault:
                 elec_faults.append({"name": "GROUND FAULT DETECTED", "val": f"{i_g} A", "desc": "Terdeteksi arus bocor ke tanah (>0.5A).", "action": "🔴 STOP EMERGENCY. Lakukan Megger Test Fasa-ke-Ground."})
                 elec_status = "CRITICAL"
            
            st.session_state.elec_result = {"df": df_elec, "faults": elec_faults, "status": elec_status, "load": load_pct, "body_temp": t_body}

        if st.session_state.elec_result:
            res = st.session_state.elec_result
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.dataframe(res['df'], use_container_width=True, hide_index=True)
            with col_m2:
                fig_load = go.Figure(go.Indicator(mode="gauge+number", value=res['load'], title={'text':"Load %"}, 
                                                  gauge={'axis':{'range':[0,120]}, 'bar':{'color':'black'}, 
                                                         'steps':[{'range':[0,100], 'color':'#e8f5e9'}, 
                                                                  {'range':[100,120], 'color':'#ffebee'}]})) # Overload > 100%
                fig_load.update_layout(height=200, margin=dict(t=30,b=20,l=20,r=20))
                st.plotly_chart(fig_load, use_container_width=True)
            
            if res['faults']:
                for f in res['faults']: 
                    if "CRITICAL" in f['name'].upper() or "EMERGENCY" in f['action'].upper():
                        st.error(f"🚨 **{f['name']}:** {f['desc']} -> {f['action']}")
                    else:
                        st.warning(f"⚠️ **{f['name']}:** {f['desc']} -> {f['action']}")

    # --------------------------------------------------------------------------
    # TAB 3: HIDROLIK
    # --------------------------------------------------------------------------
    with tab3:
        with st.form("hydro_form"):
            c1, c2, c3 = st.columns(3)
            p_in = c1.number_input("Suction (Bar)", value=0.5, step=0.1, format="%.1f", min_value=-1.0)
            p_out = c2.number_input("Discharge (Bar)", value=4.5, step=0.1, format="%.1f", min_value=0.0)
            sg = c3.number_input("SG Fluid", value=0.85, step=0.01, format="%.2f", min_value=0.01)
            head_des = st.number_input("Design Head (m)", value=50.0, step=1.0, format="%.1f", min_value=1.0)
            submit_hydro = st.form_submit_button("🌊 ANALISA HIDROLIK")
        
        if submit_hydro:
            res_hydro = hydro_inspector.analyze_performance(p_in, p_out, sg, head_des)
            st.session_state.hydro_result = res_hydro

        if st.session_state.hydro_result:
            res = st.session_state.hydro_result
            c1, c2 = st.columns(2)
            c1.metric("Actual Head", f"{res['actual_head']:.1f} m", f"{res['deviation']:.1f}%")
            if "NORMAL" in res['status'] or "EXCELLENT" in res['status']:
                c2.success(f"**{res['status']}**")
            else:
                st.warning(f"**{res['status']}**")
                st.error(f"**Analisa:** {res['desc']}")
                st.write(f"**Tindakan:** {res['action']}")

    # --------------------------------------------------------------------------
    # TAB 4: KESIMPULAN (Final Report)
    # --------------------------------------------------------------------------
    with tab4:
        if st.button("GENERATE FINAL REPORT", type="primary"):
            if st.session_state.mech_result and st.session_state.elec_result:
                mech = st.session_state.mech_result
                elec = st.session_state.elec_result
                hydro = st.session_state.hydro_result
                
                # Mapping Status ke format health_logic
                vib_status = "ZONE D" if "DANGEROUS" in mech['status'] else "ZONE C" if "WARNING" in mech['status'] else "ZONE A"
                elec_status = elec['status'] # Ambil status langsung dari ElectricalInspector
                
                # Kumpulkan semua diagnosa teknis dari semua modul
                all_diags = [f['name'] for f in mech['faults']] # Mekanikal
                all_diags += [f['name'] for f in elec['faults']] # Elektrikal
                if hydro and "NORMAL" not in hydro['status'] and "EXCELLENT" not in hydro['status']:
                    all_diags.append(f"HYDRAULIC: {hydro['status']}") # Hidrolik
                
                # Persiapkan data konteks untuk Cross-Analysis di health_logic
                context_data = {
                    "load_pct": elec['load'],
                    "actual_head": hydro['actual_head'] if hydro else None,
                    "design_head": hydro_inspector.design_head if hydro else None # Tambahkan design head
                }

                health = assess_overall_health(
                    vib_status, 
                    elec_status, 
                    max(mech['temps'].values()), 
                    mech['phys'], 
                    all_diags,
                    extra_context=context_data 
                )
                st.session_state.health_result = health
            else:
                st.warning("⚠️ Harap jalankan analisa MEKANIKAL dan ELEKTRIKAL terlebih dahulu.")

        if st.session_state.health_result:
            hr = st.session_state.health_result
            # Menampilkan status keseluruhan dengan gaya yang lebih menarik
            st.markdown(f"""
            <div style="background:{'#d4edda' if 'GOOD' in hr['status'] else '#f8d7da' if 'CRITICAL' in hr['status'] else '#fff3cd'};
                        padding:25px;border-radius:12px;text-align:center;
                        border:2px solid {hr['color']}; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);">
                <h1 style='color:{hr['color']}; margin-bottom:10px;'>{hr['status']}</h1>
                <p style='font-size:1.2em; color:#333; margin-bottom:15px;'>{hr['desc']}</p>
                <hr style='border-top:1px solid #bbb;'>
                <h4 style='color:{hr['color']}; margin-top:15px;'>Tindakan Rekomendasi:</h4>
                <p style='font-size:1.1em; color:#555;'>{hr['action']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.error("### 🚫 Root Cause Analisis:")
                reasons = hr.get('reasons', [])
                if reasons:
                    for r in reasons: st.write(f"❌ {r}")
                else:
                    st.success("Tidak ada isu kritikal yang teridentifikasi.")
            
            with c2:
                st.warning("### 🔧 Rekomendasi Tindakan:")
                recommendations = hr.get('recommendations', [])
                if recommendations:
                    for rec in recommendations: st.write(f"🛠️ {rec}")
                else:
                    st.info("Lanjutkan monitoring rutin sesuai jadwal.")
            
            st.caption(f"Standards Referensi: " + ", ".join(hr.get('standards', ['ISO 10816', 'IEC 60034', 'API 610'])))

# ==============================================================================
# MODE 2: COMMISSIONING (Placeholder)
# ==============================================================================
elif activity_type == "🚀 COMMISSIONING":
    st.title("🚀 Commissioning Mode")
    st.info("Modul Commissioning (API 686 / 676 Check) akan diimplementasikan selanjutnya.")
