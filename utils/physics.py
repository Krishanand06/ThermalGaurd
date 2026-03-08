# WBGT calculation and risk classification logic
import math


def calculate_wet_bulb(temp_c: float, rh: float) -> float:
    """Calculates Wet Bulb Temperature using Stull's  formula."""
    tw = (
        temp_c * math.atan(0.151977 * math.sqrt(rh + 8.313659))
        + math.atan(temp_c + rh)
        - math.atan(rh - 1.676331)
        + 0.00391838 * (rh ** 1.5) * math.atan(0.023101 * rh)
        - 4.686035
    )
    return round(tw, 1)


def apply_clothing_adjustment(tw: float, ppe_on: bool) -> float:
    """+5°C penalty if the worker is wearing heavy PPE."""
    return tw + 5.0 if ppe_on else tw


def get_activity_modifier(intensity: str) -> dict:
    """ adjustments based on work rate."""
    modifiers = {
        "Light": {
            "label": "Light (≤180 W)",
            "examples": "Sitting, standing, inspecting, light assembly",
            "threshold_offset": 0.0,   # baseline
            "metabolic_w": 180,
        },
        "Moderate": {
            "label": "Moderate (180-300 W)",
            "examples": "Walking, lifting, pushing, carrying",
            "threshold_offset": -2.0,  # lower safe threshold by 2°C
            "metabolic_w": 300,
        },
        "Heavy": {
            "label": "Heavy (300-415 W)",
            "examples": "Shoveling, climbing, manual excavation",
            "threshold_offset": -4.0,  # lower safe threshold by 4°C
            "metabolic_w": 415,
        },
    }
    return modifiers.get(intensity, modifiers["Moderate"])


def categorize_risk(adjusted_tw: float, acclimatized: bool, intensity: str = "Moderate") -> dict:
    """Categorizes heat risk based on adjusted WBGT and acclimatization."""
    activity_mod = get_activity_modifier(intensity)
    offset = activity_mod["threshold_offset"]

    if acclimatized:
        thresholds = [25 + offset, 28 + offset, 31 + offset, 34 + offset]
    else:
        thresholds = [22 + offset, 25 + offset, 28 + offset, 31 + offset]

    if adjusted_tw < thresholds[0]:
        level = "Safe"
        color = "#00C853"
        work_rest = "Normal operations - no mandatory rest required."
        hydration = "Encourage water intake: 500 mL per hour."
        actions = []
    elif adjusted_tw < thresholds[1]:
        level = "Caution"
        color = "#FFD600"
        work_rest = "50 minutes work / 10 minutes rest per hour."
        hydration = "Mandatory: 750 mL of water per hour per worker."
        actions = ["Monitor workers for signs of heat stress."]
    elif adjusted_tw < thresholds[2]:
        level = "Warning"
        color = "#FF6D00"
        work_rest = "45 minutes work / 15 minutes rest per hour."
        hydration = "Mandatory: 1 Liter of water per hour per worker."
        actions = [
            "Implement buddy system.",
            "Provide shaded rest areas with active cooling.",
        ]
    elif adjusted_tw < thresholds[3]:
        level = "Danger"
        color = "#FF1744"
        work_rest = "30 minutes work / 30 minutes rest per hour."
        hydration = "Mandatory: 1 Liter of water per hour per worker + electrolytes."
        actions = [
            "IMPLEMENT BUDDY SYSTEM IMMEDIATELY.",
            "On-site medical personnel required.",
            "Mandatory acclimatization protocol for new workers.",
        ]
    else:
        level = "Extreme Danger"
        color = "#D50000"
        work_rest = "HALT all non-essential manual labor."
        hydration = "Mandatory: 1.5 Liters of water per hour + electrolytes."
        actions = [
            "STOP ALL NON-ESSENTIAL OUTDOOR WORK.",
            "Emergency cooling stations must be active.",
            "Medical team on standby.",
            "Only mission-critical operations with full PPE and constant monitoring.",
        ]

    return {
        "level": level,
        "color": color,
        "work_rest": work_rest,
        "hydration": hydration,
        "actions": actions,
        "thresholds": thresholds,
    }
