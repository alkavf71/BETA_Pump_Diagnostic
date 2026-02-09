import pandas as pd

class MechanicalInspector:
    """
    MODULE INSPEKSI MEKANIKAL (Logic Layer)
    
    Standards:
    - ISO 20816-3 (Zone Limits)
    - ISO 13373 (Diagnostic Patterns)
    - API 610 / ISO 13709 (Pump specific issues)
    - API 686 (Alignment & Mounting)
    """
    
    def __init__(self, vib_limit_warn=4.5, temp_limit_warn=85.0):
        self.vib_limit_warn = vib_limit_warn
        self.vib_limit_trip = 7.10
        self.temp_limit_warn = temp_limit_warn
        self.vib_limit_zone_a = 2.30 

        # --- DATABASE DIAGNOSA & REKOMENDASI ---
        self.knowledge_base = {
            "MISALIGNMENT": {
                "desc": "Indikasi ketidaklurusan poros (Angular/Offset).",
                "action": "🔧 Lakukan Laser Alignment (Tol. <0.05mm). Cek kondisi Coupling & Shimming.",
                "std": "API 686 Ch. 4"
            },
            "UNBALANCE": {
                "desc": "Distribusi massa rotor/impeller tidak seimbang.",
                "action": "⚖️ Lakukan Balancing (Grade G2.5/G6.3). Cek kotoran menumpuk di fan/impeller.",
                "std": "ISO 21940-11"
            },
            "LOOSENESS": {
                "desc": "Kekenduran struktural pada kaki motor/pompa atau baut pondasi.",
                "action": "🔩 Cek Soft Foot. Kencangkan Baut Pondasi & Baseplate. Cek keretakan Grouting.",
                "std": "API 686 Ch. 5"
            },
            "BENT_SHAFT": {
                "desc": "Indikasi poros bengkok (Physical damage).",
                "action": "📏 Ukur Run-out poros (Max 0.05mm). Ganti poros jika melebihi toleransi.",
                "std": "API 610 / ISO 13373"
            },
            "BEARING_FAIL": {
                "desc": "Kerusakan elemen rolling bearing (Aus/Cacat).",
                "action": "🔄 Ganti Bearing segera. Cek kualitas pelumas (Grease/Oil).",
                "std": "OEM Manual / ISO 13373"
            },
            "CAVITATION": {
                "desc": "Kavitasi (Masalah sisi hisap/suction).",
                "action": "🌊 Cek NPSH Available. Bersihkan Suction Strainer. Cek Level Tangki.",
                "std": "API 610 / ISO 13709"
            },
            "OVERHEAT": {
                "desc": "Suhu operasional melebihi batas aman.",
                "action": "🌡️ Cek sistem pendingin (Fan/Sirip). Lakukan Regreasing. Cek Overload.",
                "std": "API 610 / NEMA MG-1"
            }
        }

    def _determine_zone(self, value):
        if value < self.vib_limit_zone_a: return "ZONE A (New)"
        elif value < self.vib_limit_warn: return "ZONE B (Good)"
        elif value < self.vib_limit_trip: return "ZONE C (Warning)"
        else: return "ZONE D (Damage)"

    def _avg(self, v1, v2):
        return (v1 + v2) / 2

    def analyze_vibration(self, inputs):
        """
        Menganalisa vibrasi berdasarkan Logic Heuristic ISO 13373.
        Membedakan diagnosa untuk DRIVER (Motor) dan DRIVEN (Pompa).
        """
        # 1. Hitung Rata-rata
        m_h = self._avg(inputs['m_de_h'], inputs['m_nde_h'])
        m_v = self._avg(inputs['m_de_v'], inputs['m_nde_v'])
        m_a = self._avg(inputs['m_de_a'], inputs['m_nde_a'])
        
        p_h = self._avg(inputs['p_de_h'], inputs['p_nde_h'])
        p_v = self._avg(inputs['p_de_v'], inputs['p_nde_v'])
        p_a = self._avg(inputs['p_de_a'], inputs['p_nde_a'])

        # 2. Buat DataFrame Report
        data = [
            ["Driver", "H", inputs['m_de_h'], inputs['m_nde_h'], m_h, self.vib_limit_warn, self._determine_zone(m_h)],
            ["Driver", "V", inputs['m_de_v'], inputs['m_nde_v'], m_v, self.vib_limit_warn, self._determine_zone(m_v)],
            ["Driver", "A", inputs['m_de_a'], inputs['m_nde_a'], m_a, self.vib_limit_warn, self._determine_zone(m_a)],
            ["Driven", "H", inputs['p_de_h'], inputs['p_nde_h'], p_h, self.vib_limit_warn, self._determine_zone(p_h)],
            ["Driven", "V", inputs['p_de_v'], inputs['p_nde_v'], p_v, self.vib_limit_warn, self._determine_zone(p_v)],
            ["Driven", "A", inputs['p_de_a'], inputs['p_nde_a'], p_a, self.vib_limit_warn, self._determine_zone(p_a)],
        ]
        df = pd.DataFrame(data, columns=["Unit", "Axis", "DE", "NDE", "Avr", "Limit", "Remark"])

        # 3. RULE-BASED DIAGNOSTIC ENGINE
        detected_faults = []
        
        max_m = max(m_h, m_v, m_a)
        max_p = max(p_h, p_v, p_a)
        global_max = max(max_m, max_p)

        # Hanya diagnosa jika vibrasi di atas Warning (Zone C/D)
        if global_max >= self.vib_limit_warn:
            
            # --- RULE 1: MISALIGNMENT (High Axial) ---
            # Jika Axial dominan (> 50% dari Max Radial)
            if (m_a > 0.5 * max(m_h, m_v)) or (p_a > 0.5 * max(p_h, p_v)):
                if m_a > self.vib_limit_warn or p_a > self.vib_limit_warn:
                    detected_faults.append(self.knowledge_base["MISALIGNMENT"])

            # --- RULE 2: UNBALANCE (High Radial Horizontal) ---
            # Biasanya Horizontal tinggi, Vertikal rendah, Axial rendah
            if (m_h > self.vib_limit_warn and m_h > m_v) or (p_h > self.vib_limit_warn and p_h > p_v):
                # Pastikan bukan misalignment (axial harus rendah)
                if max(m_a, p_a) < self.vib_limit_warn:
                    detected_faults.append(self.knowledge_base["UNBALANCE"])

            # --- RULE 3: LOOSENESS / SOFT FOOT (High Vertical) ---
            # Pada mesin horizontal, Vertikal harusnya lebih rendah dari Horizontal.
            # Jika V mendekati atau melebihi H, itu tanda longgar.
            if (m_v > 0.8 * m_h and m_v > self.vib_limit_warn) or (p_v > 0.8 * p_h and p_v > self.vib_limit_warn):
                detected_faults.append(self.knowledge_base["LOOSENESS"])

            # --- RULE 4: BENT SHAFT ---
            # Axial tinggi di kedua sisi (Driver & Driven)
            if m_a > self.vib_limit_trip and p_a > self.vib_limit_trip:
                detected_faults.append(self.knowledge_base["BENT_SHAFT"])

            # --- RULE 5: CAVITATION (Specific to Pump) ---
            if p_h > self.vib_limit_warn and p_v > self.vib_limit_warn and p_a > self.vib_limit_warn:
                # Jika motor halus tapi pompa kasar semua arah -> Indikasi Flow/Cavitation
                if max_m < self.vib_limit_warn:
                    detected_faults.append(self.knowledge_base["CAVITATION"])

        return df, detected_faults, global_max

    def analyze_full_health(self, vib_inputs, temp_inputs, noise_obs=None):
        """
        Fungsi Integrasi Utama: Vibrasi + Suhu + Noise
        """
        # 1. Analisa Vibrasi
        df, faults, max_vib = self.analyze_vibration(vib_inputs)
        
        # 2. Analisa Suhu
        temp_max = max(temp_inputs.values())
        if temp_max > self.temp_limit_warn:
            # Cegah duplikasi jika sudah ada overheat
            if self.knowledge_base["OVERHEAT"] not in faults:
                faults.append(self.knowledge_base["OVERHEAT"])
            
        # 3. Analisa Noise (Manual Input)
        if noise_obs == "Kavitasi / Kerikil":
             if self.knowledge_base["CAVITATION"] not in faults:
                 faults.append(self.knowledge_base["CAVITATION"])
        elif noise_obs == "Bearing Defect / Gemuruh":
             if self.knowledge_base["BEARING_FAIL"] not in faults:
                 faults.append(self.knowledge_base["BEARING_FAIL"])

        # 4. Tentukan Status Final
        status = "NORMAL"
        if any("ZONE C" in x for x in df['Remark'].values): status = "WARNING"
        if temp_max > self.temp_limit_warn: status = "WARNING"
        
        if any("ZONE D" in x for x in df['Remark'].values): status = "CRITICAL"
        if temp_max > 95.0: status = "CRITICAL"

        return {
            "dataframe": df,
            "faults": faults,
            "max_vib": max_vib,
            "max_temp": temp_max,
            "status": status
        }
