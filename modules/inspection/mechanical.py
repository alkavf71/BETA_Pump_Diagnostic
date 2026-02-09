
import pandas as pd

class MechanicalInspector:
    """
    Menangani standar:
    1. ISO 20816 (Vibrasi Mesin)
    2. API 610 / ISO 13709 (Pompa Sentrifugal)
    """
    
    def __init__(self, limit_vib=4.5):
        self.limit_vib = limit_vib
        # ISO 20816: Zone A (New) biasanya < 2.3 mm/s untuk Class II
        self.limit_zone_a = 2.30 

    def analyze_vibration(self, inputs):
        """
        Input: Dictionary data vibrasi (H/V/A untuk DE/NDE)
        Output: DataFrame Laporan & Kesimpulan
        Standar: ISO 20816-3
        """
        # Logic Helper: Hitung Rata-rata (Avr)
        def calc_avr(v1, v2): return (v1 + v2) / 2
        
        # Logic Helper: Tentukan Zone ISO
        def get_zone(val):
            if val < self.limit_zone_a: return "ZONE A (New Condition)"
            elif val < self.limit_vib: return "ZONE B (Unlimited Ops)"
            elif val < 7.1: return "ZONE C (Restricted)"
            else: return "ZONE D (Damage Risk)"

        # Hitung Rata-rata per Axis
        avr_m_h = calc_avr(inputs['m_de_h'], inputs['m_nde_h'])
        avr_m_v = calc_avr(inputs['m_de_v'], inputs['m_nde_v'])
        avr_m_a = calc_avr(inputs['m_de_a'], inputs['m_nde_a'])
        
        avr_p_h = calc_avr(inputs['p_de_h'], inputs['p_nde_h'])
        avr_p_v = calc_avr(inputs['p_de_v'], inputs['p_nde_v'])
        avr_p_a = calc_avr(inputs['p_de_a'], inputs['p_nde_a'])

        # Buat Data Table
        data = [
            ["Driver", "H", inputs['m_de_h'], inputs['m_nde_h'], avr_m_h, self.limit_vib, get_zone(avr_m_h)],
            ["Driver", "V", inputs['m_de_v'], inputs['m_nde_v'], avr_m_v, self.limit_vib, get_zone(avr_m_v)],
            ["Driver", "A", inputs['m_de_a'], inputs['m_nde_a'], avr_m_a, self.limit_vib, get_zone(avr_m_a)],
            ["Driven", "H", inputs['p_de_h'], inputs['p_nde_h'], avr_p_h, self.limit_vib, get_zone(avr_p_h)],
            ["Driven", "V", inputs['p_de_v'], inputs['p_nde_v'], avr_p_v, self.limit_vib, get_zone(avr_p_v)],
            ["Driven", "A", inputs['p_de_a'], inputs['p_nde_a'], avr_p_a, self.limit_vib, get_zone(avr_p_a)],
        ]
        
        df = pd.DataFrame(data, columns=["Unit", "Axis", "DE", "NDE", "Avr", "Limit", "Remark"])
        
        # Diagnosa Penyebab (Heuristic ISO)
        causes = []
        max_val = max(avr_m_h, avr_m_v, avr_m_a, avr_p_h, avr_p_v, avr_p_a)
        
        if max_val >= self.limit_vib:
            # Contoh Logic Sederhana
            if (avr_m_a > self.limit_vib) or (avr_p_a > self.limit_vib):
                causes.append("MISALIGNMENT (Dominan Axial)")
            if (avr_m_h > self.limit_vib) and (avr_m_h > avr_m_v):
                causes.append("UNBALANCE (Dominan Horizontal)")

        status = "NORMAL"
        if any("ZONE C" in x for x in df['Remark']): status = "WARNING"
        if any("ZONE D" in x for x in df['Remark']): status = "CRITICAL"

        return df, status, causes, max_val

    def analyze_pump_hydraulic(self, p_in, p_out, sg, head_design):
        """
        Standar: API 610 / ISO 13709
        """
        diff_press = p_out - p_in
        actual_head = (diff_press * 10.197) / sg
        deviation = ((actual_head - head_design) / head_design) * 100
        
        if deviation < -10.0:
            return actual_head, "DEGRADATION", "API 610: Head Drop > 10% (Internal Wear)"
        elif deviation > 10.0:
            return actual_head, "RESTRICTION", "System Curve: Discharge Blocked/High Head"
        else:
            return actual_head, "NORMAL", "API 610: Within Operation Range"
