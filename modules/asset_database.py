class Asset:
    def __init__(self, tag, name, pump_type, power_kw, rpm, volt, ampere, iso_group="Group 3", mount_type="Rigid"):
        self.tag = tag
        self.name = name
        self.pump_type = pump_type
        self.power_kw = power_kw
        self.rpm = rpm
        self.volt_rated = volt      # <-- INI YANG TADI HILANG
        self.fla_rated = ampere     # <-- INI JUGA
        self.mount_type = mount_type
        
        # --- AUTO LIMIT VIBRASI (ISO 10816-3 / ISO 20816) ---
        # Logic penentuan limit berdasarkan Power & Mounting
        self.vib_limit_warning, self.vib_limit_alarm = self._calculate_iso_limits(iso_group)

    def _calculate_iso_limits(self, group):
        """
        Menentukan Limit berdasarkan ISO 10816-3
        """
        if self.mount_type == "Rigid":
            if group == "Group 4" or self.power_kw <= 15.0:
                return 2.80, 4.50  # Small Machine
            else:
                return 4.50, 7.10  # Medium/Large Machine
        else:
            # Flexible Mounting
            if group == "Group 4" or self.power_kw <= 15.0:
                return 4.50, 7.10
            else:
                return 7.10, 11.20
        return 4.50, 7.10 # Default

# --- DATA ASET (UPDATED DENGAN VOLT & AMPERE) ---
ASSETS = {
    "P-01 (MFO Transfer)": Asset(
        tag="P-01",
        name="HC 180-56/2/N",
        pump_type="Centrifugal",
        power_kw=45.0,
        rpm=1483,
        volt=380,       # Data Screenshot 1
        ampere=85.0,    # Data Screenshot 1
        iso_group="Group 3"
    ),
    "P-02 (KSB Booster)": Asset(
        tag="P-02",
        name="KSB RPH EM 80-230",
        pump_type="Centrifugal",
        power_kw=18.5,
        rpm=2950,
        volt=380,       # Data Screenshot 2
        ampere=35.5,    # Estimasi (krn tidak ada di foto, biasa ~2x kW)
        iso_group="Group 3"
    ),
    "P-03 (Blackmer)": Asset(
        tag="P-03",
        name="Blackmer FRA (Rotary)",
        pump_type="Rotary",
        power_kw=30.0,
        rpm=2956,
        volt=400,       # Data Screenshot 3 (ABB Motor)
        ampere=54.0,    # Estimasi
        iso_group="Group 3"
    ),
    "P-04 (KSB S6)": Asset(
        tag="P-04",
        name="KSB RPH S6 080-230B",
        pump_type="Centrifugal",
        power_kw=15.0,
        rpm=2955,
        volt=380,       # Data Screenshot 4
        ampere=29.0,    # Estimasi
        iso_group="Group 4" # Limit Lebih Ketat
    ),
}

def get_asset_list():
    return list(ASSETS.keys())

def get_asset_details(tag_key):
    return ASSETS.get(tag_key)
