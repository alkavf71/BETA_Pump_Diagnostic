import pandas as pd

class MechanicalInspector:
    """
    MODULE INSPEKSI MEKANIKAL (Logic Layer) - REVISI MULTI-FAULT
    """
    
    def __init__(self, vib_limit_warn=4.5, temp_limit_warn=85.0):
        self.vib_limit_warn = vib_limit_warn
        self.vib_limit_trip = 7.10
        self.temp_limit_warn = temp_limit_warn
        self.vib_limit_zone_a = 2.30 

        # DATABASE DIAGNOSA (Knowledge Base)
        self.knowledge_base = {
            "MISALIGNMENT": {
                "name": "MISALIGNMENT",
                "desc": "Indikasi ketidaklurusan poros (Angular/Offset).",
                "action": "🔧 Lakukan Laser Alignment. Cek Shimming & Coupling.",
                "std": "API 686 Ch. 4"
            },
            "UNBALANCE": {
                "name": "UNBALANCE",
                "desc": "Distribusi massa rotor/impeller tidak seimbang.",
                "action": "⚖️ Lakukan Balancing (Grade G2.5). Cek kotoran menumpuk.",
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
            },
            "GENERAL_HIGH": {
                "name": "GENERAL HIGH VIBRATION",
                "desc": "Vibrasi tinggi terdeteksi namun pola tidak spesifik.",
                "action": "🔍 Lakukan pengecekan menyeluruh (Spektrum Analisis disarankan).",
                "std": "ISO 10816-3"
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

        # 3. RULE-BASED DIAGNOSTIC ENGINE (INDEPENDENT CHECKS)
        detected_faults = []
        
        # --- CEK DRIVER (MOTOR) SECARA MANDIRI ---
        
        # A. Misalignment Driver (Axial Dominan)
        if m_a > self.vib_limit_warn:
            if m_a > 0.5 * max(m_h, m_v):
                fault = self.knowledge_base["MISALIGNMENT"].copy()
                fault['trigger'] = f"[DRIVER] Vibrasi Axial ({m_a:.2f}) dominan thd Radial."
                detected_faults.append(fault)

        # B. Unbalance Driver (Horizontal Dominan)
        if m_h > self.vib_limit_warn:
            if (m_h > m_v) and (m_h > m_a):
                fault = self.knowledge_base["UNBALANCE"].copy()
                fault['trigger'] = f"[DRIVER] Vibrasi Horizontal ({m_h:.2f}) tertinggi (Pola Radial)."
                detected_faults.append(fault)

        # C. Looseness Driver (Vertical Tinggi)
        if m_v > self.vib_limit_warn:
            if m_v > 0.8 * m_h: # Vertikal mendekati atau melebihi Horizontal
                fault = self.knowledge_base["LOOSENESS"].copy()
                fault['trigger'] = f"[DRIVER] Vibrasi Vertikal ({m_v:.2f}) tinggi (Indikasi Soft Foot/Longgar)."
                detected_faults.append(fault)

        # --- CEK DRIVEN (POMPA) SECARA MANDIRI ---

        # D. Misalignment Driven
        if p_a > self.vib_limit_warn:
            if p_a > 0.5 * max(p_h, p_v):
                fault = self.knowledge_base["MISALIGNMENT"].copy()
                fault['trigger'] = f"[DRIVEN] Vibrasi Axial ({p_a:.2f}) dominan thd Radial."
                detected_faults.append(fault)

        # E. Unbalance Driven
        if p_h > self.vib_limit_warn:
            if (p_h > p_v) and (p_h > p_a):
                fault = self.knowledge_base["UNBALANCE"].copy()
                fault['trigger'] = f"[DRIVEN] Vibrasi Horizontal ({p_h:.2f}) tertinggi."
                detected_faults.append(fault)

        # F. Looseness Driven
        if p_v > self.vib_limit_warn:
            if p_v > 0.8 * p_h:
                fault = self.knowledge_base["LOOSENESS"].copy()
                fault['trigger'] = f"[DRIVEN] Vibrasi Vertikal ({p_v:.2f}) tinggi."
                detected_faults.append(fault)

        # --- CEK KOMBINASI (SYSTEM WIDE) ---

        # G. Bent Shaft (Axial Kanan-Kiri Tinggi)
        if (m_a > self.vib_limit_trip) and (p_a > self.vib_limit_trip):
            fault = self.knowledge_base["BENT_SHAFT"].copy()
            fault['trigger'] = "Vibrasi Axial Driver & Driven sama-sama KRITIS."
            detected_faults.append(fault)

        # H. Cavitation (Pompa Goyang Semua Arah)
        if (p_h > self.vib_limit_warn) and (p_v > self.vib_limit_warn) and (p_a > self.vib_limit_warn):
            # Cek duplikasi, jangan tambahkan jika sudah didiagnosa Unbalance/Misalignment di Pompa
            # Tapi Kavitasi biasanya acak, jadi kita tambahkan saja sebagai kemungkinan.
            fault = self.knowledge_base["CAVITATION"].copy()
            fault['trigger'] = "Vibrasi Pompa tinggi di SEMUA arah (Horizontal/Vertical/Axial)."
            detected_faults.append(fault)
            
        # I. General High Vibration (Fallback)
        # Jika ada vibrasi tinggi TAPI tidak masuk kategori di atas
        max_all = max(m_h, m_v, m_a, p_h, p_v, p_a)
        if max_all > self.vib_limit_warn and len(detected_faults) == 0:
            fault = self.knowledge_base["GENERAL_HIGH"].copy()
            fault['trigger'] = f"Vibrasi Max ({max_all:.2f}) melebihi limit, pola tidak spesifik."
            detected_faults.append(fault)

        return df, detected_faults, max_all

    def analyze_full_health(self, vib_inputs, temp_inputs, noise_obs=None):
        # 1. Analisa Vibrasi
        df, faults, max_vib = self.analyze_vibration(vib_inputs)
        
        # 2. Analisa Suhu
        temp_max = max(temp_inputs.values())
        if temp_max > self.temp_limit_warn:
            fault = self.knowledge_base["OVERHEAT"].copy()
            hottest_point = max(temp_inputs, key=temp_inputs.get)
            fault['trigger'] = f"Suhu {hottest_point} mencapai {temp_max}°C."
            faults.append(fault)
            
        # 3. Analisa Noise
        if noise_obs == "Kavitasi / Kerikil":
             # Cek agar tidak duplikat dgn diagnosa vibrasi
             if not any(f['name'] == "CAVITATION / FLOW" for f in faults):
                 fault = self.knowledge_base["CAVITATION"].copy()
                 fault['trigger'] = "Terdeteksi suara fisik 'Kerikil' (Kavitasi)."
                 faults.append(fault)
        elif noise_obs == "Bearing Defect / Gemuruh":
             fault = self.knowledge_base["BEARING_FAIL"].copy()
             fault['trigger'] = "Terdeteksi suara fisik 'Gemuruh' (Bearing Defect)."
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
