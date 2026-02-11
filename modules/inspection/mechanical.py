import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# BAGIAN A: THE BRAIN (LOGIKA DIAGNOSA)
# ==========================================

def get_iso_limit_suggestion(kw, is_flexible=False):
    """
    Logika Smart Limit ISO 10816-3.
    Group 2 (15-300 kW): Rigid=4.5, Flexible=7.1
    Group 1 (>300 kW)  : Rigid=7.1, Flexible=11.0
    """
    if kw < 15: return 4.50
    if 15 <= kw <= 300: return 7.10 if is_flexible else 4.50
    else: return 11.0 if is_flexible else 7.10

def get_iso_remark(value_avg, limit):
    """Jalur A: ISO Severity Logic"""
    if value_avg > limit: return "🔴 DANGER"
    elif value_avg > (limit * 0.60): return "🟡 WARNING"
    elif value_avg > (limit * 0.30): return "🟢 SATISFACTORY"
    else: return "🔵 GOOD"

def analyze_hydraulic_performance(suc_bar, dis_bar, design_head_m, actual_flow_m3h, design_flow_m3h):
    """Jalur C: Hydraulic Performance Logic"""
    messages = []
    
    # 1. Head Analysis
    diff_bar = dis_bar - suc_bar
    actual_head_m = (diff_bar * 10.2) / 0.85 # Asumsi SG 0.85
    
    if design_head_m > 0:
        head_ratio = (actual_head_m / design_head_m) * 100
        if head_ratio < 75: messages.append(f"🔴 LOW HEAD PERF ({head_ratio:.0f}%): Indikasi Internal Leak / Wear Ring Aus.")
        elif head_ratio > 110: messages.append(f"🟡 HIGH HEAD ({head_ratio:.0f}%): Operasi dekat Shut-off.")

    # 2. Flow Analysis (Operating Region)
    if design_flow_m3h > 0 and actual_flow_m3h > 0:
        flow_ratio = (actual_flow_m3h / design_flow_m3h) * 100
        if flow_ratio < 60: messages.append(f"🔴 LOW FLOW ({flow_ratio:.0f}% BEP): Risiko Recirculation & Panas.")
        elif flow_ratio > 120: messages.append(f"🔴 HIGH FLOW ({flow_ratio:.0f}% BEP): Risiko Kavitasi & Motor Overload.")
    
    # 3. Suction Analysis
    if suc_bar < 0: messages.append("🔴 NEGATIVE SUCTION: Risiko Kavitasi Tinggi (Vaporization).")
        
    return messages if messages else ["🟢 Hydraulic Normal"]

def analyze_spectrum_logic(rpm, peaks):
    """Jalur D: Root Cause Analysis (Spectrum)"""
    if rpm == 0 or not peaks: return ["Data Spektrum Kosong"]
    run_speed_hz = rpm / 60
    diagnosis = []
    max_amp = max([p['amp'] for p in peaks])
    
    for peak in peaks:
        f, a = peak['freq'], peak['amp']
        if a < 0.3 or (a < 0.1 * max_amp): continue
        order = f / run_speed_hz
        
        if 0.8 <= order <= 1.2: diagnosis.append("UNBALANCE (1x RPM)")
        elif 1.8 <= order <= 2.2: diagnosis.append("MISALIGNMENT (2x RPM)")
        elif 2.8 <= order <= 3.2: diagnosis.append("LOOSENESS (3x RPM)")
        elif order > 3.5: diagnosis.append("BEARING DEFECT (High Freq)")
            
    return list(set(diagnosis)) if diagnosis else ["Spectrum Normal"]

# ==========================================
# BAGIAN B: USER INTERFACE (UI)
# ==========================================

def render_mechanical_page():
    st.header("🔍 Digital Reliability Assistant")
    st.caption("Integrated Diagnostic System: ISO 10816 + API 610 + Thermal + Structural Analysis")
    st.markdown("---")

    # --- 1. SPESIFIKASI & STANDARDISASI DATA ---
    st.subheader("📋 1. Equipment Specification")
    col_spec_motor, col_spec_pump = st.columns(2)

    with col_spec_motor:
        st.info("🔌 Driver (Motor) Spec")
        c1, c2 = st.columns([0.7, 0.3])
        p_val = c1.number_input("Rated Power", value=30.0)
        p_unit = c2.selectbox("Unit Power", ["kW", "HP"])
        m_power_kw = p_val * 0.7457 if p_unit == "HP" else p_val
            
        m_rpm = st.number_input("Rated Speed (RPM)", value=2950)
        
        # Smart Limit Logic
        is_flex = st.checkbox("Flexible Foundation? (Skid/Rubber)")
        auto_limit = get_iso_limit_suggestion(m_power_kw, is_flex)
        limit_rms = st.number_input("⚠️ ISO Trip Limit (mm/s)", value=auto_limit)
        st.caption(f"Suggestion: {auto_limit} mm/s based on ISO 10816-3 Group 2")

    with col_spec_pump:
        st.success("💧 Driven (Pump) Spec")
        p_manuf = st.text_input("Manufaktur / Tag", "P-101A")
        
        c3, c4 = st.columns([0.7, 0.3])
        h_val = c3.number_input("Design Head", value=50.0)
        h_unit = c4.selectbox("Unit Head", ["Meter (m)", "Feet (ft)"])
        design_head_m = h_val * 0.3048 if h_unit == "Feet (ft)" else h_val

        c5, c6 = st.columns([0.7, 0.3])
        q_val = c5.number_input("Design Flow (BEP)", value=100.0)
        q_unit = c6.selectbox("Unit Flow", ["m3/hr", "GPM"])
        design_flow_m3h = q_val * 0.2271 if q_unit == "GPM" else q_val

    st.markdown("---")

    # --- 2. INPUT DATA LAPANGAN (VIBRATION, THERMAL, STRUCTURAL) ---
    st.subheader("📝 2. Field Measurement Data")
    col_driver, col_driven = st.columns(2)

    # Fungsi helper input biar rapi
    def input_block(prefix):
        c1, c2 = st.columns(2)
        v_de = c1.number_input("Vel DE (mm/s)", key=f"{prefix}_v_de")
        v_nde = c2.number_input("Vel NDE (mm/s)", key=f"{prefix}_v_nde")
        
        c3, c4 = st.columns(2)
        a_de = c3.number_input("Accel DE (g)", key=f"{prefix}_a_de")
        a_nde = c4.number_input("Accel NDE (g)", key=f"{prefix}_a_nde")
        
        c5, c6 = st.columns(2)
        d_de = c5.number_input("Disp DE (μm)", key=f"{prefix}_d_de")
        d_nde = c6.number_input("Disp NDE (μm)", key=f"{prefix}_d_nde")
        
        c7, c8 = st.columns(2)
        t_de = c7.number_input("Temp DE (°C)", key=f"{prefix}_t_de", value=45.0)
        t_nde = c8.number_input("Temp NDE (°C)", key=f"{prefix}_t_nde", value=42.0)
        
        return v_de, v_nde, a_de, a_nde, d_de, d_nde, t_de, t_nde

    with col_driver:
        st.markdown("##### ⚡ Driver Side")
        m_v_de, m_v_nde, m_a_de, m_a_nde, m_d_de, m_d_nde, m_t_de, m_t_nde = input_block("m")

    with col_driven:
        st.markdown("##### 💧 Driven Side")
        p_v_de, p_v_nde, p_a_de, p_a_nde, p_d_de, p_d_nde, p_t_de, p_t_nde = input_block("p")

    st.markdown("---")
    
    # --- 3. PROCESS & SPECTRUM DATA ---
    c_proc, c_spec = st.columns(2)
    
    with c_proc:
        st.subheader("🚰 3. Process Data")
        suc = st.number_input("Suction Press (BarG)", value=0.5)
        dis = st.number_input("Discharge Press (BarG)", value=4.0)
        act_flow_in = st.number_input("Actual Flow Reading", value=95.0)
        
        # Konversi Flow Aktual
        act_flow_m3h = act_flow_in * 0.2271 if q_unit == "GPM" else act_flow_in
        
        # Live Calc
        diff = dis - suc
        curr_head = (diff * 10.2) / 0.85
        st.caption(f"Est. Actual Head: {curr_head:.1f} m | Act. Flow: {act_flow_m3h:.1f} m3/h")

    with c_spec:
        st.subheader("📈 4. Peak Picking (Spectrum)")
        with st.expander("Input 3 Puncak Tertinggi", expanded=True):
            peaks_data = []
            for i in range(1, 4):
                cc1, cc2 = st.columns(2)
                f = cc1.number_input(f"Freq {i} (Hz)", key=f"pf_{i}")
                a = cc2.number_input(f"Amp {i} (mm/s)", key=f"pa_{i}")
                if f > 0: peaks_data.append({'freq': f, 'amp': a})

    # ==========================================
    # BAGIAN C: EXECUTION & REPORTING
    # ==========================================
    if st.button("🚀 RUN COMPLETE DIAGNOSIS", type="primary", use_container_width=True):
        st.divider()
        st.title(f"📊 Reliability Report: {p_manuf}")
        
        # --- 1. DATA PROCESSING (Mencari Nilai Max/Avg) ---
        max_vel = max(m_v_de, m_v_nde, p_v_de, p_v_nde)
        max_acc = max(m_a_de, m_a_nde, p_a_de, p_a_nde)
        max_disp = max(m_d_de, m_d_nde, p_d_de, p_d_nde)
        max_temp_motor = max(m_t_de, m_t_nde)
        max_temp_pump = max(p_t_de, p_t_nde)

        # --- 2. MENJALANKAN 6 PILAR LOGIKA ---
        
        # [Jalur A] ISO Severity
        iso_status = get_iso_remark(max_vel, limit_rms)
        
        # [Jalur B] Bearing Condition
        bearing_status = "🔴 DAMAGED" if max_acc > 2.0 else ("🟡 WARNING" if max_acc > 1.0 else "🟢 GOOD")
        
        # [Jalur C] Hydraulic Logic
        hyd_msgs = analyze_hydraulic_performance(suc, dis, design_head_m, act_flow_m3h, design_flow_m3h)
        
        # [Jalur D] Spectrum Logic
        spec_msgs = analyze_spectrum_logic(m_rpm, peaks_data)
        
        # [Jalur E] Structural Logic
        struct_status = "🔴 LOOSENESS RISK" if max_disp > 100 else "🟢 RIGID"
        
        # [Jalur F] Thermal Logic
        therm_status = "🔴 OVERHEAT" if max_temp_motor > 80 else "🟢 NORMAL"

        # --- 3. TAMPILAN DASHBOARD ---
        
        # Scorecard
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Vibration (ISO)", f"{max_vel:.2f} mm/s", iso_status)
        col2.metric("Bearing Health", f"{max_acc:.2f} g", bearing_status)
        col3.metric("Structure (Disp)", f"{max_disp:.0f} μm", struct_status)
        col4.metric("Max Temp", f"{max_temp_motor:.1f} °C", therm_status)

        # Tabel Detail Vibrasi
        st.subheader("📋 Vibration Severity Table")
        vib_data = [
            {"Point": "Motor DE", "Vel (mm/s)": m_v_de, "Acc (g)": m_a_de, "Disp (μm)": m_d_de, "Temp (°C)": m_t_de},
            {"Point": "Motor NDE", "Vel (mm/s)": m_v_nde, "Acc (g)": m_a_nde, "Disp (μm)": m_d_nde, "Temp (°C)": m_t_nde},
            {"Point": "Pump DE", "Vel (mm/s)": p_v_de, "Acc (g)": p_a_de, "Disp (μm)": p_d_de, "Temp (°C)": p_t_de},
            {"Point": "Pump NDE", "Vel (mm/s)": p_v_nde, "Acc (g)": p_a_nde, "Disp (μm)": p_d_nde, "Temp (°C)": p_t_nde},
        ]
        st.dataframe(pd.DataFrame(vib_data), use_container_width=True)

        # --- 4. REKOMENDASI CERDAS (CROSS-REFERENCE) ---
        st.subheader("💡 Expert Recommendations (Root Cause)")
        
        rec_list = []
        
        # Logika Gabungan (Sintesis)
        
        # 1. Thermal + Accel (Pelumasan vs Kerusakan)
        if max_temp_motor > 60:
            if max_acc < 1.0:
                rec_list.append("🛢️ **LUBRICATION ISSUE:** Suhu Motor Tinggi tapi Vibrasi Bearing rendah. Indikasi Grease kering/kurang. Lakukan Regreasing segera.")
            else:
                rec_list.append("⚙️ **BEARING FAILURE:** Suhu Tinggi + Vibrasi Tinggi. Bearing mengalami kerusakan fisik & gesekan panas.")

        # 2. Structural + Velocity
        if max_disp > 100:
            if max_vel < limit_rms:
                rec_list.append("🏗️ **LOOSENESS:** Displacement tinggi tapi Velocity normal. Cek kekencangan Baut Pondasi (Anchor Bolt) & Frame.")
            else:
                rec_list.append("⚠️ **STRUCTURAL DAMAGE:** Displacement & Velocity tinggi. Unbalance/Misalignment sudah mengguncang struktur.")

        # 3. Spectrum Specifics
        for msg in spec_msgs:
            if "UNBALANCE" in msg: rec_list.append("⚖️ **UNBALANCE:** Lakukan Cleaning Impeller & Balancing.")
            if "MISALIGNMENT" in msg: rec_list.append("📏 **MISALIGNMENT:** Cek Softfoot & Lakukan Laser Alignment.")

        # 4. Hydraulic Specifics
        for msg in hyd_msgs:
            if "LOW FLOW" in msg: rec_list.append("🌊 **FLOW ISSUE:** Buka Valve Discharge perlahan untuk mencegah Recirculation.")
            if "HIGH FLOW" in msg: rec_list.append("🛑 **FLOW ISSUE:** Throttling valve discharge untuk mencegah Kavitasi.")
            if "LOW HEAD" in msg: rec_list.append("🔧 **PUMP WEAR:** Cek clearance Wear Ring & Impeller.")

        # Jika tidak ada masalah
        if not rec_list and iso_status == "🟢 SATISFACTORY" and bearing_status == "🟢 GOOD":
            st.success("✅ Unit dalam kondisi PRIMA. Tidak ada tindakan perbaikan yang diperlukan.")
        else:
            for rec in rec_list:
                st.warning(rec)
