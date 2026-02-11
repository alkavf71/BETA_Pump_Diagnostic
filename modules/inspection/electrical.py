import pandas as pd
import numpy as np

class ElectricalInspector:
    """
    MODULE INSPEKSI ELEKTRIKAL (Logic Layer)
    
    Standards Reference:
    1. IEC 60034-1: Rotating Electrical Machines - Rating and Performance.
       - Batas toleransi tegangan supply: +/- 5% (Zone A).
       - Batas overload arus (Service Factor).
    2. NEMA MG-1: Motors and Generators.
       - Definisi Voltage Unbalance & Derating Factor.
       - Rule of thumb: 1% V-Unbalance = 6-10% I-Unbalance.
    3. IEEE / Fluke Guidelines:
       - Batas aman Voltage Unbalance (2%).
       - Batas aman Current Unbalance (10%).
    """
    
    def __init__(self):
        # --- THRESHOLDS (BATAS AMAN) ---
        
        # 1. Voltage Unbalance (IEC 60034-1)
        # Zone A (Aman): 0 - 2%
        # Zone B (Warning/Derating): > 2%
        # Critical: > 5% (Resiko lilitan terbakar tinggi)
        self.limit_v_unbal_warn = 2.0 
        self.limit_v_unbal_trip = 5.0
        
        # 2. Current Unbalance (NEMA/IEEE)
        # 10% adalah indikator umum kesehatan motor/koneksi
        self.limit_i_unbal_warn = 10.0
        
        # 3. Voltage Deviation (IEC 60034-1 Zone A)
        # Toleransi tegangan masuk +/- 5% dari Nameplate
        self.volt_tolerance = 0.05 

        # 4. Ground Fault (Safety)
        # > 0.5 Ampere bocor ke tanah dianggap bahaya
        self.limit_ground_fault = 0.5

    def _calc_nema_unbalance(self, values):
        """
        Menghitung % Unbalance menggunakan metode NEMA MG-1.
        Rumus: (Max Deviation from Average / Average) * 100
        """
        avg = np.mean(values)
        if avg == 0: return 0.0, 0.0
        
        max_dev = max([abs(v - avg) for v in values])
        unbalance = (max_dev / avg) * 100
        return unbalance, avg

    def analyze_health(self, vol_inputs, amp_inputs, rated_vol, rated_fla):
        """
        Fungsi Utama Diagnosa Kesehatan Elektrikal.
        
        Args:
            vol_inputs (list): [V_rs, V_st, V_tr]
            amp_inputs (list): [I_r, I_s, I_t]
            rated_vol (float): Tegangan Nameplate (misal 380V)
            rated_fla (float): Full Load Ampere Nameplate
            
        Returns:
            df_report (DataFrame): Tabel data olahan untuk UI
            faults (list): Daftar diagnosa kerusakan
            status (str): Status Global (NORMAL/WARNING/CRITICAL)
            load_pct (float): Persentase pembebanan motor
        """
        
        faults = []
        status = "NORMAL"

        # --- 1. PROSES DATA (CALCULATION) ---
        v_unbal, v_avg = self._calc_nema_unbalance(vol_inputs)
        i_unbal, i_avg = self._calc_nema_unbalance(amp_inputs)
        max_amp = max(amp_inputs)
        
        # Hitung % Load (Pembebanan)
        if rated_fla > 0:
            load_pct = (max_amp / rated_fla) * 100
        else:
            load_pct = 0.0

        # --- 2. LOGIC DIAGNOSA (RULE BASED) ---

        # A. VOLTAGE UNBALANCE (IEC 60034 / NEMA)
        # Ketimpangan tegangan adalah pembunuh utama motor (Overheat).
        if v_unbal > self.limit_v_unbal_trip:
            faults.append({
                "name": "CRITICAL VOLTAGE UNBALANCE",
                "val": f"{v_unbal:.2f}%",
                "desc": "Ketimpangan tegangan > 5%. Suhu lilitan akan naik drastis.",
                "action": "🔴 STOP MOTOR SEGERA. Periksa Sumber Listrik (Trafo/Genset) & Sambungan Panel."
            })
            status = "CRITICAL"
        elif v_unbal > self.limit_v_unbal_warn:
            faults.append({
                "name": "VOLTAGE UNBALANCE (Zone B)",
                "val": f"{v_unbal:.2f}%",
                "desc": "Ketimpangan tegangan > 2%. Masuk area Derating (IEC 60034).",
                "action": "⚠️ Kurangi beban motor (Derating). Cek pembagian beban 1-fasa di panel distribusi."
            })
            if status != "CRITICAL": status = "WARNING"

        # B. CURRENT UNBALANCE (Kesehatan Lilitan/Koneksi)
        # Jika tegangan seimbang tapi arus timpang -> Masalah di Motor/Kabel.
        if i_unbal > self.limit_i_unbalance_warn:
            # Pastikan motor tidak dalam kondisi mati/load sangat rendah (false alarm)
            if i_avg > 1.0: 
                faults.append({
                    "name": "HIGH CURRENT UNBALANCE",
                    "val": f"{i_unbal:.2f}%",
                    "desc": "Arus antar fasa tidak seimbang (>10%) padahal tegangan relatif stabil.",
                    "action": "⚡ Cek 'Loose Connection' (Kabel kendor) di terminal box. Lakukan Megger Test (Indikasi Short Turn)."
                })
                if status != "CRITICAL": status = "WARNING"

        # C. OVERLOAD (IEC 60034 Rating)
        # Cek apakah arus melebihi rating nameplate
        # Toleransi 5% untuk fluktuasi sesaat
        if max_amp > (rated_fla * 1.05):
            faults.append({
                "name": "OVERLOAD (OVERCURRENT)",
                "val": f"{max_amp:.1f} A",
                "desc": f"Arus aktual melebihi Nameplate ({rated_fla} A). Panas berlebih pada lilitan.",
                "action": "📉 Kurangi beban pompa (Cek BJ fluida / Valve Discharge). Cek Bearing macet."
            })
            status = "CRITICAL"

        # D. VOLTAGE DEVIATION (Under/Over Voltage)
        # IEC 60034 Zone A: Tegangan harus dalam range +/- 5%
        v_min = rated_vol * (1 - self.volt_tolerance)
        v_max = rated_vol * (1 + self.volt_tolerance)
        
        if v_avg < v_min:
            faults.append({
                "name": "UNDER VOLTAGE",
                "val": f"{v_avg:.1f} V",
                "desc": f"Tegangan supply drop di bawah batas {v_min:.0f}V (-5%). Arus akan naik untuk kompensasi daya.",
                "action": "🔌 Naikkan Tap Trafo atau cek ukuran kabel supply (Voltage Drop)."
            })
            if status != "CRITICAL": status = "WARNING"
        elif v_avg > v_max:
            faults.append({
                "name": "OVER VOLTAGE",
                "val": f"{v_avg:.1f} V",
                "desc": f"Tegangan supply terlalu tinggi di atas {v_max:.0f}V (+5%). Saturasi inti besi (Core Loss).",
                "action": "🔌 Turunkan Tap Trafo."
            })
            if status != "CRITICAL": status = "WARNING"

        # E. SINGLE PHASING (Kehilangan 1 Fasa)
        # Deteksi ekstrim: Salah satu arus 0 atau sangat kecil dibanding yang lain
        if (min(amp_inputs) < 0.5) and (max(amp_inputs) > 5.0):
             faults.append({
                "name": "SINGLE PHASING",
                "val": "Phase Loss",
                "desc": "Satu fasa hilang! Motor mendengung keras dan cepat panas.",
                "action": "🔴 STOP EMERGENCY. Cek Sekering (Fuse) putus atau Kontaktor rusak."
            })
             status = "CRITICAL"

        # --- 3. SUSUN DATAFRAME LAPORAN ---
        report_data = {
            "Parameter": [
                "Tegangan R-S", "Tegangan S-T", "Tegangan T-R", "Rata-rata Tegangan", "Unbalance Volt",
                "Arus R", "Arus S", "Arus T", "Rata-rata Arus", "Unbalance Arus", "Load %"
            ],
            "Nilai Aktual": [
                f"{vol_inputs[0]:.1f} V", f"{vol_inputs[1]:.1f} V", f"{vol_inputs[2]:.1f} V", f"{v_avg:.1f} V", f"{v_unbal:.2f} %",
                f"{amp_inputs[0]:.1f} A", f"{amp_inputs[1]:.1f} A", f"{amp_inputs[2]:.1f} A", f"{i_avg:.1f} A", f"{i_unbal:.2f} %", f"{load_pct:.1f} %"
            ],
            "Limit / Standar": [
                f"Rated {rated_vol}V", f"Rated {rated_vol}V", f"Rated {rated_vol}V", f"±5% ({v_min:.0f}-{v_max:.0f}V)", "< 2.0 % (IEC)",
                "-", "-", "-", f"Max {rated_fla}A", "< 10 %", "Max 100 %"
            ]
        }
        df = pd.DataFrame(report_data)

        return df, faults, status, load_pct
