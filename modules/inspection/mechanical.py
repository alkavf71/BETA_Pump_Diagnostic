import streamlit as st
import pandas as pd
import numpy as np

# --- 1. FUNGSI LOGIKA & ALGORITMA (THE BRAIN) ---
def get_remark(value_avg, limit):
    """
    Menentukan Remark berdasarkan 4 Zona ISO 10816.
    Rasio batas zona dikalibrasi sesuai standar Class I (Small Machines) referensi user:
    
    - Limit (User Input) = Batas C/D (Trip) = 100%
    - Batas B/C (Alert)  = 1.8 / 4.5 = 0.40 (40% dari Limit)
    - Batas A/B (New)    = 0.71 / 4.5 ≈ 0.16 (16% dari Limit)
    """
    # ZONE D: > 100% Limit (BAHAYA)
    if value_avg > limit:
        return "Zone D: Unacceptable (Damage Risk)"
    
    # ZONE C: 40% - 100% Limit (WARNING)
    elif value_avg > (limit * 0.40):
        # Kita tetap bisa kasih sub-notifikasi jika sudah parah (>70%)
        if value_avg > (limit * 0.70):
            return "Zone C (Upper): Restricted Operation (Plan Maintenance)"
        return "Zone C: Unsatisfactory (Alert)"
    
    # ZONE B: 16% - 40% Limit (AMAN)
    elif value_avg > (limit * 0.16):
         return "Zone B: Satisfactory (Unlimited Operation)"
    
    # ZONE A: < 16% Limit (SANGAT BAGUS/BARU)
    else:
         return "Zone A: Excellent / New Machine Condition"

def analyze_spectrum(rpm, peaks):
    """
    Menganalisis 3 puncak frekuensi dominan.
    Mengembalikan string diagnosa.
    """
    if rpm == 0: return "" # Hindari pembagian nol
    
    run_speed_hz = rpm / 60
    diagnosis = []
    tolerance = 0.15 # Toleransi 15%
    
    # Cari nilai amp tertinggi untuk referensi
    max_amp = 0
    if peaks:
        max_amp = max([p['amp'] for p in peaks])

    for peak in peaks:
        f = peak['freq']
        a = peak['amp']
        
        # Skip noise kecil (misal di bawah 10% dari max peak atau < 0.5 mm/s)
        if a < 0.5 or (max_amp > 0 and a < 0.1 * max_amp): 
            continue
            
        order = f / run_speed_hz
        
        # Logika Rule-Based
        if (1.0 - tolerance) <= order <= (1.0 + tolerance):
            diagnosis.append(f"- Dominan di 1x RPM ({f} Hz) dengan amplitudo {a} mm/s: Indikasi **UNBALANCE**.")
        elif (2.0 - tolerance) <= order <= (2.0 + tolerance):
            diagnosis.append(f"- Tinggi di 2x RPM ({f} Hz): Indikasi **MISALIGNMENT**.")
        elif (3.0 - tolerance) <= order <= (3.0 + tolerance):
            diagnosis.append(f"- Tinggi di 3x RPM ({f} Hz): Indikasi **MISALIGNMENT** atau **LOOSENESS**.")
        elif not order.is_integer() and order > 3.5:
            diagnosis.append(f"- Frekuensi tinggi non-sinkron ({f} Hz): Indikasi masalah **BEARING**.")

    if not diagnosis:
        return "" # Tidak ada diagnosa spesifik
    
    return "\n".join(diagnosis)

def generate_narrative(df_report, spectrum_analysis, hydraulic_issue):
    """Menggabungkan semua temuan menjadi satu kesimpulan naratif"""
    narrative = []
    
    # 1. Cek Overall Vibration (Dari Tabel)
    damage_rows = df_report[df_report['Remark'] == "Vibration causes damage"]
    if not damage_rows.empty:
        narrative.append("🔴 **KONDISI KRITIS (OVERALL):**")
        for idx, row in damage_rows.iterrows():
            narrative.append(f"   - {row['Component']} {row['Param']} Average ({row['Avr']:.2f} mm/s) melebihi limit.")
    
    # 2. Cek Spectrum (Jika ada input)
    if spectrum_analysis:
        narrative.append("\n🔎 **ANALISA SPEKTRUM (PENYEBAB):**")
        narrative.append(spectrum_analysis)
    
    # 3. Cek Hydraulic
    if hydraulic_issue:
         narrative.append(f"\n💧 **ISU HYDRAULIC:** {hydraulic_issue}")

    # 4. Kesimpulan Akhir
    if not narrative:
        return "✅ **KESIMPULAN:** Unit beroperasi Normal. Tidak ditemukan anomali vibrasi maupun hidrolik."
    else:
        return "\n".join(narrative)

# --- 2. TAMPILAN UTAMA (UI) ---

def render_mechanical_page():
    st.header("🔍 Mechanical Inspection Input")
    st.markdown("---")

    # --- BAGIAN 1: SPESIFIKASI & LIMIT (WAJIB ADA UNTUK RUMUS) ---
    with st.expander("⚙️ Equipment Specification (Data Awal)", expanded=True):
        c_spec1, c_spec2, c_spec3 = st.columns(3)
        eq_tag = c_spec1.text_input("Tag Number", "P-101A")
        power_kw = c_spec2.number_input("Motor Power (kW)", value=30.0)
        rpm_input = c_spec3.number_input("Running Speed (RPM)", value=1480, help="Penting untuk analisa spektrum!")
        
        st.caption("Konfigurasi Limit Evaluasi:")
        limit_rms = st.number_input("Limit Velocity RMS (mm/s)", value=4.50, step=0.1)

    # --- BAGIAN 2: FORM INPUT UTAMA (GRID LAYOUT) ---
    st.subheader("📝 Vibration Data Input")
    col_driver, col_driven = st.columns(2)

    # --- A. KOLOM DRIVER (MOTOR) ---
    with col_driver:
        st.info("⚡ DRIVER (Motor)")
        # Baris 1: Horizontal
        st.markdown("**1. Horizontal (mm/s)**")
        c1, c2 = st.columns(2)
        m_h_de = c1.number_input("DE - Horiz", key="m_h_de")
        m_h_nde = c2.number_input("NDE - Horiz", key="m_h_nde")
        # Baris 2: Vertical
        st.markdown("**2. Vertical (mm/s)**")
        c3, c4 = st.columns(2)
        m_v_de = c3.number_input("DE - Vert", key="m_v_de")
        m_v_nde = c4.number_input("NDE - Vert", key="m_v_nde")
        # Baris 3: Axial
        st.markdown("**3. Axial (mm/s)**")
        c5, c6 = st.columns(2)
        m_a_de = c5.number_input("DE - Axial", key="m_a_de")
        m_a_nde = c6.number_input("NDE - Axial", key="m_a_nde")
        # Baris 4: Temp
        st.markdown("**4. Temp (°C)**")
        c7, c8 = st.columns(2)
        m_t_de = c7.number_input("DE - Temp", key="m_t_de")
        m_t_nde = c8.number_input("NDE - Temp", key="m_t_nde")

    # --- B. KOLOM DRIVEN (POMPA) ---
    with col_driven:
        st.success("💧 DRIVEN (Pompa)")
        # Baris 1: Horizontal
        st.markdown("**1. Horizontal (mm/s)**")
        p1, p2 = st.columns(2)
        p_h_de = p1.number_input("DE - Horiz", key="p_h_de")
        p_h_nde = p2.number_input("NDE - Horiz", key="p_h_nde")
        # Baris 2: Vertical
        st.markdown("**2. Vertical (mm/s)**")
        p3, p4 = st.columns(2)
        p_v_de = p3.number_input("DE - Vert", key="p_v_de")
        p_v_nde = p4.number_input("NDE - Vert", key="p_v_nde")
        # Baris 3: Axial
        st.markdown("**3. Axial (mm/s)**")
        p5, p6 = st.columns(2)
        p_a_de = p5.number_input("DE - Axial", key="p_a_de")
        p_a_nde = p6.number_input("NDE - Axial", key="p_a_nde")
        # Baris 4: Temp
        st.markdown("**4. Temp (°C)**")
        p7, p8 = st.columns(2)
        p_t_de = p7.number_input("DE - Temp", key="p_t_de")
        p_t_nde = p8.number_input("NDE - Temp", key="p_t_nde")

    # --- BAGIAN 3: ANALISA LANJUT & HYDRAULIC ---
    st.markdown("---")
    c_adv, c_hyd = st.columns(2)

    with c_adv:
        # Input Peak Picking disembunyikan dalam Expander agar tidak penuh, tapi ADA.
        with st.expander("📈 Advanced Spectrum (Peak Picking)", expanded=True):
            st.caption("Masukkan 3 puncak tertinggi dari Adash untuk diagnosa otomatis.")
            peaks_data = []
            for i in range(1, 4):
                cols = st.columns([1, 1])
                f = cols[0].number_input(f"Freq Puncak {i} (Hz)", min_value=0.0, key=f"fp_{i}")
                a = cols[1].number_input(f"Amp Puncak {i} (mm/s)", min_value=0.0, key=f"ap_{i}")
                if f > 0 and a > 0:
                    peaks_data.append({'freq': f, 'amp': a})

    with c_hyd:
        st.markdown("##### 🚰 Hydraulic Data")
        suc = st.number_input("Suction Press (BarG)", value=0.5)
        dis = st.number_input("Discharge Press (BarG)", value=4.0)

    # --- BUTTON PROCESS ---
    st.markdown("---")
    process_btn = st.button("🚀 GENERATE REPORT & DIAGNOSIS", type="primary", use_container_width=True)

    # --- 4. OUTPUT HASIL ---
    if process_btn:
        st.divider()
        st.header("📊 Laporan Hasil Inspeksi")
        st.write(f"**Equipment:** {eq_tag} | **RPM:** {rpm_input} | **Limit:** {limit_rms} mm/s")

        # A. BUILD TABLE (Sama seperti sebelumnya)
        def calc_avg(v1, v2): return (v1 + v2) / 2
        
        data_rows = [
            {"Component": "Driver", "Param": "H", "DE": m_h_de, "NDE": m_h_nde, "Limit": limit_rms},
            {"Component": "Driver", "Param": "V", "DE": m_v_de, "NDE": m_v_nde, "Limit": limit_rms},
            {"Component": "Driver", "Param": "A", "DE": m_a_de, "NDE": m_a_nde, "Limit": limit_rms},
            {"Component": "Driver", "Param": "T (°C)", "DE": m_t_de, "NDE": m_t_nde, "Limit": None},
            {"Component": "Driven", "Param": "H", "DE": p_h_de, "NDE": p_h_nde, "Limit": limit_rms},
            {"Component": "Driven", "Param": "V", "DE": p_v_de, "NDE": p_v_nde, "Limit": limit_rms},
            {"Component": "Driven", "Param": "A", "DE": p_a_de, "NDE": p_a_nde, "Limit": limit_rms},
            {"Component": "Driven", "Param": "T (°C)", "DE": p_t_de, "NDE": p_t_nde, "Limit": None},
        ]
        df = pd.DataFrame(data_rows)
        df["Avr"] = df.apply(lambda x: calc_avg(x["DE"], x["NDE"]), axis=1)
        df["Remark"] = df.apply(lambda x: "-" if x["Param"]=="T (°C)" else get_remark(x["Avr"], x["Limit"]), axis=1)

        # TAMPILKAN TABEL
        st.dataframe(
            df[["Component", "Param", "DE", "NDE", "Avr", "Limit", "Remark"]].style.format({
                "DE": "{:.2f}", "NDE": "{:.2f}", "Avr": "{:.2f}", "Limit": "{:.2f}"
            }),
            use_container_width=True, hide_index=True, height=300
        )

        # B. PROSES ANALISA (SPEKTRUM & HYDRAULIC)
        # 1. Analisa Spektrum
        spec_result = analyze_spectrum(rpm_input, peaks_data)
        
        # 2. Analisa Hydraulic
        hyd_issue = ""
        diff_press = dis - suc
        if diff_press < 1.0: hyd_issue = f"Differential Pressure Rendah ({diff_press:.1f} Bar). Cek Impeller/RPM."
        
        # 3. Generate Narasi Gabungan
        final_conclusion = generate_narrative(df, spec_result, hyd_issue)

        # TAMPILKAN KESIMPULAN
        st.markdown("### 📝 Kesimpulan & Rekomendasi Teknik")
        
        if "Normal" in final_conclusion:
            st.success(final_conclusion)
        else:
            st.warning(final_conclusion)
            
            st.markdown("""
            **Rekomendasi Umum:**
            1. Jika diagnosa **Unbalance**: Lakukan pembersihan (cleaning) pada kipas/impeller, cek balancing.
            2. Jika diagnosa **Misalignment**: Cek kondisi kopling (coupling), lakukan alignment ulang.
            3. Jika diagnosa **Bearing**: Cek lubrikasi (greasing), monitor bunyi abnormal.
            """)
