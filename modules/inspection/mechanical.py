import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. BAGIAN LOGIKA & ALGORITMA (THE BRAIN)
# ==========================================
# Catatan: Semua fungsi di sini HANYA menerima satuan SI (kW, Meter, m3/hr)

def get_iso_limit_suggestion(kw, is_flexible=False):
    """
    Logika Penentuan Limit ISO 10816-3 (Group 1 & 2).
    Group 2 (15-300 kW): Rigid=4.5, Flexible=7.1
    Group 1 (>300 kW)  : Rigid=7.1, Flexible=11.0
    """
    if kw < 15:
        return 4.50 # Default untuk mesin kecil (<15kW biasanya pakai rule of thumb)
        
    if 15 <= kw <= 300: # Group 2 (Medium)
        return 7.10 if is_flexible else 4.50
    else: # Group 1 (Large > 300kW)
        return 11.0 if is_flexible else 7.10

def get_iso_remark(value_avg, limit):
    """Logika Penilaian Severity ISO 10816"""
    if value_avg > limit: return "Vibration causes damage"
    elif value_avg > (limit * 0.60): return "Short-term operation allowable"
    elif value_avg > (limit * 0.30): return "Unlimited long-term operation allowable"
    else: return "New machine condition"

def analyze_hydraulic_performance(suc_bar, dis_bar, design_head_m, actual_flow_m3h, design_flow_m3h):
    """
    Diagnosa Hidrolik Lanjutan (Sesuai API 610 & HI 9.6.3).
    Input: Pressure (Bar), Head (m), Flow (m3/h).
    """
    messages = []
    
    # 1. Cek Head Performance (Pressure Generation)
    diff_bar = dis_bar - suc_bar
    actual_head_m = (diff_bar * 10.2) / 0.85 # Asumsi SG 0.85 (BBM)
    
    if design_head_m > 0:
        head_ratio = (actual_head_m / design_head_m) * 100
        if head_ratio < 70:
            messages.append(f"🔴 LOW HEAD PERF: Hanya {head_ratio:.0f}% dari Desain (Indikasi: Impeller/Wear Ring Aus).")
        elif head_ratio > 110:
            messages.append(f"🟡 HIGH HEAD: {head_ratio:.0f}% (Indikasi: Operasi dekat Shut-off / Buntu).")

    # 2. Cek Flow Performance (Operating Region - API 610)
    # Preferred Operating Region (POR) biasanya 70% - 120% dari BEP (Design Flow)
    if design_flow_m3h > 0 and actual_flow_m3h > 0:
        flow_ratio = (actual_flow_m3h / design_flow_m3h) * 100
        
        if flow_ratio < 60:
             messages.append(f"🔴 LOW FLOW ({flow_ratio:.0f}% BEP): Risiko Recirculation & Vibrasi Tinggi.")
        elif flow_ratio < 70:
             messages.append(f"🟡 BELOW POR ({flow_ratio:.0f}% BEP): Kurang Efisien.")
        elif flow_ratio > 120:
             messages.append(f"🔴 HIGH FLOW ({flow_ratio:.0f}% BEP): Risiko Kavitasi & Motor Overload.")
        else:
             messages.append(f"🟢 GOOD FLOW ({flow_ratio:.0f}% BEP): Operasi di Titik Efisiensi Terbaik.")
    
    elif actual_flow_m3h == 0:
         messages.append("⚪ INFO: Data Flow Meter 0 / Tidak Diinput.")

    return "\n".join(messages) if messages else "Normal Hydraulic Condition"

def analyze_spectrum_logic(rpm, peaks):
    """Diagnosa Spektrum (Unbalance, Misalign, Looseness)"""
    if rpm == 0 or not peaks: return "Data Spektrum Tidak Tersedia"
    run_speed_hz = rpm / 60
    diagnosis = []
    tolerance = 0.15
    max_amp = max([p['amp'] for p in peaks])
    
    for peak in peaks:
        f, a = peak['freq'], peak['amp']
        if a < 0.3 or (a < 0.1 * max_amp): continue # Filter noise
        order = f / run_speed_hz
        
        if (1.0 - tolerance) <= order <= (1.0 + tolerance): diagnosis.append("UNBALANCE")
        elif (2.0 - tolerance) <= order <= (2.0 + tolerance): diagnosis.append("MISALIGNMENT")
        elif (3.0 - tolerance) <= order <= (3.0 + tolerance): diagnosis.append("LOOSENESS")
        elif order > 3.5: diagnosis.append("BEARING DEFECT")
            
    return ", ".join(set(diagnosis)) if diagnosis else "Normal"

# ==========================================
# 2. TAMPILAN ANTARMUKA (UI)
# ==========================================

def render_mechanical_page():
    st.header("🔍 Mechanical & Process Inspection")
    st.markdown("---")

    # ==========================================
    # INPUT STEP 1: SPESIFIKASI (NORMALISASI DATA)
    # ==========================================
    st.subheader("📋 1. Equipment Specification (Data Plat Nama)")
    
    col_spec_motor, col_spec_pump = st.columns(2)

    with col_spec_motor:
        st.info("🔌 Spesifikasi Motor (Driver)")
        
        # Input Power & RPM
        c1, c2 = st.columns([0.7, 0.3])
        p_val = c1.number_input("Rated Power", value=30.0)
        p_unit = c2.selectbox("Satuan", ["kW", "HP"])
        
        if p_unit == "HP":
            m_power_kw = p_val * 0.7457
        else:
            m_power_kw = p_val
            
        m_rpm = st.number_input("Rated Speed (RPM)", value=2950)
        
        # --- FITUR SMART LIMIT ---
        st.write("---")
        st.caption("🏗️ Tipe Pondasi (Untuk Auto-Limit ISO)")
        # Checkbox untuk Flexible Foundation
        is_flex = st.checkbox("Flexible Foundation? (Skid/Rubber/Lantai Atas)")
        
        # Panggil fungsi Smart Limit
        auto_limit = get_iso_limit_suggestion(m_power_kw, is_flex)
        
        # Tampilkan Limit (User tetap bisa edit manual kalau mau kustom)
        limit_rms = st.number_input("⚠️ ISO Vibration Limit (Trip)", value=auto_limit, step=0.1)
        
        if is_flex:
            st.caption(f"ℹ️ Mode Flexible: Limit dilonggarkan ke {auto_limit} mm/s")
        else:
            st.caption(f"ℹ️ Mode Rigid (Default): Limit ketat di {auto_limit} mm/s")

    with col_spec_pump:
        st.success("💧 Spesifikasi Pompa (Driven)")
        p_manuf = st.text_input("Manufaktur / Model", "KSB / Blackmer")
        
        # --- INPUT HEAD DENGAN PILIHAN SATUAN ---
        c3, c4 = st.columns([0.7, 0.3])
        h_val = c3.number_input("Design Head (BEP)", value=50.0)
        h_unit = c4.selectbox("Satuan Head", ["Meter (m)", "Feet (ft)"])
        
        # [LOGIC KONVERSI] Head ke Meter
        if h_unit == "Feet (ft)":
            design_head_m = h_val * 0.3048
            st.caption(f"ℹ️ Konversi: {h_val} ft = {design_head_m:.2f} m")
        else:
            design_head_m = h_val

        # --- INPUT FLOW DESAIN DENGAN PILIHAN SATUAN ---
        c5, c6 = st.columns([0.7, 0.3])
        q_val = c5.number_input("Design Flow (BEP)", value=100.0)
        q_unit = c6.selectbox("Satuan Flow", ["m3/hr", "GPM (US)"])
        
        # [LOGIC KONVERSI] Flow ke m3/hr
        if q_unit == "GPM (US)":
            design_flow_m3h = q_val * 0.2271
            st.caption(f"ℹ️ Konversi: {q_val} GPM = {design_flow_m3h:.2f} m3/h")
        else:
            design_flow_m3h = q_val

    st.markdown("---")

    # ==========================================
    # INPUT STEP 2: VIBRATION DATA (FIELD)
    # ==========================================
    st.subheader("📝 2. Vibration Data Entry (ADASH/VibXpert)")
    col_driver, col_driven = st.columns(2)

    def input_row(label, key_prefix):
        st.markdown(f"**{label}**")
        c_de, c_nde = st.columns(2)
        v_de = c_de.number_input(f"DE", key=f"{key_prefix}_de")
        v_nde = c_nde.number_input(f"NDE", key=f"{key_prefix}_nde")
        return v_de, v_nde

    with col_driver:
        st.markdown("##### Driver (Motor)")
        m_h_de, m_h_nde = input_row("1. Vel - Horizontal (mm/s)", "m_h")
        m_v_de, m_v_nde = input_row("2. Vel - Vertical (mm/s)", "m_v")
        m_a_de, m_a_nde = input_row("3. Vel - Axial (mm/s)", "m_a")
        m_acc_de, m_acc_nde = input_row("4. Accel (g)", "m_acc")
        m_disp_de, m_disp_nde = input_row("5. Disp (μm)", "m_disp")

    with col_driven:
        st.markdown("##### Driven (Pompa)")
        p_h_de, p_h_nde = input_row("1. Vel - Horizontal (mm/s)", "p_h")
        p_v_de, p_v_nde = input_row("2. Vel - Vertical (mm/s)", "p_v")
        p_a_de, p_a_nde = input_row("3. Vel - Axial (mm/s)", "p_a")
        p_acc_de, p_acc_nde = input_row("4. Accel (g)", "p_acc")
        p_disp_de, p_disp_nde = input_row("5. Disp (μm)", "p_disp")

    st.markdown("---")
    
    # ==========================================
    # INPUT STEP 3: PROCESS DATA (FLOW & PRESSURE)
    # ==========================================
    st.subheader("🚰 3. Process & Hydraulic Data")
    c_proc1, c_proc2 = st.columns(2)
    
    with c_proc1:
        st.markdown("##### Pressure Reading")
        suc = st.number_input("Suction Press (BarG)", value=0.5)
        dis = st.number_input("Discharge Press (BarG)", value=4.0)
        
        # Kalkulasi Head Aktual
        diff = dis - suc
        act_head_m = (diff * 10.2) / 0.85 # Asumsi SG 0.85
        st.metric("Actual Head Est.", f"{act_head_m:.1f} m")

    with c_proc2:
        st.markdown("##### Flow Meter Reading")
        # Input Flow Aktual (Lapangan)
        act_flow_input = st.number_input("Actual Flow Rate (Reading)", value=90.0)
        
        # Konversi Flow Aktual agar match dengan Design Flow
        if q_unit == "GPM (US)":
            act_flow_m3h = act_flow_input * 0.2271
            st.caption(f"Running: {act_flow_m3h:.1f} m3/h")
        else:
            act_flow_m3h = act_flow_input

    # Input Spektrum (Disembunyikan di expander biar rapi)
    with st.expander("📈 Input Data Spektrum (Peak Picking)"):
        peaks_data = []
        for i in range(1, 4):
            cc1, cc2 = st.columns(2)
            f = cc1.number_input(f"Freq {i} (Hz)", key=f"pf_{i}")
            a = cc2.number_input(f"Amp {i} (mm/s)", key=f"pa_{i}")
            if f > 0: peaks_data.append({'freq': f, 'amp': a})

    # ==========================================
    # EXECUTION: GENERATE REPORT
    # ==========================================
    if st.button("🚀 ANALYZE & GENERATE REPORT", type="primary", use_container_width=True):
        st.divider()
        st.header(f"📊 Laporan Diagnosa: {p_manuf}")
        
        # Summary Header
        c_sum1, c_sum2, c_sum3 = st.columns(3)
        c_sum1.metric("Motor Power", f"{m_power_kw:.1f} kW")
        c_sum2.metric("Running Speed", f"{m_rpm} RPM")
        
        # Hitung % Flow Operation
        if design_flow_m3h > 0:
            flow_pct = (act_flow_m3h / design_flow_m3h) * 100
            c_sum3.metric("Operating Point", f"{flow_pct:.0f}% BEP")

        # TABEL 1: VIBRATION ISO
        st.subheader("1. Evaluasi Vibrasi (ISO 10816-3)")
        vib_data = [
            {"Point": "Driver", "Dir": "H", "DE": m_h_de, "NDE": m_h_nde, "Limit": limit_rms},
            {"Point": "Driver", "Dir": "V", "DE": m_v_de, "NDE": m_v_nde, "Limit": limit_rms},
            {"Point": "Driver", "Dir": "A", "DE": m_a_de, "NDE": m_a_nde, "Limit": limit_rms},
            {"Point": "Driven", "Dir": "H", "DE": p_h_de, "NDE": p_h_nde, "Limit": limit_rms},
            {"Point": "Driven", "Dir": "V", "DE": p_v_de, "NDE": p_v_nde, "Limit": limit_rms},
            {"Point": "Driven", "Dir": "A", "DE": p_a_de, "NDE": p_a_nde, "Limit": limit_rms},
        ]
        df_vib = pd.DataFrame(vib_data)
        df_vib["Avr"] = (df_vib["DE"] + df_vib["NDE"]) / 2
        df_vib["Remark"] = df_vib.apply(lambda x: get_iso_remark(x["Avr"], x["Limit"]), axis=1)
        st.dataframe(df_vib.style.format({"DE": "{:.2f}", "NDE": "{:.2f}", "Avr": "{:.2f}", "Limit": "{:.2f}"}), use_container_width=True, hide_index=True)

        # TABEL 2: DIAGNOSA KOMPREHENSIF
        st.subheader("2. Kesimpulan Diagnosa")
        
        # Run Logic
        spec_diag = analyze_spectrum_logic(m_rpm, peaks_data)
        hyd_diag = analyze_hydraulic_performance(suc, dis, design_head_m, act_flow_m3h, design_flow_m3h)
        
        # Tampilkan Hasil
        diag_summary = [
            {"Domain": "Mekanikal (Spektrum)", "Hasil Analisa": spec_diag},
            {"Domain": "Hidrolik & Proses", "Hasil Analisa": hyd_diag},
        ]
        st.table(pd.DataFrame(diag_summary))

        # REKOMENDASI OTOMATIS
        st.subheader("3. Rekomendasi Tindakan")
        rec_list = []
        if "UNBALANCE" in spec_diag: rec_list.append("- Lakukan Balancing In-situ atau di Workshop.")
        if "MISALIGNMENT" in spec_diag: rec_list.append("- Cek Softfoot & Lakukan Laser Alignment.")
        if "LOW FLOW" in hyd_diag: rec_list.append("- Buka Valve Discharge perlahan atau cek saringan suction (Mencegah Recirculation).")
        if "HIGH FLOW" in hyd_diag: rec_list.append("- Throttling valve discharge untuk mengembalikan ke kurva operasi (Mencegah Kavitasi).")
        
        if not rec_list:
            st.success("✅ Unit beroperasi dalam batas normal. Lanjutkan monitoring rutin.")
        else:
            for rec in rec_list:
                st.warning(rec)
