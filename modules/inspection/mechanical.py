import pandas as pd

class MechanicalInspector:
    
    def __init__(self, vib_limit_warn=4.5, temp_limit_warn=85.0):
        self.vib_limit_warn = vib_limit_warn
        self.vib_limit_trip = 7.10
        self.temp_limit_warn = temp_limit_warn
        self.vib_limit_zone_a = 2.30 

        # DATABASE KNOWLEDGE BASE (Tetap Sama)
        self.knowledge_base = {
            "MISALIGNMENT": {
                "name": "MISALIGNMENT",
                "desc": "Indikasi ketidaklurusan poros (Angular/Offset).",
                "action": "🔧 Lakukan Laser Alignment (Tol. <0.05mm). Cek kondisi Coupling.",
                "std": "API 686 Ch. 4"
            },
            "UNBALANCE": {
                "name": "UNBALANCE",
                "desc": "Distribusi massa rotor/impeller tidak seimbang.",
                "action": "⚖️ Lakukan Balancing (Grade G2.5). Cek kotoran di fan/impeller.",
                "std": "ISO 21940-11"
            },
            "LOOSENESS": {
                "name": "LOOSENESS",
                "desc": "Kekenduran struktural / Soft Foot.",
                "action": "🔩 Cek Soft Foot. Kencangkan Baut Pondasi. Cek Grouting.",
                "std": "API 686 Ch. 5"
            },
            "BENT_SHAFT": {
                "name": "BENT SHAFT",
                "desc": "Indikasi poros bengkok (Physical damage).",
                "action": "📏 Ukur Run-out poros (Max 0.05mm).",
                "std": "API 610"
            },
            "CAVITATION": {
                "name": "CAVITATION / FLOW",
                "desc": "Masalah Flow atau Kavitasi (Hisapan).",
                "action": "🌊 Cek NPSH Available. Bersihkan Strainer. Cek Valve Suction.",
                "std": "API 610"
            },
             "BEARING_FAIL": {
                "name": "BEARING DEFECT",
                "desc": "Kerusakan elemen rolling bearing.",
                "action": "🔄 Ganti Bearing segera.",
                "std": "ISO 13373"
            },
             "OVERHEAT": {
                "name": "OVERHEAT",
                "desc": "Suhu Operasi Tinggi.",
                "action": "🌡️ Cek Cooling Fan & Sirip Motor.",
                "std": "NEMA MG-1"
            }
        }

    def _determine_zone(self, value):
        if value < self.vib_limit_zone_a: return "ZONE A (New)"
        elif value < self.vib_limit_warn: return "ZONE B (Good)"
        elif value < self.vib_limit_trip: return "ZONE C (Warning)"
        else: return "ZONE D (Damage)"

    def _avg(self, v1, v2): return (v1 + v2) / 2

    def analyze_vibration(self, inputs):
        # 1. Hitung Rata-rata
        m_h = self._avg(inputs['m_de_h'], inputs['m_nde_h'])
        m_v = self._avg(inputs['m_de_v'], inputs['m_nde_v'])
        m_a = self._avg(inputs['m_de_a'], inputs['m_nde_a'])
        
        p_h = self._avg(inputs['p_de_h'], inputs['p_nde_h'])
        p_v = self._avg(inputs['p_de_v'], inputs['p_nde_v'])
        p_a = self._avg(inputs['p_de_a'], inputs['p_nde_a'])

        # 2. DataFrame Report
        data = [
            ["Driver", "H", inputs['m_de_h'], inputs['m_nde_h'], m_h, self.vib_limit_warn, self._determine_zone(m_h)],
            ["Driver", "V", inputs['m_de_v'], inputs['m_nde_v'], m_v, self.vib_limit_warn, self._determine_zone(m_v)],
            ["Driver", "A", inputs['m_de_a'], inputs['m_nde_a'], m_a, self.vib_limit_warn, self._determine_zone(m_a)],
            ["Driven", "H", inputs['p_de_h'], inputs['p_nde_h'], p_h, self.vib_limit_warn, self._determine_zone(p_h)],
            ["Driven", "V", inputs['p_de_v'], inputs['p_nde_v'], p_v, self.vib_limit_warn, self._determine_zone(p_v)],
            ["Driven", "A", inputs['p_de_a'], inputs['p_nde_a'], p_a, self.vib_limit_warn, self._determine_zone(p_a)],
        ]
        df = pd.DataFrame(data, columns=["Unit", "Axis", "DE", "NDE", "Avr", "Limit", "Remark"])

        # 3. RULE-BASED DIAGNOSTIC ENGINE (UPDATED WITH TRIGGER REMARK)
        detected_faults = []
        max_m = max(m_h, m_v, m_a)
        max_p = max(p_h, p_v, p_a)
        global_max = max(max_m, max_p)

        if global_max >= self.vib_limit_warn:
            
            # --- MISALIGNMENT (Axial Dominan) ---
            if (m_a > 0.5 * max(m_h, m_v)) and (m_a > self.vib_limit_warn):
                fault = self.knowledge_base["MISALIGNMENT"].copy()
                fault['trigger'] = f"Vibrasi Axial Driver ({m_a:.2f} mm/s) sangat dominan."
                detected_faults.append(fault)
                
            elif (p_a > 0.5 * max(p_h, p_v)) and (p_a > self.vib_limit_warn):
                fault = self.knowledge_base["MISALIGNMENT"].copy()
                fault['trigger'] = f"Vibrasi Axial Driven ({p_a:.2f} mm/s) sangat dominan."
                detected_faults.append(fault)

            # --- UNBALANCE (Radial Horizontal Dominan) ---
            if (m_h > self.vib_limit_warn) and (m_h > m_v) and (m_h > m_a):
                fault = self.knowledge_base["UNBALANCE"].copy()
                fault['trigger'] = f"Vibrasi Horizontal Driver ({m_h:.2f} mm/s) tertinggi (Pola Radial)."
                detected_faults.append(fault)
            
            elif (p_h > self.vib_limit_warn) and (p_h > p_v) and (p_h > p_a):
                fault = self.knowledge_base["UNBALANCE"].copy()
                fault['trigger'] = f"Vibrasi Horizontal Driven ({p_h:.2f} mm/s) tertinggi (Pola Radial)."
                detected_faults.append(fault)

            # --- LOOSENESS (Vertical Dominan/Tinggi) ---
            if (m_v > 0.8 * m_h) and (m_v > self.vib_limit_warn):
                fault = self.knowledge_base["LOOSENESS"].copy()
                fault['trigger'] = f"Vibrasi Vertikal Driver ({m_v:.2f} mm/s) tidak wajar (Mendekati Horizontal)."
                detected_faults.append(fault)
            
            elif (p_v > 0.8 * p_h) and (p_v > self.vib_limit_warn):
                fault = self.knowledge_base["LOOSENESS"].copy()
                fault['trigger'] = f"Vibrasi Vertikal Driven ({p_v:.2f} mm/s) tidak wajar (Mendekati Horizontal)."
                detected_faults.append(fault)

            # --- BENT SHAFT (Axial Keduanya Tinggi) ---
            if (m_a > self.vib_limit_warn) and (p_a > self.vib_limit_warn):
                fault = self.knowledge_base["BENT_SHAFT"].copy()
                fault['trigger'] = f"Axial Driver ({m_a:.2f}) & Driven ({p_a:.2f}) sama-sama tinggi."
                detected_faults.append(fault)

            # --- CAVITATION (Driven Tinggi Semua Arah) ---
            if (p_h > self.vib_limit_warn) and (p_v > self.vib_limit_warn) and (p_a > self.vib_limit_warn):
                 if max_m < self.vib_limit_warn: # Driver Halus
                    fault = self.knowledge_base["CAVITATION"].copy()
                    fault['trigger'] = f"Vibrasi Pompa tinggi segala arah (Max: {max_p:.2f} mm/s), tapi Motor halus."
                    detected_faults.append(fault)

        return df, detected_faults, global_max

    def analyze_full_health(self, vib_inputs, temp_inputs, noise_obs=None):
        # 1. Analisa Vibrasi
        df, faults, max_vib = self.analyze_vibration(vib_inputs)
        
        # 2. Analisa Suhu
        temp_max = max(temp_inputs.values())
        if temp_max > self.temp_limit_warn:
            fault = self.knowledge_base["OVERHEAT"].copy()
            # Cari bearing mana yang paling panas
            hottest_point = max(temp_inputs, key=temp_inputs.get)
            fault['trigger'] = f"Suhu {hottest_point} mencapai {temp_max}°C (Limit {self.temp_limit_warn}°C)."
            
            # Cek duplikasi
            if not any(f['name'] == "OVERHEAT" for f in faults):
                faults.append(fault)
            
        # 3. Analisa Noise
        if noise_obs == "Kavitasi / Kerikil":
             if not any(f['name'] == "CAVITATION / FLOW" for f in faults):
                 fault = self.knowledge_base["CAVITATION"].copy()
                 fault['trigger'] = "Terdeteksi suara fisik 'Kerikil' (Kavitasi) saat inspeksi."
                 faults.append(fault)
                 
        elif noise_obs == "Bearing Defect / Gemuruh":
             if not any(f['name'] == "BEARING DEFECT" for f in faults):
                 fault = self.knowledge_base["BEARING_FAIL"].copy()
                 fault['trigger'] = "Terdeteksi suara fisik 'Gemuruh/Decit' (Bearing) saat inspeksi."
                 faults.append(fault)

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
