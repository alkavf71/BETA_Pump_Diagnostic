import pandas as pd

class MechanicalInspector:
    """
    Module Inspeksi Mekanikal Standar:
    1. ISO 20816-3 (Vibrasi Mesin - Zone Classification)
    2. API 610 / ISO 13709 (Limit Suhu Bearing & Vibrasi Pompa)
    """
    
    def __init__(self, vib_limit_warn=4.5, temp_limit_warn=85.0):
        # Default ISO 20816 Class II (Medium Machine) -> 4.5 mm/s limit B/C
        self.vib_limit_warn = vib_limit_warn 
        self.vib_limit_trip = 7.10
        self.temp_limit_warn = temp_limit_warn # API 610 Bearing Temp Alarm
        
        # Penentuan Batas Zone A (New Machine)
        # Biasanya 50-60% dari batas Warning
        self.vib_limit_zone_a = 2.30 

    def _determine_zone(self, value):
        """Internal Helper: Tentukan Zone ISO 20816"""
        if value < self.vib_limit_zone_a:
            return "ZONE A (New Condition)"
        elif value < self.vib_limit_warn:
            return "ZONE B (Unlimited Ops)"
        elif value < self.vib_limit_trip:
            return "ZONE C (Restricted Ops)"
        else:
            return "ZONE D (Damage Risk)"

    def analyze_vibration(self, inputs):
        """
        Input: Dictionary data vibrasi (12 titik)
        Output: DataFrame Laporan & List Diagnosa
        """
        # 1. Hitung Rata-rata (Average) per Axis
        def avg(v1, v2): return (v1 + v2) / 2
        
        avr_m_h = avg(inputs['m_de_h'], inputs['m_nde_h'])
        avr_m_v = avg(inputs['m_de_v'], inputs['m_nde_v'])
        avr_m_a = avg(inputs['m_de_a'], inputs['m_nde_a'])
        
        avr_p_h = avg(inputs['p_de_h'], inputs['p_nde_h'])
        avr_p_v = avg(inputs['p_de_v'], inputs['p_nde_v'])
        avr_p_a = avg(inputs['p_de_a'], inputs['p_nde_a'])

        # 2. Susun Data Report (Format Tabel Laporan Perusahaan)
        data = [
            ["Driver", "H", inputs['m_de_h'], inputs['m_nde_h'], avr_m_h, self.vib_limit_warn, self._determine_zone(avr_m_h)],
            ["Driver", "V", inputs['m_de_v'], inputs['m_nde_v'], avr_m_v, self.vib_limit_warn, self._determine_zone(avr_m_v)],
            ["Driver", "A", inputs['m_de_a'], inputs['m_nde_a'], avr_m_a, self.vib_limit_warn, self._determine_zone(avr_m_a)],
            ["Driven", "H", inputs['p_de_h'], inputs['p_nde_h'], avr_p_h, self.vib_limit_warn, self._determine_zone(avr_p_h)],
            ["Driven", "V", inputs['p_de_v'], inputs['p_nde_v'], avr_p_v, self.vib_limit_warn, self._determine_zone(avr_p_v)],
            ["Driven", "A", inputs['p_de_a'], inputs['p_nde_a'], avr_p_a, self.vib_limit_warn, self._determine_zone(avr_p_a)],
        ]
        
        df = pd.DataFrame(data, columns=["Unit", "Axis", "DE", "NDE", "Avr", "Limit", "Remark"])
        
        # 3. Diagnosa Cerdas (Heuristic Logic ISO 13373)
        diagnoses = []
        max_val = max(avr_m_h, avr_m_v, avr_m_a, avr_p_h, avr_p_v, avr_p_a)
        
        if max_val >= self.vib_limit_warn:
            # Misalignment Logic
            if (avr_m_a > self.vib_limit_warn) or (avr_p_a > self.vib_limit_warn):
                diagnoses.append("MISALIGNMENT (Vibrasi Axial Dominan)")
            # Unbalance Logic
            if (avr_m_h > self.vib_limit_warn) and (avr_m_h > avr_m_v):
                diagnoses.append("UNBALANCE (Vibrasi Radial Horizontal Dominan)")
            # Looseness Logic
            if (avr_m_v > self.vib_limit_warn) and (avr_m_v > avr_m_h):
                diagnoses.append("MECHANICAL LOOSENESS (Vibrasi Vertikal Dominan)")

        return df, diagnoses, max_val

    def analyze_temperature(self, temps):
        """
        Input: Dictionary {'m_de': 40, 'm_nde': 45, ...}
        Standard: API 610 / Bearing Manufacturer Limits
        """
        issues = []
        max_temp = 0
        
        for point, val in temps.items():
            if val > max_temp: max_temp = val
            
            if val > 95.0:
                issues.append(f"CRITICAL: {point} Overheat (>95°C) - Stop Immediately")
            elif val > self.temp_limit_warn:
                issues.append(f"WARNING: {point} High Temp (>{self.temp_limit_warn}°C) - Check Lubrication/Cooling")
                
        status = "NORMAL"
        if any("WARNING" in x for x in issues): status = "WARNING"
        if any("CRITICAL" in x for x in issues): status = "CRITICAL"
        
        return status, issues, max_temp
