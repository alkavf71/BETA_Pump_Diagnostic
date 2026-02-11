def assess_overall_health(vib_status, elec_status, max_temp, phys_issues, diagnoses):
    """
    Fungsi Logic Gabungan (Holistic Health Assessment)
    Menggabungkan hasil Mekanikal, Elektrikal, dan Fisik.
    """
    
    # 1. INIT DEFAULT (Asumsi Sehat)
    final_status = "GOOD CONDITION"
    color = "#28a745" # Green
    desc = "Aset beroperasi dalam batas normal."
    action = "Lanjutkan operasional & monitoring rutin."
    reasons = []
    recommendations = []
    standards = []

    # 2. FILTER INPUTS
    # Normalisasi status vibrasi
    is_vib_danger = "ZONE D" in vib_status
    is_vib_warn = "ZONE C" in vib_status
    
    # Normalisasi status elektrikal
    is_elec_danger = "CRITICAL" in elec_status or "TRIP" in elec_status
    is_elec_warn = "WARNING" in elec_status

    # 3. LOGIC PENENTUAN STATUS (HIERARKI)
    
    # --- LEVEL 1: DANGER / CRITICAL (Prioritas Tertinggi) ---
    if is_vib_danger or is_elec_danger or max_temp > 90 or "MAJOR" in str(phys_issues):
        final_status = "CRITICAL / DANGER"
        color = "#dc3545" # Red
        desc = "Terdeteksi kegagalan fungsi yang membahayakan aset/keselamatan."
        action = "⛔ STOP OPERASI & LAKUKAN PERBAIKAN SEGERA."
        
        # Cari Penyebab Utama (Root Cause)
        if is_vib_danger: reasons.append("Vibrasi Sangat Tinggi (ISO Zone D).")
        if is_elec_danger: reasons.append("Parameter Listrik Trip/Overload.")
        if max_temp > 90: reasons.append(f"Overheat Ekstrem ({max_temp}°C).")
        for issue in phys_issues:
            if "MAJOR" in issue: reasons.append(f"Isu Fisik: {issue}")

    # --- LEVEL 2: WARNING / ALERT ---
    elif is_vib_warn or is_elec_warn or max_temp > 75 or phys_issues:
        final_status = "WARNING / ALERT"
        color = "#ffc107" # Yellow
        desc = "Aset beroperasi dengan penyimpangan. Risiko kerusakan jangka panjang."
        action = "⚠️ Jadwalkan maintenance dalam waktu dekat (Planned Maintenance)."
        
        if is_vib_warn: reasons.append("Vibrasi Meningkat (ISO Zone C).")
        if is_elec_warn: reasons.append("Ketidakseimbangan Listrik/Voltage.")
        if max_temp > 75: reasons.append(f"Suhu Agak Tinggi ({max_temp}°C).")
        for issue in phys_issues:
            reasons.append(f"Temuan Fisik: {issue}")
            
    # --- LEVEL 3: GOOD (Sisanya) ---
    else:
        reasons.append("Semua parameter dalam batas toleransi.")

    # 4. GENERATE REKOMENDASI SPESIFIK (Berdasarkan Diagnosa)
    # Mapping Diagnosa -> Solusi
    
    # Gabungkan semua diagnosa string untuk pencarian kata kunci
    diag_str = " ".join(diagnoses).upper()
    
    if "MISALIGNMENT" in diag_str:
        recommendations.append("Lakukan Laser Alignment pada kopling.")
        standards.append("ISO 10816-3")
        
    if "UNBALANCE" in diag_str:
        recommendations.append("Cek kebersihan impeller/fan. Lakukan Balancing.")
        standards.append("ISO 1940-1")
        
    if "LOOSE" in diag_str or "SOFT FOOT" in diag_str:
        recommendations.append("Cek kekencangan baut pondasi (Soft Foot Check).")
    
    if "BEARING" in diag_str:
        recommendations.append("Ganti Bearing. Cek kualitas pelumasan.")
    
    if "KAVITASI" in diag_str:
        recommendations.append("Cek saringan hisap (Strainer). Pastikan NPSHa > NPSHr.")
        standards.append("API 610")
        
    if "VOLTAGE" in diag_str or "UNBALANCE" in diag_str:
        recommendations.append("Cek koneksi terminal box & tegangan supply trafo.")
        standards.append("IEC 60034")

    if "OVERLOAD" in diag_str:
        recommendations.append("Kurangi beban pompa (throttling) atau cek sumbatan.")

    if not recommendations:
        if final_status == "GOOD CONDITION":
            recommendations.append("Pertahankan parameter operasi.")
        else:
            recommendations.append("Lakukan inspeksi visual mendalam.")

    # 5. RETURN DICTIONARY (Harus cocok dengan main.py)
    return {
        "status": final_status,
        "color": color,
        "desc": desc,
        "action": action,
        "reasons": reasons,                  # List Root Cause
        "recommendations": recommendations,  # List Solusi
        "standards": list(set(standards))    # List Standar (Unik)
    }
