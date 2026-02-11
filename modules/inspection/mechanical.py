import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. BAGIAN LOGIKA & ALGORITMA (THE BRAIN)
# ==========================================

def get_iso_remark(value_avg, limit):
    """
    Menentukan Remark sesuai Legend Chart ISO 10816 (Gambar User).
    
    Klasifikasi:
    - Zone D (> Limit)      : Vibration causes damage
    - Zone C (60-100% Limit): Short-term operation allowable
    - Zone B (30-60% Limit) : Unlimited long-term operation allowable
    - Zone A (< 30% Limit)  : New machine condition
    """
    
    # ZONE D: Merah (Bahaya)
    if value_avg > limit:
        return "Vibration causes damage"
    
    # ZONE C: Oranye (Warning)
    # Di grafik, batas C biasanya sekitar 60% dari batas Trip (Misal 2.8 dari 4.5)
    elif value_avg > (limit * 0.60):
        return "Short-term operation allowable"
    
    # ZONE B: Kuning (Aman Operasi)
    # Di grafik, batas B biasanya sekitar 30% dari batas Trip (Misal 1.4 dari 4.5)
    elif value_avg > (limit * 0.30):
         return "Unlimited long-term operation allowable"
    
    # ZONE A: Hijau (Sangat Bagus)
    else:
         return "New machine condition"

def analyze_bearing_condition(acc_val):
    """Analisa kondisi bearing berdasarkan Acceleration (g)"""
    # Rule of Thumb Industri
    if acc_val > 2.0:
        return "🔴 **CRITICAL BEARING:** Acceleration > 2.0g. Indikasi kerusakan fisik (spalling). Ganti segera."
    elif acc_val > 1.0:
        return "🟡 **BEARING WARNING:** Acceleration > 1.0g. Indikasi kurang lubrikasi. Lakukan regreasing."
    return ""

def analyze_structural_stiffness(disp_val, vel_val):
    """Analisa kekakuan struktur berdasarkan Displacement (μm)"""
    # Threshold 100μm (bisa disesuaikan standar perusahaan)
    if disp_val > 100.0:
        if vel_val < 4.0:
            return f"🟡 **STRUCTURAL LOOSENESS:** Displacement tinggi ({disp_val:.0f} μm) tapi Velocity rendah. Cek baut pondasi/pipa."
        else:
            return f"🔴 **EXCESSIVE MOVEMENT:** Displacement ({disp_val:.0f} μm) & Velocity tinggi. Risiko kerusakan struktur fatal."
    return ""

def analyze_spectrum(rpm, peaks):
    """Diagnosa Penyebab (Root Cause) via Peak Picking"""
    if rpm == 0: return ""
    
    run_speed_hz = rpm / 60
    diagnosis = []
    tolerance = 0.15 # Toleransi 15% untuk Slip Motor
    
    # Cari max amplitude untuk filter noise
    max_amp = max([p['amp'] for p in peaks]) if peaks else 0

    for peak in peaks:
        f = peak['freq']
        a = peak['amp']
        
        # Filter noise (abaikan jika < 10% dari puncak tertinggi atau < 0.3 mm/s)
        if a < 0.3 or (max_amp > 0 and a < 0.1 * max_amp): continue
            
        order = f / run_speed_hz
        
        # Logika Diagnosa
        if (1.0 - tolerance) <= order <= (1.0 + tolerance):
            diagnosis.append(f"- Dominan 1x RPM ({f} Hz): Indikasi **UNBALANCE**.")
        elif (2.0 - tolerance) <= order <= (2.0 + tolerance):
            diagnosis.append(f"- Tinggi di 2x RPM ({f} Hz): Indikasi **MISALIGNMENT**.")
        elif (3.0 - tolerance) <= order <= (3.0 + tolerance):
             diagnosis.append(f"- Tinggi di 3x RPM ({f} Hz): Indikasi **LOOSENESS**.")
        elif not order.is_integer() and order > 3.5:
             diagnosis.append(f"- Frekuensi tinggi ({f} Hz): Indikasi **BEARING DEFECT**.")

    return "\n".join(diagnosis) if diagnosis else ""

def generate_comprehensive_report(df, spectrum_msg, hyd_msg):
    """Menyusun Kesimpulan Akhir"""
    narrative = []
    
    # 1. Cek Overall Velocity (ISO)
    danger_rows = df[(df['Param'].isin(['H', 'V', 'A'])) & (df['Remark'].str.contains('Zone C|Zone D'))]
    if not danger_rows.empty:
        narrative.append("🔴 **KONDISI VELOCITY (ISO 10816):**")
        for _, row in danger_rows.iterrows():
            narrative.append(f"   - {row['Component']} {row['Param']} ({row['Avr']:.2f} mm/s): {row['Remark']}")

    # 2. Cek Acceleration (Bearing)
    acc_rows = df[df['Param'] == 'Accel (g)']
    for _, row in acc_rows.iterrows():
        msg = analyze_bearing_condition(row['Avr'])
        if msg: narrative.append(f"   - {row['Component']}: {msg}")

    # 3. Cek Displacement (Struktur)
    # Kita butuh pair Displacement & Velocity tertinggi untuk logika ini
    for comp in ['Driver', 'Driven']:
        disp_row = df[(df['Component'] == comp) & (df['Param'] == 'Disp (μm)')]
        if not disp_row.empty:
            d_val = disp_row.iloc[0]['Avr']
            # Ambil max velocity dari komponen yg sama
            v_rows = df[(df['Component'] == comp) & (df['Param'].isin(['H','V','A']))]
            max_v = v_rows['Avr'].max() if not v_rows.empty else 0
            
            struct_msg = analyze_structural_stiffness(d_val, max_v)
            if struct_msg: narrative.append(f"   - {comp}: {struct_msg}")

    # 4. Cek Spektrum
    if spectrum_msg:
        narrative.append("\n🔎 **ANALISA SPEKTRUM (PENYEBAB):**")
        narrative.append(spectrum_msg)

    # 5. Cek Hydraulic
    if hyd_msg:
        narrative.append(f"\n💧 **ISU HYDRAULIC:** {hyd_msg}")

    if not narrative:
        return "✅ **KESIMPULAN:** Unit beroperasi Normal (Excellent). Tidak ditemukan anomali signifikan."
    else:
        return "\n".join(narrative)

# ==========================================
# 2. TAMPILAN ANTARMUKA (UI)
# ==========================================

def render_mechanical_page():
    st.header("🔍 Mechanical Inspection Input")
    st.markdown("---")

    # --- A. SPESIFIKASI & LIMIT ---
    with st.expander("⚙️ Equipment Specification & Limits", expanded=True):
        c1, c2, c3 = st.columns(3)
        eq_tag = c1.text_input("Tag Number", "P-101A")
        rpm_val = c2.number_input("Running Speed (RPM)", value=1480, step=10, help="Wajib untuk analisa spektrum!")
        limit_rms = c3.number_input("Limit Velocity (Trip) mm/s", value=4.50, step=0.1)

    # --- B. FORM INPUT DATA (GRID LAYOUT) ---
    st.subheader("📝 Vibration Data Entry")
    col_driver, col_driven = st.columns(2)

    # Helper function untuk membuat input row
    def input_row(label, key_prefix):
        st.markdown(f"**{label}**")
        c_de, c_nde = st.columns(2)
        v_de = c_de.number_input(f"DE", key=f"{key_prefix}_de")
        v_nde = c_nde.number_input(f"NDE", key=f"{key_prefix}_nde")
        return v_de, v_nde

    # --- DRIVER (MOTOR) ---
    with col_driver:
        st.info("⚡ DRIVER (Motor)")
        m_h_de, m_h_nde = input_row("1. Horizontal (mm/s)", "m_h")
        m_v_de, m_v_nde = input_row("2. Vertical (mm/s)", "m_v")
        m_a_de, m_a_nde = input_row("3. Axial (mm/s)", "m_a")
        m_acc_de, m_acc_nde = input_row("4. Acceleration (g)", "m_acc") # Input Bearing
        m_disp_de, m_disp_nde = input_row("5. Displacement (μm)", "m_disp") # Input Struktur
        m_t_de, m_t_nde = input_row("6. Temp (°C)", "m_t")

    # --- DRIVEN (POMPA) ---
    with col_driven:
        st.success("💧 DRIVEN (Pompa)")
        p_h_de, p_h_nde = input_row("1. Horizontal (mm/s)", "p_h")
        p_v_de, p_v_nde = input_row("2. Vertical (mm/s)", "p_v")
        p_a_de, p_a_nde = input_row("3. Axial (mm/s)", "p_a")
        p_acc_de, p_acc_nde = input_row("4. Acceleration (g)", "p_acc")
        p_disp_de, p_disp_nde = input_row("5. Displacement (μm)", "p_disp")
        p_t_de, p_t_nde = input_row("6. Temp (°C)", "p_t")

    # --- C. ANALISA LANJUT (PEAK PICKING) & HYDRAULIC ---
    st.markdown("---")
    c_adv, c_hyd = st.columns(2)

    with c_adv:
        with st.expander("📈 Advanced Spectrum (Peak Picking)", expanded=True):
            st.caption("Masukkan 3 Puncak Tertinggi dari ADASH")
            peaks_data = []
            for i in range(1, 4):
                cc1, cc2 = st.columns(2)
                f = cc1.number_input(f"Freq {i} (Hz)", key=f"pf_{i}")
                a = cc2.number_input(f"Amp {i} (mm/s)", key=f"pa_{i}")
                if f > 0: peaks_data.append({'freq': f, 'amp': a})

    with c_hyd:
        st.markdown("##### 🚰 Hydraulic Data")
        suc = st.number_input("Suction (BarG)", value=0.5)
        dis = st.number_input("Discharge (BarG)", value=4.0)

    # --- TOMBOL PROSES ---
    st.markdown("---")
    if st.button("🚀 GENERATE COMPLETE REPORT", type="primary", use_container_width=True):
        
        st.divider()
        st.header(f"📊 Laporan Inspeksi: {eq_tag}")
        st.write(f"**RPM:** {rpm_val} | **Velocity Limit:** {limit_rms} mm/s")

        # 1. MENYUSUN DATAFRAME UTAMA
        raw_data = [
            # Driver
            {"Component": "Driver", "Param": "H", "DE": m_h_de, "NDE": m_h_nde, "Limit": limit_rms},
            {"Component": "Driver", "Param": "V", "DE": m_v_de, "NDE": m_v_nde, "Limit": limit_rms},
            {"Component": "Driver", "Param": "A", "DE": m_a_de, "NDE": m_a_nde, "Limit": limit_rms},
            {"Component": "Driver", "Param": "Accel (g)", "DE": m_acc_de, "NDE": m_acc_nde, "Limit": 1.0}, # Limit g visual saja
            {"Component": "Driver", "Param": "Disp (μm)", "DE": m_disp_de, "NDE": m_disp_nde, "Limit": 100}, # Limit um visual saja
            {"Component": "Driver", "Param": "Temp (°C)", "DE": m_t_de, "NDE": m_t_nde, "Limit": None},
            # Driven
            {"Component": "Driven", "Param": "H", "DE": p_h_de, "NDE": p_h_nde, "Limit": limit_rms},
            {"Component": "Driven", "Param": "V", "DE": p_v_de, "NDE": p_v_nde, "Limit": limit_rms},
            {"Component": "Driven", "Param": "A", "DE": p_a_de, "NDE": p_a_nde, "Limit": limit_rms},
            {"Component": "Driven", "Param": "Accel (g)", "DE": p_acc_de, "NDE": p_acc_nde, "Limit": 1.0},
            {"Component": "Driven", "Param": "Disp (μm)", "DE": p_disp_de, "NDE": p_disp_nde, "Limit": 100},
            {"Component": "Driven", "Param": "Temp (°C)", "DE": p_t_de, "NDE": p_t_nde, "Limit": None},
        ]
        
        df = pd.DataFrame(raw_data)
        
        # Hitung Avr
        df["Avr"] = (df["DE"] + df["NDE"]) / 2
        
        # Hitung Remark (Logic berbeda tiap parameter)
        def determine_row_remark(row):
            p = row['Param']
            val = row['Avr']
            lim = row['Limit']
            
            # 1. Logika untuk Velocity (ISO 10816)
            if p in ['H', 'V', 'A']: 
                return get_iso_remark(val, lim)
            
            # 2. Logika untuk Acceleration (Bearing)
            elif p == 'Accel (g)': 
                if val > 2.0: return "Vibration causes damage" # Atau 'Bearing Damaged' jika ingin beda
                if val > 1.0: return "Short-term operation allowable" # Atau 'Lubrication Required'
                return "Unlimited long-term operation allowable"
            
            # 3. Logika untuk Displacement (Struktur)
            elif p == 'Disp (μm)': 
                if val > 100: return "Short-term operation allowable" # Visual Check
                return "Unlimited long-term operation allowable"
            
            return "-" # Untuk Temp

        df["Remark"] = df.apply(determine_row_remark, axis=1)

        # 2. TAMPILKAN TABEL
        st.dataframe(
            df.style.format({"DE": "{:.2f}", "NDE": "{:.2f}", "Avr": "{:.2f}", "Limit": "{:.2f}"}),
            use_container_width=True, hide_index=True, height=500
        )

        # 3. PROSES DIAGNOSA NARATIF
        # A. Spektrum
        spec_msg = analyze_spectrum(rpm_val, peaks_data)
        
        # B. Hydraulic
        hyd_msg = ""
        diff = dis - suc
        if diff < 1.0: hyd_msg = f"Diff Pressure Rendah ({diff:.1f} Bar). Cek performa pompa."
        
        # C. Generate Full Report
        final_conclusion = generate_comprehensive_report(df, spec_msg, hyd_msg)

        # 4. OUTPUT KESIMPULAN
        st.markdown("### 📝 Kesimpulan & Rekomendasi Teknik")
        if "Normal" in final_conclusion:
            st.success(final_conclusion)
        else:
            st.warning(final_conclusion)
            st.markdown("""
            **Rekomendasi Tindakan (Action Plan):**
            1. **Unbalance:** Cleaning Impeller / Balancing In-situ.
            2. **Misalignment:** Cek Coupling / Laser Alignment.
            3. **Bearing Issue:** Regreasing / Ganti Bearing (jika g > 2.0).
            4. **Looseness:** Torque check baut pondasi.
            """)
