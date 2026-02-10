import pandas as pd
import numpy as np

class ElectricalInspector:
    """
    MODULE INSPEKSI ELEKTRIKAL
    Standards:
    - IEC 60034-1 (Rating & Performance)
    - NEMA MG-1 (Voltage Unbalance Limits)
    """
    
    def __init__(self):
        # Limit Standar IEC 60034-1 (Sesuai TKI)
        self.limit_v_unbalance_warn = 2.0 # % (Zone A Limit - IEC)
        self.limit_v_unbalance_trip = 5.0 # % (Zone B Limit - Danger)
        
        self.limit_i_unbalance_warn = 10.0 
        self.voltage_tolerance = 0.05 # +/- 5% (Zone A Voltage Variation)

    def _calc_unbalance(self, values):
        """
        Rumus NEMA: (Max Deviation from Avg) / Avg * 100
        """
        avg = sum(values) / 3
        if avg == 0: return 0.0, 0.0
        
        max_dev = max([abs(v - avg) for v in values])
        unbalance = (max_dev / avg) * 100
        return unbalance, avg

    def analyze_health(self, vol_inputs, amp_inputs, rated_vol, rated_fla):
        """
        Input: 
        - vol_inputs: list [V_rs, V_st, V_tr]
        - amp_inputs: list [I_r, I_s, I_t]
        - rated_vol: dari Database Aset (misal 380V)
        - rated_fla: dari Database Aset (misal 45A)
        """
        
        # 1. HITUNG UNBALANCE
        v_unbal, v_avg = self._calc_unbalance(vol_inputs)
        i_unbal, i_avg = self._calc_unbalance(amp_inputs)
        
        # 2. DIAGNOSA LOGIC
        faults = []
        status = "NORMAL"

        # A. Cek Voltage Unbalance (Musuh Utama Motor)
        if v_unbal > self.limit_v_unbalance_trip:
            faults.append({
                "name": "CRITICAL VOLTAGE UNBALANCE",
                "val": f"{v_unbal:.2f}%",
                "desc": "Ketidakseimbangan tegangan sangat tinggi (>5%). Motor cepat panas/terbakar.",
                "action": "🔴 STOP MOTOR. Cek Trafo & Koneksi Panel (Loose Connection)."
            })
            status = "CRITICAL"
        elif v_unbal > self.limit_v_unbalance_warn:
            faults.append({
                "name": "VOLTAGE UNBALANCE",
                "val": f"{v_unbal:.2f}%",
                "desc": "Tegangan tidak seimbang (>1%). Perlu Derating beban.",
                "action": "⚠️ Cek pembagian beban 1-fasa di panel. Cek kabel supply."
            })
            if status == "NORMAL": status = "WARNING"

        # B. Cek Current Unbalance
        if i_unbal > self.limit_i_unbalance_warn:
            # Pastikan bukan karena motor mati (Arus kecil)
            if i_avg > 1.0: 
                faults.append({
                    "name": "HIGH CURRENT UNBALANCE",
                    "val": f"{i_unbal:.2f}%",
                    "desc": "Arus antar fasa timpang (>10%).",
                    "action": "⚡ Cek Tahanan Isolasi (Megger) & Resistansi Lilitan. Cek Kontak Breaker."
                })
                if status == "NORMAL": status = "WARNING"

        # C. Cek Overload (Overcurrent)
        # IEC 60034: Motor tidak boleh beroperasi terus menerus di atas Rated Current
        max_amp = max(amp_inputs)
        load_pct = (max_amp / rated_fla) * 100
        
        if max_amp > (rated_fla * 1.05): # Toleransi 5% bacaan alat
            faults.append({
                "name": "OVERLOAD / OVERCURRENT",
                "val": f"{load_pct:.1f}% FLA",
                "desc": f"Arus aktual ({max_amp:.1f}A) melebihi Nameplate ({rated_fla}A).",
                "action": "📉 Kurangi beban pompa (Throttling). Cek masalah mekanis (Bearing/Alignment)."
            })
            status = "CRITICAL"

        # D. Cek Voltage Deviation (Under/Over Voltage)
        # IEC Zone A: +/- 5% dari Rated
        v_min_limit = rated_vol * (1 - self.voltage_tolerance)
        v_max_limit = rated_vol * (1 + self.voltage_tolerance)
        
        if v_avg < v_min_limit:
            faults.append({
                "name": "UNDER VOLTAGE",
                "val": f"{v_avg:.1f} V",
                "desc": f"Tegangan supply terlalu rendah (<{v_min_limit:.0f}V). Arus akan naik.",
                "action": "🔌 Naikkan Tap Trafo. Cek drop tegangan kabel."
            })
            if status == "NORMAL": status = "WARNING"
        elif v_avg > v_max_limit:
            faults.append({
                "name": "OVER VOLTAGE",
                "val": f"{v_avg:.1f} V",
                "desc": f"Tegangan supply terlalu tinggi (>{v_max_limit:.0f}V). Core loss meningkat.",
                "action": "🔌 Turunkan Tap Trafo."
            })
            if status == "NORMAL": status = "WARNING"

        # E. Single Phasing (Salah satu arus 0)
        if (min(amp_inputs) < 1.0) and (max(amp_inputs) > 5.0):
             faults.append({
                "name": "SINGLE PHASING",
                "val": "0 Amp",
                "desc": "Hilang satu fasa! Motor mendengung dan akan terbakar hitungan menit.",
                "action": "🔴 STOP EMERGENCY. Cek Sekering/Kabel Putus."
            })
             status = "CRITICAL"

        # 3. DATA REPORT
        report_data = {
            "Parameter": ["Voltage R-S", "Voltage S-T", "Voltage T-R", "Avg Voltage", "Unbalance V", 
                          "Current R", "Current S", "Current T", "Avg Current", "Unbalance I", "Load %"],
            "Value": [f"{vol_inputs[0]:.1f} V", f"{vol_inputs[1]:.1f} V", f"{vol_inputs[2]:.1f} V", f"{v_avg:.1f} V", f"{v_unbal:.2f} %",
                      f"{amp_inputs[0]:.1f} A", f"{amp_inputs[1]:.1f} A", f"{amp_inputs[2]:.1f} A", f"{i_avg:.1f} A", f"{i_unbal:.2f} %", f"{load_pct:.1f} %"],
            "Limit": [f"±5% ({rated_vol}V)", f"±5% ({rated_vol}V)", f"±5% ({rated_vol}V)", "-", "< 1.0 %",
                      f"Max {rated_fla}A", f"Max {rated_fla}A", f"Max {rated_fla}A", "-", "< 10 %", "100 %"]
        }
        df = pd.DataFrame(report_data)

        return df, faults, status, load_pct
