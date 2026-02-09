# modules/asset_database.py

class Asset:
    def __init__(self, tag, name, pump_type, power_kw, rpm, volt, ampere, mount_type="Rigid"):
        self.tag = tag
        self.name = name
        self.pump_type = pump_type # Centrifugal / Positive Displacement
        self.power_kw = power_kw
        self.rpm = rpm
        self.volt_rated = volt
        self.fla_rated = ampere # Full Load Ampere
        self.mount_type = mount_type # Rigid / Flexible (Penting untuk ISO 10816)
        
        # --- AUTO CALCULATION LIMITS ---
        self.vib_limit_warning = self._get_iso_vib_limit()
        self.vib_limit_alarm = self.vib_limit_warning * 1.6 # Rule of thumb ISO

    def _get_iso_vib_limit(self):
        """
        Menentukan Limit Vibrasi (Velocity mm/s RMS) berdasarkan ISO 10816-3 / 20816
        Group 1: Large Machines > 300 kW
        Group 2: Medium Machines 15 kW < P < 300 kW
        Group 3: Pumps > 15 kW (External Driver)
        Group 4: Pumps (Integrated Driver)
        """
        # Default untuk Pompa Industrial (Group 2/3)
        if self.mount_type == "Rigid":
            # Zone B limit (Acceptable for long term)
            if self.power_kw > 15: return 4.5  # mm/s
            else: return 2.8 # Small machine
        else: # Flexible mounting
            if self.power_kw > 15: return 7.1
            else: return 4.5
        return 4.5 # Default safety

# --- DATABASE POPULATION (DARI SCREENSHOT ANDA) ---
ASSETS = {
    "P-101 (Transfer MFO)": Asset(
        tag="P-101",
        name="HC 180-56/2/N (MFO Pump)",
        pump_type="Centrifugal",
        power_kw=45.0,     # Dari Screenshot 1
        rpm=1483,          # Dari Screenshot 1
        volt=380,          # Asumsi std
        ampere=85.0,       # Dari Screenshot 1
        mount_type="Rigid"
    ),
    "P-102 (Booster KSB)": Asset(
        tag="P-102",
        name="KSB RPH EM 80-230",
        pump_type="Centrifugal", # API 610 Type
        power_kw=18.5,     # Dari Screenshot 2 (Siemens Motor)
        rpm=2950,          # Dari Screenshot 2
        volt=380,
        ampere=35.5,       # Estimasi dari kW (karena tidak ada di foto, nanti bisa diedit)
        mount_type="Rigid"
    ),
    "P-103 (Blackmer)": Asset(
        tag="P-103",
        name="Blackmer FRA (Vane Pump)",
        pump_type="Positive Displacement", # API 676 Type
        power_kw=30.0,     # Dari Screenshot 3 (ABB Motor)
        rpm=2956,          # Dari Screenshot 3
        volt=400,
        ampere=54.0,       # Estimasi
        mount_type="Rigid"
    ),
    "P-104 (KSB S6)": Asset(
        tag="P-104",
        name="KSB RPH S6 080-230B",
        pump_type="Centrifugal",
        power_kw=15.0,     # Dari Screenshot 4 (Siemens Motor)
        rpm=2955,          # Dari Screenshot 4
        volt=380,
        ampere=29.0,       # Estimasi
        mount_type="Rigid"
    ),
}

def get_asset_list():
    return list(ASSETS.keys())

def get_asset_details(tag_key):
    return ASSETS.get(tag_key)
