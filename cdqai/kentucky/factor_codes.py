# CDQAI file version: 2.5.1
"""Kentucky contributing-factor codes used by the dashboard review filters."""

FACTOR_CATALOGS = {
    "human": {
        "label": "Human Factors",
        "codes": {
            "01": "Alcohol Involvement",
            "02": "Cell Phone",
            "03": "Disregard Traffic Control",
            "04": "Distraction",
            "05": "Drug Involvement",
            "06": "Emotional",
            "07": "Exceeded Stated Speed Limit",
            "08": "Failed to Yield Right of Way",
            "09": "Fatigue",
            "10": "Fell Asleep",
            "11": "Following Too Close",
            "12": "Improper Backing",
            "13": "Improper Passing",
            "14": "Inattention",
            "15": "Lost Consciousness/Fainted",
            "16": "Medication",
            "17": "Misjudge Clearance",
            "18": "Not Under Proper Control",
            "19": "Overcorrecting/Oversteering",
            "20": "Physical Disability",
            "21": "Sick",
            "22": "Too Fast for Conditions",
            "23": "Turning Improperly",
            "24": "Weaving in Traffic",
            "97": "Other",
            "99": "None Detected",
        },
        "field": "HumanFactorCode",
    },
    "environmental": {
        "label": "Environmental Factors",
        "codes": {
            "01": "Animals Action",
            "02": "Construction Work Zone",
            "03": "Debris in Roadway",
            "04": "Fixed Object",
            "05": "Glare",
            "06": "Holes/Deep Ruts/Bumps",
            "07": "Improperly Parked Vehicle",
            "08": "Improper/Non-Working Traffic Controls",
            "09": "Maintenance/Utility Work Zone",
            "10": "Shoulders Defective/Drop-off",
            "11": "Slippery Surface",
            "12": "View Obstructed/Limited",
            "13": "Water Pooling",
            "97": "Other",
            "99": "None Detected",
        },
        "field": "EnvironmentalFactorCode",
    },
    "vehicle": {
        "label": "Vehicle Factors",
        "codes": {
            "01": "Brakes Defective",
            "02": "Headlights Defective",
            "03": "Load Securement",
            "04": "Other Lighting Defective",
            "05": "Oversized Load on Vehicle",
            "06": "Overweight",
            "07": "Steering Failure",
            "08": "Tire Failure",
            "09": "Tow Hitch Defective/Sep. of Units",
            "97": "Other",
            "99": "None Detected",
        },
        "field": "VehicularFactorCode",
    },
}


def normalize_factor_code(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text.zfill(2) if text.isdigit() else text.upper()


def factor_description(factor_type: str, code: object) -> str:
    normalized = normalize_factor_code(code)
    return FACTOR_CATALOGS[factor_type]["codes"].get(normalized, "Unmapped code")
