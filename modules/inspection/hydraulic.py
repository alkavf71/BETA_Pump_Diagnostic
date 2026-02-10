import pandas as pd

class HydraulicInspector:
    """
    MODULE INSPEKSI HIDROLIK (HYDRAULIC PERFORMANCE) - API 610 LEVEL
    
    Standards:
    - API 610 (Centrifugal Pumps for Petroleum Industries)
    - ISO 9906 (Rotodynamic pumps — Hydraulic performance acceptance tests)
    
    Logic Bertingkat:
    1. EXCELLENT (0% s.d -3%): Sesuai standar terima pabrik (API 610).
    2. GOOD / ACCEPTABLE (-3% s.d -10%): Degradasi wajar operasional.
    3. POOR (< -10%): Degradasi kritis, perlu perbaikan (impeller/wear ring).
    4. RESTRICTED FLOW (> +5%): Indikasi sumbatan atau valve tertutup.
    """

    def __init__(self):
        # Thresholds (Batas Toleransi)
        self.tol_excellent = -3.0  # API 610 Factory Tolerance
        self.tol_acceptable = -10.0 # Common Industry Limit for Maintenance
        self.tol_high_head = 5.0   # Shut-off region danger zone

    def calculate_head(self, p_in_bar, p_out_bar, sg):
        """
        Menghitung Total Dynamic Head (TDH) dalam Meter.
        Rumus: H = (Diff Pressure (Bar) * 10.197) / SG
        """
        if sg <= 0: return 0.0
        
        diff_press = p_out_bar - p_in_bar
        actual_head = (diff_press * 10.197) / sg
        return actual_head

    def analyze_performance(self, p_in, p_out, sg, design_head):
        """
        Melakukan analisa kesehatan hidrolik bertingkat.
        """
        actual_head = self.calculate_head(p_in, p_out, sg)
        
        # Hitung Deviasi (%)
        if design_head > 0:
            deviation = ((actual_head - design_head) / design_head) * 100
        else:
            deviation = 0.0

        # --- LOGIC DIAGNOSA BERTINGKAT ---
        status = "UNKNOWN"
        diag_desc = "-"
        action = "-"
        
        # 1. KASUS HEAD NAIK (HIGH PRESSURE / RESTRICTION)
        if deviation > self.tol_high_head:
            status = "HIGH SYSTEM RESISTANCE"
            diag_desc = f"📈 Head Aktual ({actual_head:.1f}m) lebih tinggi {deviation:.1f}% dari desain. Pompa bekerja di area kiri kurva (Shut-off)."
            action = "🔧 Bahaya Defleksi Poros! Cek bukaan Valve Discharge (Pastikan 100% Open). Cek sumbatan pipa."
            
        # 2. KASUS HEAD TURUN (WEAR / DEGRADATION)
        else:
            if deviation >= self.tol_excellent:
                # Range: 0% s.d -3%
                status = "EXCELLENT (API 610)"
                diag_desc = f"✅ Performa Prima. Deviasi {deviation:.1f}% masih masuk toleransi pabrik (API 610/ISO 9906 Grade 1)."
                action = "✅ Lanjutkan operasi normal."
                
            elif deviation >= self.tol_acceptable:
                # Range: -3% s.d -10%
                status = "GOOD (ACCEPTABLE DEGRADATION)"
                diag_desc = f"⚠️ Performa turun {deviation:.1f}%. Masih batas wajar operasional (Normal Wear)."
                action = "👀 Monitor tren penurunan Head bulan depan."
                
            else:
                # Range: < -10%
                status = "POOR (MAINTENANCE REQUIRED)"
                diag_desc = f"📉 Head drop kritis ({deviation:.1f}%). Efisiensi pompa turun drastis."
                action = "🛠️ Jadwalkan penggantian Impeller atau Wear Ring. Cek internal leakage."

        return {
            "actual_head": actual_head,
            "deviation": deviation,
            "status": status,
            "desc": diag_desc,
            "action": action
        }
