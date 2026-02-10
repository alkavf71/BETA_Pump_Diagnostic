import pandas as pd

class HydraulicInspector:
    """
    MODULE INSPEKSI HIDROLIK (HYDRAULIC PERFORMANCE)
    Standards:
    - API 610 / ISO 13709 (Centrifugal Pump Performance)
    - Hydraulic Institute Standards (HI 9.6)
    """

    def __init__(self):
        # Toleransi degradasi Head (API 610 biasanya +/- 3% untuk tes, 
        # tapi untuk maintenance lapangan kita pakai 10%)
        self.degradation_limit = -10.0 # % (Head Drop)
        self.high_head_limit = 10.0    # % (System Restriction)

    def calculate_head(self, p_in_bar, p_out_bar, sg):
        """
        Menghitung Total Dynamic Head (TDH) dalam Meter.
        Rumus: H = (Diff Pressure (Bar) * 10.197) / SG
        """
        if sg <= 0: return 0.0 # Cegah error pembagian 0
        
        diff_press = p_out_bar - p_in_bar
        actual_head = (diff_press * 10.197) / sg
        return actual_head

    def analyze_performance(self, p_in, p_out, sg, design_head):
        """
        Input:
        - p_in (Bar): Suction Pressure
        - p_out (Bar): Discharge Pressure
        - sg: Specific Gravity
        - design_head (m): Rated Head dari Nameplate
        """
        
        actual_head = self.calculate_head(p_in, p_out, sg)
        
        # Hitung Deviasi (%)
        if design_head > 0:
            deviation = ((actual_head - design_head) / design_head) * 100
        else:
            deviation = 0.0 # Jika data desain kosong

        # Diagnosa
        status = "NORMAL"
        diag_desc = "Performa pompa sesuai kurva desain."
        action = "✅ Lanjutkan operasi."
        color_code = "green"

        if deviation < self.degradation_limit:
            status = "LOW PERFORMANCE"
            diag_desc = f"📉 Head turun {deviation:.1f}%. Indikasi Impeller Aus (Worn) atau Internal Recirculation (Wear Ring Bocor)."
            action = "⚠️ Cek Clearance Wear Ring saat Overhaul. Cek kondisi Impeller."
            color_code = "red"
            
        elif deviation > self.high_head_limit:
            status = "HIGH SYSTEM RESISTANCE"
            diag_desc = f"📈 Head naik {deviation:.1f}%. Tekanan discharge terlalu tinggi (Flow tertahan)."
            action = "🔧 Cek bukaan Valve Discharge (Throttled?). Cek buntu pada pipa/filter discharge."
            color_code = "orange"

        return {
            "actual_head": actual_head,
            "deviation": deviation,
            "status": status,
            "desc": diag_desc,
            "action": action,
            "color": color_code
        }
