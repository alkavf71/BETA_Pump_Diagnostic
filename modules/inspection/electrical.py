class ElectricalInspector:
    """
    Menangani standar:
    1. IEC 60034-1 (Rotating Electrical Machines)
    """
    
    def analyze_health(self, volts, amps, fla_rating):
        """
        volts: list [v1, v2, v3]
        amps: list [i1, i2, i3]
        fla_rating: Ampere Nameplate
        """
        # 1. Voltage Unbalance (IEC 60034-1: Max 1% ideal, 3% limit lapangan)
        avg_volt = sum(volts) / 3
        max_dev_v = max([abs(v - avg_volt) for v in volts])
        v_unbalance = (max_dev_v / avg_volt) * 100
        
        # 2. Current Unbalance (IEC 60034: Akibat V-Unbalance)
        avg_curr = sum(amps) / 3
        if avg_curr == 0: avg_curr = 1 # Prevent div by zero
        max_dev_i = max([abs(i - avg_curr) for i in amps])
        i_unbalance = (max_dev_i / avg_curr) * 100
        
        diagnoses = []
        
        # Logic IEC 60034 Derating
        if v_unbalance > 1.0:
            diagnoses.append(f"IEC 60034: Volt Unbalance {v_unbalance:.2f}% (Derating Required)")
        
        # Logic Overload
        max_amp = max(amps)
        if max_amp > fla_rating:
             diagnoses.append(f"IEC 60034: Overload ({max_amp}A > {fla_rating}A)")
             
        status = "FAULT" if diagnoses else "OK"
        
        return {
            "v_unbalance": v_unbalance,
            "i_unbalance": i_unbalance,
            "status": status,
            "notes": diagnoses
        }
