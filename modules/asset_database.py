# modules/asset_database.py (REVISED ISO LOGIC)

class Asset:
    def __init__(self, tag, name, pump_type, power_kw, rpm, mount_type="Rigid"):
        self.tag = tag
        self.name = name
        self.pump_type = pump_type
        self.power_kw = power_kw
        self.rpm = rpm
        self.mount_type = mount_type
        
        # --- AUTO LIMIT ISO 10816-3 ---
        self.vib_limit_warning, self.vib_limit_alarm = self._calculate_iso_limits()

    def _calculate_iso_limits(self):
        """
        Menentukan Limit berdasarkan ISO 10816-3
        Asumsi: P-03 (Rotary) juga mengikuti envelope vibrasi umum mesin rotasi (ISO).
        """
        # LOGIC UNTUK RIGID MOUNTING (Beton)
        if self.mount_type == "Rigid":
            if self.power_kw > 15.0:
                # Group 3 (Pompa Besar/Sedang)
                return 4.50, 7.10
            else:
                # Group 4 (Pompa Kecil <= 15kW) -> LIMIT LEBIH KETAT!
                return 2.80, 4.50
        
        # LOGIC UNTUK FLEXIBLE MOUNTING (Skid Baja)
        else:
            if self.power_kw > 15.0:
                return 7.10, 11.20
            else:
                return 4.50, 7.10

# --- DATA ASET (UPDATED) ---
ASSETS = {
    "P-01 (MFO Transfer)": Asset(
        tag="P-01",
        name="HC 180-56/2/N",
        pump_type="Centrifugal",
        power_kw=45.0,     # > 15kW -> Limit 4.5 / 7.1
        rpm=1483
    ),
    "P-02 (KSB Booster)": Asset(
        tag="P-02",
        name="KSB RPH EM 80-230",
        pump_type="Centrifugal",
        power_kw=18.5,     # > 15kW -> Limit 4.5 / 7.1
        rpm=2950
    ),
    "P-03 (Blackmer)": Asset(
        tag="P-03",
        name="Blackmer FRA (Rotary)",
        pump_type="Rotary", 
        power_kw=30.0,     # > 15kW -> Limit 4.5 / 7.1
        rpm=2956
    ),
    "P-04 (KSB S6)": Asset(
        tag="P-04",
        name="KSB RPH S6 080-230B",
        pump_type="Centrifugal",
        power_kw=15.0,     # <= 15kW -> Limit 2.8 / 4.5 (LEBIH KETAT)
        rpm=2955
    ),
}

def get_asset_list():
    return list(ASSETS.keys())

def get_asset_details(tag_key):
    return ASSETS.get(tag_key)
