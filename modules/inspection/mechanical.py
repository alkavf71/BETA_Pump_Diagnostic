import streamlit as st
import numpy as np

# --- 1. LOGIC & ALGORITHM FUNCTION (OTAKNYA) ---

def get_iso10816_zone(power_kw, velocity_rms, foundation_type='Rigid'):
    """
    Menentukan Zona ISO 10816-3 berdasarkan Power (kW) dan Velocity RMS.
    Asumsi: Group 1 (Large) > 300kW, Group 2 (Medium) 15-300kW.
    """
    # Batas limit berdasarkan ISO 10816-3 (Simplified for General Pump)
    # Zone boundaries: A/B, B/C, C/D
    
    if power_kw > 15: # Medium to Large Machines
        if foundation_type == 'Rigid':
            limits = [2.3, 4.5, 7.1] # mm/s RMS
        else: # Flexible
            limits = [3.5, 7.1, 11.0]
    else: # Small Machines (<15 kW) - Strictly Speaking ISO 10816 Class I
        limits = [0.71, 1.8, 4.5]

    if velocity_rms < limits[0]:
        return "Zone A (Good)", "🟢"
    elif velocity_rms < limits[1]:
        return "Zone B (Satisfactory)", "🟢"
    elif velocity_rms < limits[2]:
        return "Zone C (Unsatisfactory/Alert)", "🟡"
    else:
        return "Zone D (Unacceptable/Danger)", "🔴"

def analyze_spectrum(rpm, peaks):
    """
    Menganalisis 3 puncak frekuensi dominan untuk menentukan akar masalah.
    peaks = list of dict [{'freq': 25, 'amp': 4.2}, ...]
    """
    run_speed_hz = rpm / 60
    diagnosis = []
    
    # Toleransi pembacaan frekuensi (+- 10%)
    tolerance = 0.1 
    
    max_amp_peak = max(peaks, key=lambda x: x['amp'])
    
    for peak in peaks:
        f = peak['freq']
        a = peak['amp']
        
        # Skip jika amplitudo terlalu kecil (noise)
        if a < 1.0: 
            continue
            
        order = f / run_speed_hz
        
        # Logika Diagnosa
        if (1.0 - tolerance) <= order <= (1.0 + tolerance):
            if a == max_amp_peak['amp']: # Jika ini puncak tertinggi
                diagnosis.append(f"Dominan 1x RPM ({f} Hz). Indikasi kuat **UNBALANCE**.")
            else:
                diagnosis.append(f"Ada komponen 1x RPM ({f} Hz). Kemungkinan Unbalance atau Bent shaft.")
                
        elif (2.0 - tolerance) <= order <= (2.0 + tolerance):
            diagnosis.append(f"Tinggi di 2x RPM ({f} Hz). Indikasi kuat **MISALIGNMENT**.")
            
        elif order > 3.5 and not order.is_integer():
             diagnosis.append(f"Frekuensi tinggi non-sinkron ({f} Hz). Indikasi **BEARING** atau **GEAR MESH**.")
             
        elif order.is_integer() and order > 3:
             diagnosis.append(f"Banyak harmonik ({order:.1f}x). Indikasi **MECHANICAL LOOSENESS**.")

    if not diagnosis:
        return "Spektrum normal atau amplitudo rendah."
    
    return " | ".join(diagnosis)

# --- 2. MAIN UI FUNCTION ---

def render_mechanical_page():
    st.title("🔧 Mechanical Diagnostics (Pump & Motor)")
    st.markdown("---")

    # A. INPUT SPESIFIKASI (UNIVERSAL)
    st.subheader("1. Equipment Specification")
    col_spec1, col_spec2, col_spec3 = st.columns(3)
    
    with col_spec1:
        eq_name = st.text_input("Tag Number / Equipment Name", "P-101A")
    with col_spec2:
        power_kw = st.number_input("Motor Power (kW)", min_value=0.1, value=30.0)
    with col_spec3:
        rpm_input = st.number_input("Running Speed (RPM)", min_value=0, value=1480)
        foundation = st.selectbox("Foundation Type", ["Rigid (Semen/Angkur Kuat)", "Flexible (Isolator/Karet)"])

    st.markdown("---")

    # B. INPUT PENGUKURAN (LOOP UNTUK 4 TITIK UKUR)
    st.subheader("2. Vibration & Condition Data")
    
    # Kita buat Tabs agar tampilan bersih
    tab1, tab2, tab3, tab4 = st.tabs(["Motor DE", "Motor NDE", "Pump DE", "Pump NDE"])
    
    measure_points = {
        "Motor DE": tab1, "Motor NDE": tab2, 
        "Pump DE": tab3, "Pump NDE": tab4
    }
    
    # Dictionary untuk menyimpan data input
    data_input = {}

    for point_name, tab in measure_points.items():
        with tab:
            st.info(f"Input Data untuk **{point_name}**")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                vel_val = st.number_input(f"Velocity RMS (mm/s) - {point_name}", 0.0, 100.0, 0.0, key=f"v_{point_name}")
            with c2:
                acc_val = st.number_input(f"Acceleration RMS (g) - {point_name}", 0.0, 100.0, 0.0, key=f"a_{point_name}")
            with c3:
                disp_val = st.number_input(f"Displacement (μm) - {point_name}", 0.0, 1000.0, 0.0, key=f"d_{point_name}")

            st.markdown("**ADASH FASIT Check (Visual)**")
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            fasit_unbal = f_col1.selectbox(f"Unbalance", ["🟢 Aman", "🟡 Warning", "🔴 Bahaya"], key=f"fu_{point_name}")
            fasit_misal = f_col2.selectbox(f"Misalignment", ["🟢 Aman", "🟡 Warning", "🔴 Bahaya"], key=f"fm_{point_name}")
            fasit_loose = f_col3.selectbox(f"Looseness", ["🟢 Aman", "🟡 Warning", "🔴 Bahaya"], key=f"fl_{point_name}")
            fasit_bear  = f_col4.selectbox(f"Bearing", ["🟢 Aman", "🟡 Warning", "🔴 Bahaya"], key=f"fb_{point_name}")

            # Advanced Spectrum (Peak Picking)
            with st.expander("🔎 Advanced Spectrum Input (Peak Picking)"):
                p_peaks = []
                for i in range(1, 4):
                    pc1, pc2 = st.columns(2)
                    pf = pc1.number_input(f"Freq Puncak {i} (Hz)", 0.0, 5000.0, 0.0, key=f"pf_{i}_{point_name}")
                    pa = pc2.number_input(f"Amp Puncak {i} (mm/s)", 0.0, 100.0, 0.0, key=f"pa_{i}_{point_name}")
                    p_peaks.append({'freq': pf, 'amp': pa})

            # Simpan data ke dictionary
            data_input[point_name] = {
                'vel': vel_val, 'acc': acc_val, 'disp': disp_val,
                'fasit': {'Unbalance': fasit_unbal, 'Misalign': fasit_misal, 'Looseness': fasit_loose, 'Bearing': fasit_bear},
                'peaks': p_peaks
            }

    st.markdown("---")
    
    # C. INPUT PRESSURE (HYDRAULIC)
    st.subheader("3. Hydraulic Performance (Pressure)")
    hc1, hc2 = st.columns(2)
    suc_press = hc1.number_input("Suction Pressure (BarG)", value=0.5)
    dis_press = hc2.number_input("Discharge Pressure (BarG)", value=4.0)
    
    # --- 4. BUTTON ANALYZE ---
    if st.button("🚀 ANALYZE CONDITION", type="primary"):
        st.write("## 📊 HASIL ANALISA & REKOMENDASI")
        
        # 1. Analisa Pressure
        diff_press = dis_press - suc_press
        st.write(f"**Hydraulic Head (Est):** Differential Pressure = {diff_press:.2f} Bar")
        
        if suc_press < 0:
            st.warning("⚠️ **Low Suction Pressure (Vacuum):** Risiko KAVITASI tinggi. Pastikan NPSHa cukup.")
        elif diff_press < 1.0: # Ambang batas contoh
            st.error("⚠️ **Low Performance:** Pompa tidak menghasilkan head yang cukup. Cek impeller/wear ring.")
        else:
            st.success("✅ **Hydraulic:** Tekanan operasi tampak normal (perlu verifikasi dengan kurva pompa).")

        st.markdown("---")

        # 2. Analisa Vibrasi per Titik
        for point, data in data_input.items():
            # Skip jika data 0 (tidak diinput)
            if data['vel'] == 0 and data['acc'] == 0:
                continue

            with st.container():
                st.subheader(f"📍 Point: {point}")
                
                # A. ISO 10816 Status
                zone, icon = get_iso10816_zone(power_kw, data['vel'], foundation)
                st.markdown(f"**Status ISO 10816-3:** {icon} **{zone}** (Vel: {data['vel']} mm/s)")
                
                # B. Analisa Spektrum & FASIT Combined
                st.markdown("**Diagnosa Kerusakan:**")
                
                diagnosis_list = []
                
                # Cek FASIT dulu
                for k, v in data['fasit'].items():
                    if "🔴" in v:
                        diagnosis_list.append(f"🔴 **ADASH FASIT mendeteksi {k} Parah**.")
                    elif "🟡" in v:
                        diagnosis_list.append(f"🟡 **ADASH FASIT mendeteksi {k} Warning**.")
                
                # Cek Spektrum Manual
                spec_analysis = analyze_spectrum(rpm_input, data['peaks'])
                if "normal" not in spec_analysis:
                     diagnosis_list.append(f"📈 **Analisa Spektrum:** {spec_analysis}")

                # Cek Bearing via G-Value (Rule of Thumb General)
                if data['acc'] > 1.5: # Misal ambang batas 1.5g
                    diagnosis_list.append(f"⚠️ **High Acceleration ({data['acc']} g):** Indikasi kerusakan Bearing atau kurang lubrikasi.")

                # TAMPILKAN DIAGNOSA
                if not diagnosis_list:
                    if "A" in zone or "B" in zone:
                        st.success("Mesin beroperasi dalam batas normal. Pertahankan kondisi.")
                    else:
                        st.info("Vibrasi agak tinggi namun pola spektrum/FASIT belum menunjukkan kerusakan spesifik. Cek kekencangan baut (Looseness) umum.")
                else:
                    for d in diagnosis_list:
                        st.write(f"- {d}")
                        
                    # REKOMENDASI OTOMATIS BERDASARKAN KEYWORD
                    st.markdown("**🔧 Rekomendasi Tindakan:**")
                    full_text = " ".join(diagnosis_list).lower()
                    
                    if "unbalance" in full_text:
                        st.write("1. Lakukan pembersihan (cleaning) pada impeller/fan.")
                        st.write("2. Jika berlanjut, jadwalkan in-situ balancing.")
                    if "misalignment" in full_text:
                        st.write("1. Cek kondisi kopling (coupling wear).")
                        st.write("2. Lakukan laser alignment ulang saat mesin dingin.")
                    if "bearing" in full_text or "lubrikasi" in full_text:
                        st.write("1. Lakukan Greasing (regreasing) segera.")
                        st.write("2. Monitor suara bearing. Jika bising, rencanakan penggantian bearing.")
                    if "looseness" in full_text:
                        st.write("1. Kencangkan baut pondasi dan baut mounting motor/pompa.")
                    if "kavitasi" in full_text:
                        st.write("1. Cek strainer suction (mungkin buntu).")
                        st.write("2. Cek level tangki supply.")

                st.divider()
