class VisualInspector:
    """
    Menangani standar:
    1. ISO 4406 (Hydraulic Fluid/Oil Cleanliness)
    2. ISO 12922 (Lubricants Specs)
    3. ISO 45001 / OSHA 1910 (Safety)
    """
    
    def analyze_oil_condition(self, visual_check):
        """
        Visual check mapping ke kemungkinan kode ISO 4406
        """
        if visual_check == "Clear & Bright":
            return "OK", "ISO 4406 Estimasi: -/15/12 (Clean)"
        elif visual_check == "Cloudy/Hazy":
            return "WARNING", "ISO 4406 Estimasi: -/19/16 (Water Contamination?)"
        elif visual_check == "Dark/Black":
            return "CRITICAL", "ISO 12922: Oxidized / Thermal Degradation"
        elif visual_check == "Milky":
            return "CRITICAL", "ISO 4406: High Water Content (Emulsion)"
        return "UNKNOWN", "-"

    def analyze_safety(self, checks):
        """
        checks: Dict of boolean
        Standar: OSHA 1910 / ISO 45001
        """
        violations = []
        if not checks['guard_installed']:
            violations.append("OSHA 1910.219: Rotating parts guard missing!")
        if not checks['grounding_ok']:
            violations.append("OSHA 1910.304: Grounding path discontinuous!")
        if checks['leakage_visible']:
            violations.append("ISO 14001: Environmental Leakage (Oil/Fluid)")
            
        return violations
