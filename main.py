import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- IMPORT MODULES ---
from modules.asset_database import get_asset_list, get_asset_details
from modules.inspection.mechanical import MechanicalInspector
from modules.inspection.electrical import ElectricalInspector
from modules.inspection.hydraulic import HydraulicInspector # <--- IMPORT MODULE BARU

# --- PAGE CONFIG ---
st.set_page_config(page_title="Reliability Pro Enterprise", layout="wide", page_icon="🏭")

# --- CSS UTILS (Untuk Warna Tabel Mekanikal) ---
def highlight_row(row):
    remark = row.get('Remark', '')
    if "ZONE D" in remark: 
        return ['background-color: #ffebee; color: #b71c1c']*len(row) # Merah Pucat
    elif "ZONE C" in remark: 
        return ['background-color: #fffde7; color: #f57f17']*len(row) # Kuning Pucat
    elif "ZONE A" in remark: 
        return ['background-color: #e8f5e9; color: #1b5e20; font-weight: bold']*len(row) # Hijau Pucat
    else: 
        return ['background-color: #ffffff; color: #212529']*len(row) # Putih Normal

# ==============================================================================
# SIDEBAR: PILIH ASET
# ==============================================================================
st.sidebar.title("🏭 Reliability Pro")
st.sidebar.subheader("Asset Selection")

# 1. Load Database
asset_names = get_asset_list()
selected_tag = st.sidebar.selectbox("Pilih Aset / Tag Number:", asset_names)
asset = get_asset_details(selected_tag)

# 2. Tampilkan Spesifikasi Aset
with st.sidebar.expander("ℹ️ Spesifikasi Aset", expanded=True):
    st.markdown(f"**Nama:** {asset.name}")
    st.markdown(f"**Type:** {asset.pump_type}")
    st.markdown(f"**Power:** {asset.power_kw} kW")
    st.markdown(f"**RPM:** {asset.rpm}")
    st.markdown(f"**Elec:** {asset.volt_rated}V / {asset.fla_rated}A")
    st.markdown("---")
    st.markdown(f"**ISO Limit (Warn):** `{asset.vib_limit_warning} mm/s`")
    st.markdown(f"**ISO Limit (Trip):** `{asset.vib_limit_alarm} mm/s`")

mode = st.sidebar.radio("Mode Aplikasi:", ["🛠️ INSPEKSI RUTIN", "🚀 COMMISSIONING"])

# ==============================================================================
# MODE 1: INSPEKSI RUTIN
# ==============================================================================
if mode == "🛠️ Under Construction Alkavf Corp":
    st.title(f"🛠️ Engineered by TnX: {asset.tag}")

    # Init Inspectors dengan Parameter Aset
    mech_inspector = MechanicalInspector(vib_limit_warn=asset.vib_limit_warning)
    elec_inspector = ElectricalInspector()
    hydro_inspector = HydraulicInspector() # <--- INIT INSPECTOR BARU

    # Tab Menu
    tab1, tab2, tab3 = st.tabs(["⚙️ MEKANIKAL & HIDROLIK", "⚡ ELEKTRIKAL", "👁️ VISUAL"])

    # --------------------------------------------------------------------------
    # TAB 1: MEKANIKAL (Vibrasi, Suhu, Noise, Hidrolik)
    # --------------------------------------------------------------------------
    with tab1:
        st.info(f"Limit vibrasi otomatis: **{asset.vib_limit_warning} mm/s** (ISO 20816 Group Based on {asset.power_kw} kW).")
        
        with st.form("mech_form"):
            col1, col2 = st.columns(2)
            
            # 1. INPUT DRIVER (MOTOR)
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

            # 2. INPUT DRIVEN (POMPA)
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
            
            st.markdown("---")
            
            # 3. INPUT HIDROLIK & NOISE (Dibuat berdampingan)
            c_bot1, c_bot2 = st.columns(2)
            
            with c_bot1:
                st.subheader("3. Performa Hidrolik (Pressure)")
                cp1, cp2, cp3 = st.columns(3)
                p_in = cp1.number_input("Suction (Bar):", value=0.5, step=0.1)
                p_out = cp2.number_input("Discharge (Bar):", value=4.5, step=0.1)
                sg = cp3.number_input("SG Fluid:", value=0.85, step=0.01)
                
                # Input Design Head (Nanti bisa diambil otomatis dari DB jika data lengkap)
                design_head = st.number_input("Rated Head Design (m):", value=50.0, help="Lihat Nameplate")
                
            with c_bot2:
                st.subheader("4. Akustik (Noise)")
                cn1, cn2 = st.columns(2)
                dba_val = cn1.number_input("Sound Level (dBA):", value=80.0, step=0.1)
                dba_base = cn2.number_input("Baseline (dBA):", value=78.0, step=0.1)
                noise_type = st.selectbox("Jenis Suara:", ["Normal / Halus", "Kavitasi", "Bearing Defect", "Mencicit"])

            submit_mech = st.form_submit_button("🔍 ANALISA KESEHATAN MEKANIKAL FULL")

        # --- HASIL ANALISA ---
        if submit_mech:
            # A. ANALISA VIBRASI
            inputs_vib = {
                'm_de_h': m_de_h, 'm_de_v': m_de_v, 'm_de_a': m_de_a,
                'm_nde_h': m_nde_h, 'm_nde_v': m_nde_v, 'm_nde_a': m_nde_a,
                'p_de_h': p_de_h, 'p_de_v': p_de_v, 'p_de_a': p_de_a,
                'p_nde_h': p_nde_h, 'p_nde_v': p_nde_v, 'p_nde_a': p_nde_a
            }
            inputs_temp = {'Motor DE': t_m_de, 'Motor NDE': t_m_nde, 'Pump DE': t_p_de, 'Pump NDE': t_p_nde}
            
            res_mech = mech_inspector.analyze_full_health(inputs_vib, inputs_temp, noise_type)

            # B. ANALISA HIDROLIK
            res_hydro = hydro_inspector.analyze_performance(p_in, p_out, sg, design_head)

            st.divider()
            
            # --- LAYOUT HASIL ---
            # Kiri: Tabel Vibrasi & Diagnosa Mekanikal
            # Kanan: Diagnosa Hidrolik & Gauge Vibrasi
            
            res_c1, res_c2 = st.columns([1.5, 1])
            
            with res_c1:
                st.markdown("#### 📋 Laporan Vibrasi & Suhu")
                st.dataframe(
                    res_mech['dataframe'].style.apply(highlight_row, axis=1)
                    .format({"DE": "{:.2f}", "NDE": "{:.2f}", "Avr": "{:.2f}", "Limit": "{:.2f}"}),
                    use_container_width=True, hide_index=True
                )
                
                # Logic Safety Noise
                delta_db = dba_val - dba_base
                if dba_val > 85.0:
                    st.error(f"🔊 **SAFETY ALERT:** {dba_val} dBA (Wajib Earplug - OSHA Limit).")
                elif delta_db >= 6.0:
                    st.warning(f"🔊 **NOISE WARNING:** Naik +{delta_db:.1f} dB. Indikasi degradasi.")

                # Diagnosa Multi-Fault Mekanikal
                if res_mech['faults']:
                    st.error("🚨 **DIAGNOSA MEKANIKAL:**")
                    for f in res_mech['faults']:
                        with st.expander(f"⚠️ {f['name']}", expanded=True):
                            st.info(f"**Pemicu:** {f.get('trigger', '-')}")
                            st.markdown(f"**Analisa:** {f['desc']}")
                            st.markdown(f"**Action:** {f['action']}")
                else:
                    st.success("✅ Mekanikal Sehat (Vibrasi & Suhu Normal).")

            with res_c2:
                st.markdown("#### 🌊 Performa Hidrolik")
                
                # Metric Head
                st.metric(
                    label="Actual Total Head",
                    value=f"{res_hydro['actual_head']:.1f} m",
                    delta=f"{res_hydro['deviation']:.1f}% vs Design"
                )
                
                # Status Card Hidrolik
                if res_hydro['status'] == "NORMAL":
                    st.success(f"**{res_hydro['status']}**")
                    st.caption(res_hydro['desc'])
                else:
                    st.warning(f"**{res_hydro['status']}**")
                    st.markdown(f"**Analisa:** {res_hydro['desc']}")
                    st.markdown(f"**Action:** {res_hydro['action']}")

                st.markdown("---")
                
                # Gauge Vibrasi
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number", value = res_mech['max_vib'], title = {'text': "Max Vib (mm/s)"},
                    gauge = {
                        'axis': {'range': [0, asset.vib_limit_alarm * 1.5]},
                        'bar': {'color': "black"},
                        'steps': [
                            {'range': [0, asset.vib_limit_warning], 'color': "#e8f5e9"},
                            {'range': [asset.vib_limit_warning, asset.vib_limit_alarm], 'color': "#fffde7"},
                            {'range': [asset.vib_limit_alarm, asset.vib_limit_alarm * 1.5], 'color': "#ffebee"}
                        ],
                        'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': asset.vib_limit_warning}
                    }
                ))
                fig.update_layout(height=200, margin=dict(t=10,b=10,l=10,r=10))
                st.plotly_chart(fig, use_container_width=True)

    # --------------------------------------------------------------------------
    # TAB 2: ELEKTRIKAL (Modern UI)
    # --------------------------------------------------------------------------
    with tab2:
        # Header Info
        c_info1, c_info2 = st.columns([3, 1])
        with c_info1:
            st.markdown(f"### ⚡ Motor Health Monitor: **{asset.name}**")
        with c_info2:
            st.caption(f"Rated: **{asset.volt_rated} V / {asset.fla_rated} A**")

        # Input Form (Expander)
        with st.expander("📝 Input Data Pengukuran (Klik untuk Buka/Tutup)", expanded=True):
            with st.form("elec_form"):
                ce1, ce2 = st.columns(2)
                with ce1:
                    st.markdown("**1. Tegangan (Volt Phase-to-Phase)**")
                    c_v1, c_v2, c_v3 = st.columns(3)
                    v_rs = c_v1.number_input("R-S", value=float(asset.volt_rated), step=1.0)
                    v_st = c_v2.number_input("S-T", value=float(asset.volt_rated), step=1.0)
                    v_tr = c_v3.number_input("T-R", value=float(asset.volt_rated), step=1.0)
                with ce2:
                    st.markdown("**2. Arus Beban (Ampere)**")
                    c_i1, c_i2, c_i3 = st.columns(3)
                    i_r = c_i1.number_input("R", value=float(asset.fla_rated)*0.8, step=0.1)
                    i_s = c_i2.number_input("S", value=float(asset.fla_rated)*0.8, step=0.1)
                    i_t = c_i3.number_input("T", value=float(asset.fla_rated)*0.8, step=0.1)
                    
                submit_elec = st.form_submit_button("⚡ ANALISA KUALITAS DAYA")

        # Dashboard Hasil
        if submit_elec:
            vol_inputs = [v_rs, v_st, v_tr]
            amp_inputs = [i_r, i_s, i_t]
            
            df_elec, elec_faults, elec_status, load_pct = elec_inspector.analyze_health(
                vol_inputs, amp_inputs, asset.volt_rated, asset.fla_rated
            )
            
            # Helper metrics
            v_avg = sum(vol_inputs)/3
            i_avg = sum(amp_inputs)/3
            v_unbal_val = float(df_elec.loc[df_elec['Parameter']=='Unbalance V', 'Value'].values[0].replace(' %',''))
            i_unbal_val = float(df_elec.loc[df_elec['Parameter']=='Unbalance I', 'Value'].values[0].replace(' %',''))

            st.divider()

            # 1. STATUS CARD
            if elec_status == "NORMAL":
                st.markdown("""<div style="padding:15px; border-radius:10px; background-color:#e8f5e9; border-left: 6px solid #2ecc71;">
                    <h3 style="color:#1b5e20; margin:0;">✅ SYSTEM HEALTHY</h3><p style="margin:0;">Kualitas daya listrik aman (IEC 60034).</p></div>""", unsafe_allow_html=True)
            elif elec_status == "WARNING":
                st.markdown("""<div style="padding:15px; border-radius:10px; background-color:#fff3cd; border-left: 6px solid #ffc107;">
                    <h3 style="color:#856404; margin:0;">⚠️ WARNING ALERT</h3><p style="margin:0;">Penyimpangan parameter terdeteksi.</p></div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div style="padding:15px; border-radius:10px; background-color:#f8d7da; border-left: 6px solid #dc3545;">
                    <h3 style="color:#721c24; margin:0;">🚨 CRITICAL FAULT</h3><p style="margin:0;">Bahaya! Parameter trip/safety terlampaui.</p></div>""", unsafe_allow_html=True)

            st.write("") 

            # 2. KEY METRICS
            km1, km2, km3, km4 = st.columns(4)
            with km1: st.metric("Avg Voltage", f"{v_avg:.1f} V", f"{v_avg - asset.volt_rated:.1f} V")
            with km2: 
                d_color = "normal" if v_unbal_val < 1.0 else "inverse"
                st.metric("Volt Unbalance", f"{v_unbal_val:.2f}%", "Max 1.0%", delta_color=d_color)
            with km3: st.metric("Avg Current", f"{i_avg:.1f} A")
            with km4:
                l_color = "normal" if load_pct < 100 else "inverse"
                st.metric("Motor Load", f"{load_pct:.1f}%", "Max 100%", delta_color=l_color)

            st.markdown("---")

            # 3. VISUAL BALANCE CHECK (CHARTS)
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.subheader("📊 Voltage Balance")
                fig_v = go.Figure()
                fig_v.add_trace(go.Bar(x=['R-S', 'S-T', 'T-R'], y=vol_inputs, marker_color='#4285F4', text=vol_inputs, textposition='auto'))
                fig_v.add_hline(y=asset.volt_rated, line_dash="dot", annotation_text="Rated", line_color="green")
                min_v, max_v = min(vol_inputs)*0.95, max(vol_inputs)*1.05
                fig_v.update_layout(yaxis_range=[min_v, max_v], height=250, margin=dict(t=10,b=10,l=10,r=10))
                st.plotly_chart(fig_v, use_container_width=True)

            with col_chart2:
                st.subheader("📊 Current Balance")
                fig_i = go.Figure()
                colors_i = ['#FF5252' if x > asset.fla_rated else '#FFB74D' for x in amp_inputs]
                fig_i.add_trace(go.Bar(x=['R', 'S', 'T'], y=amp_inputs, marker_color=colors_i, text=amp_inputs, textposition='auto'))
                fig_i.add_hline(y=asset.fla_rated, line_dash="dash", annotation_text="Max FLA", line_color="red")
                fig_i.update_layout(height=250, margin=dict(t=10,b=10,l=10,r=10))
                st.plotly_chart(fig_i, use_container_width=True)

            # 4. DIAGNOSA DETAIL
            if elec_faults:
                st.error("🚨 **DETIL DIAGNOSA & REKOMENDASI**")
                for f in elec_faults:
                    with st.expander(f"🔴 ISU: {f['name']} ({f['val']})", expanded=True):
                        st.markdown(f"**Analisa:** {f['desc']}")
                        st.markdown(f"**Action:** {f['action']}")

    # --------------------------------------------------------------------------
    # TAB 3: VISUAL
    # --------------------------------------------------------------------------
    with tab3:
        st.info("Fitur Visual & Safety Check (Segera Hadir di Update Berikutnya)")

# ==============================================================================
# MODE 2: COMMISSIONING
# ==============================================================================
elif mode == "🚀 COMMISSIONING":
    st.title(f"🚀 Commissioning Check: {asset.tag}")
    st.warning("Modul Commissioning sedang dalam tahap pengembangan.")
