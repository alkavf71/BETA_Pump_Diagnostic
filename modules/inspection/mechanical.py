import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. BAGIAN LOGIKA & ALGORITMA
# ==========================================

def get_iso_limit_suggestion(kw):
    """
    Menyarankan Limit ISO 10816-3 berdasarkan Power (kW).
    """
    if kw > 300:
        return 4.50 
    elif 15 <= kw <= 300:
        return 4.50 
    else:
        return 4.50 

def get_iso_remark(value_avg, limit):
    if value_avg > limit:
        return "Vibration causes damage"
    elif value_avg > (limit * 0.60):
        return "Short-term operation allowable"
    elif value_avg > (limit * 0.30):
        return "Unlimited long-term operation allowable"
    else:
        return "New machine condition"

def analyze_hydraulic_performance(suc_bar, dis_bar, design_head_m):
    """
    Mendiagnosa kesehatan hidrolik pompa.
    Konversi Head Aktual (m) = (Diff Bar * 10.2) / SG
    """
    if design_head_m == 0: return "Data Head Desain Kosong"
    
    diff_bar = dis_bar - suc_bar
    # Asumsi Specific Gravity (SG) rata-rata BBM = 0.85
    actual_head_m = (diff_bar * 10.2) / 0.85 
    
    performance_ratio = (actual_head_m / design_head_m) * 100
    
    if performance_ratio < 70:
        return f"CRITICAL: Low Performance ({performance_ratio:.0f}% dari Desain). Cek Wear Ring/Impeller."
    elif performance_ratio < 85:
        return f"WARNING: Degradasi Performa ({performance_ratio:.0f}% dari Desain)."
    elif performance_ratio > 110:
        return f"WARNING: Operasi di luar kurva (High Head/Shut-off)."
    else:
        return f"NORMAL: Performa Hidrolik Baik ({performance_ratio:.0f}%)."

def analyze_spectrum_logic(rpm, peaks):
    if rpm == 0 or not peaks: return "Data Spektrum Tidak Tersedia"
    run_speed_hz = rpm / 60
    diagnosis = []
    tolerance = 0.15
    max_amp = max([p['amp'] for p in peaks])
    for peak in peaks:
        f, a = peak['freq'], peak['amp']
        if a < 0.3 or (a < 0.1 * max_amp): continue
        order = f / run_speed_hz
        if (1.0 - tolerance) <= order <= (1.0 + tolerance):
            diagnosis.append("UNBALANCE")
        elif (2.0 - tolerance) <= order <= (2.0 + tolerance):
            diagnosis.append("MISALIGNMENT")
        elif (3.0 - tolerance) <= order <= (3.0 + tolerance):
            diagnosis.append("LOOSENESS")
        elif order > 3.5:
            diagnosis.append("BEARING DEFECT")
    return ", ".join(set(diagnosis)) if diagnosis else "Normal"

# ==========================================
# 2. TAMPILAN ANTARMUKA (UI)
# ==========================================

def render_mechanical_page():
    st.header("🔍 Mechanical Inspection Input")
    st.markdown("---")

    # --- BAGIAN INPUT SPESIFIKASI (SESUAI FORM PERTAMINA) ---
    st.subheader("📋 Equipment Specification Data")
    
    col_spec_pump, col_spec_motor = st.columns(2)

    # --- III. SPESIFIKASI POMPA ---
    with col_spec_pump:
        st.markdown("### III. Spesifikasi Pompa")
        with st.container(border=True):
            p_manuf = st.text_input("Manufaktur (Pompa)", "Blackmer")
            p_model = st.text_input("Model (Pompa)", "FRA")
            p_sn = st.text_input("S/N (Pompa)", "1041535A")
            
            c_p1, c_p2 = st.columns(2)
            p_gpm = c_p1.number_input("GPM (Flow)", value=500.0)
            p_imp_dia = c_p2.text_input("IMP DIA", "8.25")
            
            c_p3, c_p4 = st.columns(2)
            p_rated_speed = c_p3.number_input("Rated speed (r/min) - Pump", value=2900)
            p_hd_ft = c_p4.number_input("HD-FT (Head Feet)", value=164.0)
            
            c_p5, c_p6 = st.columns(2)
            p_max_imp = c_p5.text_input("MAX IMP", "9.62")
            p_max_psi = c_p6.number_input("MAX DSGN PSI @100F", value=625)
            
            p_size = st.text_input("Size", "3X4-10")

    # --- IV. SPESIFIKASI ELECTRO MOTOR ---
    with col_spec_motor:
        st.markdown("### IV. Spesifikasi Electro Motor")
        with st.container(border=True):
            m_manuf = st.text_input("Manufaktur (Motor)", "ABB")
            
            c_m1, c_m2 = st.columns(2)
            m_volt = c_m1.number_input("Rated Voltaged", value=400)
            m_freq = c_m2.number_input("Frequency (Hz)", value=50)
            
            c_m3, c_m4 = st.columns(2)
            m_rated_speed = c_m3.number_input("Rated speed (r/min) - Motor", value=2956)
            m_power_kw = c_m4.number_input("Power (kW)", value=30.0)
            
            m_sn = st.text_input("Serial No. (Motor)", "3G1P141602588")
            m_install_date = st.text_input("Installation date", "2014")

            # Auto-Calculation Limit berdasarkan kW Motor
            iso_limit = get_iso_limit_suggestion(m_power_kw)
            st.divider()
            limit_rms = st.number_input("⚠️ Vibration Limit (ISO Trip) mm/s", value=iso_limit)

    st.markdown("---")

    # --- INPUT INSPEKSI LAPANGAN ---
    st.subheader("📝 Vibration Data Entry")
    col_driver, col_driven = st.columns(2)

    def input_row(label, key_prefix):
        st.markdown(f"**{label}**")
        c_de, c_nde = st.columns(2)
        v_de = c_de.number_input(f"DE", key=f"{key_prefix}_de")
        v_nde = c_nde.number_input(f"NDE", key=f"{key_prefix}_nde")
        return v_de, v_nde

    with col_driver:
        st.info("⚡ DRIVER (Motor)")
        m_h_de, m_h_nde = input_row("1. Horizontal (mm/s)", "m_h")
        m_v_de, m_v_nde = input_row("2. Vertical (mm/s)", "m_v")
        m_a_de, m_a_nde = input_row("3. Axial (mm/s)", "m_a")
        m_acc_de, m_acc_nde = input_row("4. Acceleration (g)", "m_acc")
        m_disp_de, m_disp_nde = input_row("5. Displacement (μm)", "m_disp")
        m_t_de, m_t_nde = input_row("6. Temp (°C)", "m_t")

    with col_driven:
        st.success("💧 DRIVEN (Pompa)")
        p_h_de, p_h_nde = input_row("1. Horizontal (mm/s)", "p_h")
        p_v_de, p_v_nde = input_row("2. Vertical (mm/s)", "p_v")
        p_a_de, p_a_nde = input_row("3. Axial (mm/s)", "p_a")
        p_acc_de, p_acc_nde = input_row("4. Acceleration (g)", "p_acc")
        p_disp_de, p_disp_nde = input_row("5. Displacement (μm)", "p_disp")
        p_t_de, p_t_nde = input_row("6. Temp (°C)", "p_t")

    st.markdown("---")
    
    # --- INPUT LANJUTAN (SPEKTRUM & HIDROLIK) ---
    c_adv, c_hyd = st.columns(2)
    with c_adv:
        with st.expander("📈 Advanced Spectrum Input", expanded=True):
            peaks_data = []
            for i in range(1, 4):
                cc1, cc2 = st.columns(2)
                f = cc1.number_input(f"Freq {i} (Hz)", key=f"pf_{i}")
                a = cc2.number_input(f"Amp {i} (mm/s)", key=f"pa_{i}")
                if f > 0: peaks_data.append({'freq': f, 'amp': a})

    with c_hyd:
        st.markdown("##### 🚰 Hydraulic Process Data")
        suc = st.number_input("Suction Press (BarG)", value=0.5)
        dis = st.number_input("Discharge Press (BarG)", value=3.5)
        
        # Konversi Head dari Feet ke Meter untuk kalkulasi
        design_head_m = p_hd_ft * 0.3048
        
        diff = dis - suc
        act_head_m = (diff * 10.2) / 0.85
        st.caption(f"Design Head (m): {design_head_m:.2f} m | Act. Head: {act_head_m:.2f} m")

    # --- TOMBOL GENERATE ---
    if st.button("🚀 GENERATE COMPLETE REPORT", type="primary", use_container_width=True):
        st.divider()
        st.header(f"📊 Laporan Diagnosa: {p_model} / {m_sn}")
        st.caption(f"Motor: {m_power_kw} kW | Speed: {m_rated_speed} RPM | Pump Head: {p_hd_ft} ft")

        # --- TABEL 1: VIBRATION ---
        st.subheader("1. Tabel Vibrasi (ISO 10816)")
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

        # --- TABEL 2: PARAMETER LAIN ---
        st.subheader("2. Parameter Kondisi Bearing & Struktur")
        supp_data = [
            {"Point": "Driver", "Accel (g)": (m_acc_de + m_acc_nde)/2, "Disp (μm)": (m_disp_de + m_disp_nde)/2, "Temp (°C)": (m_t_de + m_t_nde)/2},
            {"Point": "Driven", "Accel (g)": (p_acc_de + p_acc_nde)/2, "Disp (μm)": (p_disp_de + p_disp_nde)/2, "Temp (°C)": (p_t_de + p_t_nde)/2},
        ]
        st.table(pd.DataFrame(supp_data))

        # --- TABEL 3: DIAGNOSA AKHIR ---
        st.subheader("3. Kesimpulan Diagnosa & Rekomendasi")
        
        # 1. Diagnosa Vibrasi
        spec_diag = analyze_spectrum_logic(m_rated_speed, peaks_data)
        
        # 2. Diagnosa Hidrolik (Konversi Feet ke Meter dulu)
        design_head_meter = p_hd_ft * 0.3048
        hyd_diag = analyze_hydraulic_performance(suc, dis, design_head_meter)
        
        # 3. Status Keseluruhan
        is_danger = any("damage" in r.lower() for r in df_vib["Remark"])
        status_final = "🔴 DANGER / STOP" if is_danger else "🟢 NORMAL OPERATING"
        if "WARNING" in hyd_diag: status_final = "🟡 ALERT / CHECK"

        # Rekomendasi Logic
        rec_list = []
        if "UNBALANCE" in spec_diag: rec_list.append("- Cleaning Impeller & Balancing")
        if "MISALIGNMENT" in spec_diag: rec_list.append("- Laser Alignment Check")
        if "Low Performance" in hyd_diag: rec_list.append("- Cek Internal Clearance / Wear Ring Pompa")
        if not rec_list: rec_list.append("- Monitoring Rutin")

        diag_summary = [
            {"Kategori": "Status Equipment", "Hasil": status_final},
            {"Kategori": "Diagnosa Vibrasi", "Hasil": spec_diag},
            {"Kategori": "Diagnosa Hidrolik", "Hasil": hyd_diag},
            {"Kategori": "Rekomendasi", "Hasil": "\n".join(rec_list)}
        ]
        st.table(pd.DataFrame(diag_summary))
