import pandas as pd
import numpy as np

class ElectricalInspector:
    """
    MODULE INSPEKSI ELEKTRIKAL (Logic Layer)
    Standard: IEC 60034-1 & NEMA MG-1
    """
    
    def __init__(self):
        # --- THRESHOLDS ---
        self.limit_v_unbal_warn = 2.0 
        self.limit_v_unbal_trip = 5.0
        self.limit_i_unbal_warn = 10.0 # Pastikan nama variabel konsisten 'unbal'
        self.volt_tolerance = 0.05 
        self.limit_ground_fault = 0.5

    def _calc_nema_unbalance(self, values):
        avg = np.mean(values)
        if avg == 0: return 0.0, 0.0
        max_dev = max([abs(v - avg) for v in values])
        unbalance = (max_dev / avg) * 100
        return unbalance, avg

    def analyze_health(self, vol_inputs, amp_inputs, rated_vol, rated_fla):
        faults = []
        status = "NORMAL"

        # 1. Calculation
        v_unbal, v_avg = self._calc_nema_unbalance(vol_inputs)
        i_unbal, i_avg = self._calc_nema_unbalance(amp_inputs)
        max_amp = max(amp_inputs)
        load_pct = (max_amp / rated_fla) * 100 if rated_fla > 0 else 0.0

        # 2. Logic Diagnosa
        if v_unbal > self.limit_v_unbal_trip:
            faults.append({"name": "CRITICAL VOLTAGE UNBALANCE", "val": f"{v_unbal:.1f}%", "desc": "Tegangan sangat tidak seimbang.", "action": "STOP & Cek Trafo/Panel."})
            status = "CRITICAL"
        elif v_unbal > self.limit_v_unbal_warn:
            faults.append({"name": "VOLTAGE UNBALANCE", "val": f"{v_unbal:.1f}%", "desc": "Tegangan tidak seimbang.", "action": "Cek distribusi beban."})
            status = "WARNING"

        if i_unbal > self.limit_i_unbal_warn and i_avg > 1.0:
            faults.append({"name": "HIGH CURRENT UNBALANCE", "val": f"{i_unbal:.1f}%", "desc": "Arus pincang. Indikasi koneksi kendor.", "action": "Retighten terminal box."})
            status = "WARNING" if status != "CRITICAL" else "CRITICAL"

        if max_amp > (rated_fla * 1.05):
            faults.append({"name": "OVERLOAD", "val": f"{max_amp:.1f}A", "desc": "Arus melebihi FLA.", "action": "Cek beban pompa."})
            status = "CRITICAL"

        # 3. Report Data
        report_data = {
            "Parameter": ["Avg Voltage", "V-Unbalance", "Avg Current", "I-Unbalance", "Load %"],
            "Nilai": [f"{v_avg:.1f}V", f"{v_unbal:.1f}%", f"{i_avg:.1f}A", f"{i_unbal:.1f}%", f"{load_pct:.1f}%"],
            "Status": [status, "Max 2%", "-", "Max 10%", "Max 100%"]
        }
        return pd.DataFrame(report_data), faults, status, load_pct
