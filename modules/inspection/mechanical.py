import streamlit as st
import pandas as pd
import numpy as np

# --- 1. FUNGSI LOGIKA & PERHITUNGAN ---

def get_remark(value_avg, limit):
    """
    Menentukan Remark berdasarkan logic:
    Jika Avg > Limit -> Vibration causes damage
    Jika Avg <= Limit -> Unlimited long-term operation
    (Logic disederhanakan sesuai screenshot Anda)
    """
    if value_avg > limit:
        return "Vibration causes damage"
    elif value_avg > (limit * 0.7): # Zone Warning (Opsional)
        return "Short-term operation allowable"
    else:
        return "Unlimited long-term operation allowable"

def analyze_conclusion(df_report):
    """
    Membuat kesimpulan narasi otomatis dari data tabel.
    """
    issues = []
    
    # Filter baris yang remark-nya "Vibration causes damage"
    damage_rows = df_report[df_report['Remark'] == "Vibration causes damage"]
    
    if not damage_rows.empty:
        for index, row in damage_rows.iterrows():
            comp = row['Component']
            param = row['Param']
            val = row['Avr']
            issues.append(f"🔴 **{comp} - {param}:** Nilai rata-rata {val:.2f} mm/s (High Vibration).")
            
        return "⚠️ **KESIMPULAN:** Ditemukan indikasi vibrasi tinggi yang berpotensi merusak peralatan. Segera lakukan pengecekan detail (Spectrum Analysis) pada titik-titik di atas."
    else:
        return "✅ **KESIMPULAN:** Peralatan beroperasi dalam batas aman (Allowable). Tidak ditemukan anomali vibrasi yang signifikan."

# --- 2. TAMPILAN UTAMA (UI) ---

def render_mechanical_page():
    st.header("🔍 Mechanical Inspection Input")
    st.caption("Masukkan data sesuai pembacaan alat (DE & NDE berdampingan).")
    st.markdown("---")

    # --- BAGIAN 1: SETTING LIMIT ---
    with st.expander("⚙️ Konfigurasi Standar & Limit", expanded=False):
        c_set1, c_set2 = st.columns(2)
        eq_tag = c_set1.text_input("Tag Number", "P-101A")
        limit_rms = c_set2.number_input("Limit Velocity RMS (mm/s)", value=4.50, step=0.1)

    # --- BAGIAN 2: FORM INPUT (SATU HALAMAN) ---
    # Kita buat 2 kolom besar: KIRI (Driver) dan KANAN (Driven)
    col_driver, col_driven = st.columns(2)

    # --- A. KOLOM DRIVER (MOTOR) ---
    with col_driver:
        st.subheader("⚡ DRIVER (Motor)")
        st.info("Input Data Motor")
        
        # Grid layout untuk input yang rapi: Label | Input DE | Input NDE
        # Baris 1: Horizontal
        st.markdown("**1. Horizontal (mm/s)**")
        c1, c2 = st.columns(2)
        m_h_de = c1.number_input("DE - Horiz", key="m_h_de", help="Motor DE Horizontal")
        m_h_nde = c2.number_input("NDE - Horiz", key="m_h_nde", help="Motor NDE Horizontal")
        
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

        # Baris 4: Temperature
        st.markdown("**4. Temperature (°C)**")
        c7, c8 = st.columns(2)
        m_t_de = c7.number_input("DE - Temp", key="m_t_de", step=1)
        m_t_nde = c8.number_input("NDE - Temp", key="m_t_nde", step=1)

    # --- B. KOLOM DRIVEN (POMPA) ---
    with col_driven:
        st.subheader("💧 DRIVEN (Pompa)")
        st.success("Input Data Pompa")

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

        # Baris 4: Temperature
        st.markdown("**4. Temperature (°C)**")
        p7, p8 = st.columns(2)
        p_t_de = p7.number_input("DE - Temp", key="p_t_de", step=1)
        p_t_nde = p8.number_input("NDE - Temp", key="p_t_nde", step=1)

    st.markdown("---")
    
    # --- C. HYDRAULIC & BUTTON ---
    col_h, col_btn = st.columns([1, 2])
    with col_h:
        st.markdown("##### 🚰 Hydraulic Pressure")
        suc = st.number_input("Suction (BarG)", value=0.5)
        dis = st.number_input("Discharge (BarG)", value=4.0)
    
    with col_btn:
        st.markdown("##### 🚀 Action")
        st.markdown("Klik tombol di bawah untuk memproses tabel laporan.")
        process_btn = st.button("GENERATE REPORT & ANALYSIS", type="primary", use_container_width=True)

    # --- 3. OUTPUT REPORT (HANYA MUNCUL JIKA TOMBOL DIKLIK) ---
    if process_btn:
        st.divider()
        st.header("📊 Laporan Hasil Inspeksi")
        st.write(f"**Equipment:** {eq_tag} | **Standard Limit:** {limit_rms} mm/s")

        # --- MEMBANGUN DATAFRAME (TABEL) ---
        # Helper function hitung rata-rata
        def calc_avg(v1, v2):
            return (v1 + v2) / 2

        # Data disusun list of dictionary
        data_rows = [
            # DRIVER ROWS
            {"Component": "Driver", "Param": "H", "DE": m_h_de, "NDE": m_h_nde, "Limit": limit_rms},
            {"Component": "Driver", "Param": "V", "DE": m_v_de, "NDE": m_v_nde, "Limit": limit_rms},
            {"Component": "Driver", "Param": "A", "DE": m_a_de, "NDE": m_a_nde, "Limit": limit_rms},
            {"Component": "Driver", "Param": "T (°C)", "DE": m_t_de, "NDE": m_t_nde, "Limit": None}, # Temp no limit logic yet
            # DRIVEN ROWS
            {"Component": "Driven", "Param": "H", "DE": p_h_de, "NDE": p_h_nde, "Limit": limit_rms},
            {"Component": "Driven", "Param": "V", "DE": p_v_de, "NDE": p_v_nde, "Limit": limit_rms},
            {"Component": "Driven", "Param": "A", "DE": p_a_de, "NDE": p_a_nde, "Limit": limit_rms},
            {"Component": "Driven", "Param": "T (°C)", "DE": p_t_de, "NDE": p_t_nde, "Limit": None},
        ]

        df = pd.DataFrame(data_rows)

        # Hitung Kolom Avr
        df["Avr"] = df.apply(lambda x: calc_avg(x["DE"], x["NDE"]), axis=1)

        # Hitung Kolom Remark
        def fill_remark(row):
            if row["Param"] == "T (°C)":
                return "-"
            return get_remark(row["Avr"], row["Limit"])

        df["Remark"] = df.apply(fill_remark, axis=1)

        # RAPIKAN TABEL (Reorder Columns sesuai gambar)
        # Format angka agar 2 desimal di tampilan
        st.dataframe(
            df[["Component", "Param", "DE", "NDE", "Avr", "Limit", "Remark"]].style.format({
                "DE": "{:.2f}", "NDE": "{:.2f}", "Avr": "{:.2f}", "Limit": "{:.2f}"
            }),
            use_container_width=True,
            hide_index=True,
            height=300 # Agar tabel terlihat penuh
        )

        # --- KESIMPULAN & ANALISA ---
        st.markdown("### 📝 Analisa & Rekomendasi")
        
        # 1. Analisa Vibrasi
        vibration_conclusion = analyze_conclusion(df)
        st.info(vibration_conclusion)

        # 2. Analisa Pressure
        diff_press = dis - suc
        if diff_press < 1.0:
            st.warning(f"⚠️ **Hydraulic Issue:** Differential Pressure rendah ({diff_press} Bar). Cek performa pompa.")
        else:
            st.success(f"✅ **Hydraulic:** Tekanan operasi normal (Diff: {diff_press} Bar).")
