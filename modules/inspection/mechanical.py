import streamlit as st
import pandas as pd
import numpy as np

# --- 1. LOGIC & ALGORITHM FUNCTION ---

def get_iso10816_remark(velocity_rms, limit_rms):
    """
    Memberikan Remark berdasarkan limit perusahaan.
    """
    # Logika sederhana berdasarkan gambar user
    # Jika limit 4.5, maka > 4.5 adalah danger/damage
    
    if velocity_rms <= limit_rms:
        return "Unlimited long-term operation allowable"
    elif velocity_rms <= (limit_rms * 2.5): # Asumsi Zone C (Warning)
        return "Short-term operation allowable"
    else:
        return "Vibration causes damage"

def analyze_comprehensive(data_report, spec_limit):
    """
    Menganalisa seluruh data frame untuk membuat kesimpulan naratif.
    """
    issues = []
    
    # 1. Cek Driver (Motor)
    motor_h_avr = data_report.loc['Driver', 'H']['Avr']
    motor_v_avr = data_report.loc['Driver', 'V']['Avr']
    motor_a_avr = data_report.loc['Driver', 'A']['Avr']
    
    if max(motor_h_avr, motor_v_avr, motor_a_avr) > spec_limit:
        issues.append("🔴 **MOTOR (Driver) High Vibration:** Rata-rata vibrasi motor melebihi batas yang diizinkan.")
        if motor_h_avr > motor_v_avr:
             issues.append("   - Dominasi arah Horizontal pada motor mengindikasikan kemungkinan **Unbalance** atau masalah kekakuan struktur.")
        if motor_a_avr > motor_v_avr and motor_a_avr > motor_h_avr:
             issues.append("   - Dominasi arah Axial pada motor sering dikaitkan dengan **Misalignment** poros.")

    # 2. Cek Driven (Pump)
    pump_h_avr = data_report.loc['Driven', 'H']['Avr']
    pump_v_avr = data_report.loc['Driven', 'V']['Avr']
    pump_a_avr = data_report.loc['Driven', 'A']['Avr']
    
    if max(pump_h_avr, pump_v_avr, pump_a_avr) > spec_limit:
        issues.append("🔴 **POMPA (Driven) High Vibration:** Rata-rata vibrasi pompa melebihi batas.")
        if pump_v_avr > pump_h_avr:
             issues.append("   - Dominasi arah Vertikal pada pompa bisa mengindikasikan **Looseness** (kelonggaran kaki/baut).")

    # 3. Kesimpulan Umum
    if not issues:
        return "✅ **KONDISI AMAN:** Semua parameter vibrasi berada di bawah batas limit (Allowable). Peralatan layak operasi jangka panjang."
    else:
        intro = "⚠️ **KESIMPULAN INSPEKSI:**\nDitemukan anomali sebagai berikut:\n"
        return intro + "\n".join(issues)

# --- 2. MAIN UI FUNCTION ---

def render_mechanical_page():
    st.title("🔧 Mechanical Diagnostics Report")
    st.markdown("---")

    # --- A. SETTING LIMIT & SPEC ---
    with st.expander("⚙️ Equipment Specification & Limits", expanded=True):
        col1, col2 = st.columns(2)
        eq_tag = col1.text_input("Tag Number", "P-101A")
        limit_val = col2.number_input("Limit RMS (mm/s)", value=4.5, help="Standard ISO 10816 Zone Boundary")

    # --- B. INPUT DATA (TABULAR) ---
    st.subheader("📝 Input Data Pengukuran")
    
    # Kita bagi dua kolom besar: DRIVER (Motor) & DRIVEN (Pompa)
    col_driver, col_driven = st.columns(2)
    
    # --- INPUT DRIVER (MOTOR) ---
    with col_driver:
        st.info("⚡ DRIVER (Motor)")
        # Horizontal
        c1, c2 = st.columns(2)
        m_h_de = c1.number_input("Horiz - DE (mm/s)", key="m_h_de")
        m_h_nde = c2.number_input("Horiz - NDE (mm/s)", key="m_h_nde")
        # Vertical
        c3, c4 = st.columns(2)
        m_v_de = c3.number_input("Vert - DE (mm/s)", key="m_v_de")
        m_v_nde = c4.number_input("Vert - NDE (mm/s)", key="m_v_nde")
        # Axial
        c5, c6 = st.columns(2)
        m_a_de = c5.number_input("Axial - DE (mm/s)", key="m_a_de")
        m_a_nde = c6.number_input("Axial - NDE (mm/s)", key="m_a_nde")
        # Temperature
        c7, c8 = st.columns(2)
        m_t_de = c7.number_input("Temp - DE (°C)", key="m_t_de")
        m_t_nde = c8.number_input("Temp - NDE (°C)", key="m_t_nde")

    # --- INPUT DRIVEN (POMPA) ---
    with col_driven:
        st.success("💧 DRIVEN (Pompa)")
        # Horizontal
        p1, p2 = st.columns(2)
        p_h_de = p1.number_input("Horiz - DE (mm/s)", key="p_h_de")
        p_h_nde = p2.number_input("Horiz - NDE (mm/s)", key="p_h_nde")
        # Vertical
        p3, p4 = st.columns(2)
        p_v_de = p3.number_input("Vert - DE (mm/s)", key="p_v_de")
        p_v_nde = p4.number_input("Vert - NDE (mm/s)", key="p_v_nde")
        # Axial
        p5, p6 = st.columns(2)
        p_a_de = p5.number_input("Axial - DE (mm/s)", key="p_a_de")
        p_a_nde = p6.number_input("Axial - NDE (mm/s)", key="p_a_nde")
        # Temperature
        p7, p8 = st.columns(2)
        p_t_de = p7.number_input("Temp - DE (°C)", key="p_t_de")
        p_t_nde = p8.number_input("Temp - NDE (°C)", key="p_t_nde")

    st.markdown("---")
    
    # --- C. INPUT HYDRAULIC ---
    st.subheader("🚰 Hydraulic Data")
    h1, h2 = st.columns(2)
    suc_press = h1.number_input("Suction Pressure (BarG)", value=0.5)
    dis_press = h2.number_input("Discharge Pressure (BarG)", value=4.0)

    # --- BUTTON GENERATE REPORT ---
    if st.button("📄 GENERATE FINAL REPORT", type="primary"):
        
        st.markdown("## 📊 Laporan Inspeksi Getaran")
        st.caption(f"Tag Number: {eq_tag} | Standard Limit: {limit_val} mm/s")

        # --- 1. PROSES DATA AGAR SEPERTI GAMBAR ---
        # Helper untuk menghitung rata-rata
        def calc_avg(val1, val2):
            return (val1 + val2) / 2 if (val1 > 0 or val2 > 0) else 0

        # Struktur Data untuk Tabel
        data = {
            'Component': ['Driver', 'Driver', 'Driver', 'Driver', 'Driven', 'Driven', 'Driven', 'Driven'],
            'Param': ['H', 'V', 'A', 'Temp (°C)', 'H', 'V', 'A', 'Temp (°C)'],
            'DE': [m_h_de, m_v_de, m_a_de, m_t_de, p_h_de, p_v_de, p_a_de, p_t_de],
            'NDE': [m_h_nde, m_v_nde, m_a_nde, m_t_nde, p_h_nde, p_v_nde, p_a_nde, p_t_nde],
        }
        
        df = pd.DataFrame(data)
        
        # Hitung Average
        df['Avr'] = df.apply(lambda row: calc_avg(row['DE'], row['NDE']), axis=1)
        
        # Tambah Kolom Limit
        df['Limits RMS'] = limit_val
        # Khusus baris Temperature, Limit biasanya beda (misal 80 C), tapi di gambar Anda kosong/tidak ada limit vibrasi.
        # Kita kosongkan limit vibrasi untuk baris Temp
        df.loc[df['Param'] == 'Temp (°C)', 'Limits RMS'] = np.nan

        # Tambah Kolom Remark
        def determine_remark(row):
            if row['Param'] == 'Temp (°C)':
                return "-" # Skip temperatur untuk remark vibrasi
            return get_iso10816_remark(row['Avr'], limit_val)

        df['Remark'] = df.apply(determine_remark, axis=1)

        # --- 2. DISPLAY TABEL (STYLE MIRIP EXCEL PERUSAHAAN) ---
        # Kita pivot/set index agar tampilannya rapi grouped by Driver/Driven
        
        # Format angka 2 desimal
        st.dataframe(
            df.style.format({
                "DE": "{:.2f}", 
                "NDE": "{:.2f}", 
                "Avr": "{:.2f}",
                "Limits RMS": "{:.2f}"
            }),
            use_container_width=True,
            hide_index=True
        )

        # --- 3. ANALISA HYDRAULIC ---
        st.markdown("### 🚰 Hydraulic Performance")
        diff_head = dis_press - suc_press
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("Suction", f"{suc_press} Bar")
        col_res2.metric("Discharge", f"{dis_press} Bar")
        col_res3.metric("Differential Pressure", f"{diff_head:.2f} Bar")
        
        if diff_head < 1.0:
            st.warning("⚠️ **Low Performance:** Selisih tekanan sangat rendah. Cek Impeller/RPM.")
        
        # --- 4. KESIMPULAN AKHIR & REKOMENDASI ---
        st.markdown("### 📝 Kesimpulan & Rekomendasi")
        
        # Persiapan data untuk fungsi analisa logika
        # Kita ubah DF jadi MultiIndex agar mudah diambil datanya oleh fungsi analyze_comprehensive
        df_analysis = df.set_index(['Component', 'Param'])
        
        # Panggil fungsi analisa
        conclusion_text = analyze_comprehensive(df_analysis, limit_val)
        
        st.info(conclusion_text)
        
        # Rekomendasi General (Hardcoded logic based on conclusion)
        if "High Vibration" in conclusion_text:
            st.markdown("""
            **Rekomendasi Tindakan:**
            1. 🔍 Lakukan pengecekan spektrum (FFT) untuk memastikan jenis kerusakan (Unbalance/Misalign).
            2. 🔧 Cek kekencangan baut pondasi (Soft foot check).
            3. 📏 Cek alignment poros saat unit stop.
            """)
        else:
             st.markdown("""
            **Rekomendasi Tindakan:**
            1. ✅ Pertahankan kondisi operasi.
            2. 📅 Lakukan monitoring rutin bulan depan.
            """)
