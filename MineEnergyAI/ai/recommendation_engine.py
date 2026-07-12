"""
ai/recommendation_engine.py
-----------------------------
Rule-based intelligent recommendation engine.

Given a machine type and an anomaly severity/deviation, this module
generates a human-readable diagnosis containing:
    - Possible reasons for the abnormal energy consumption
    - Actionable recommendations for the maintenance/operations team

This mirrors how real industrial condition-monitoring software presents
"expert system" style advice without requiring a trained ML classifier.
"""

# Knowledge base of possible causes per machine type
POSSIBLE_REASONS = {
    "Crusher": [
        "Motor overload due to oversized feed material",
        "Worn or damaged crushing bearings",
        "Improper feed size distribution",
        "Maintenance overdue on crusher liners",
    ],
    "Conveyor": [
        "Belt misalignment increasing friction",
        "Overloading beyond rated belt capacity",
        "Idler roller bearing wear",
        "Excessive belt tension",
    ],
    "Excavator": [
        "Hydraulic system pressure loss",
        "Increased digging resistance from harder ore face",
        "Engine running below optimal load efficiency",
        "Track/undercarriage wear increasing drag",
    ],
    "Pump": [
        "Impeller wear reducing pumping efficiency",
        "Partial pipeline blockage increasing head pressure",
        "Cavitation due to suction line issues",
        "Seal or bearing degradation",
    ],
    "Drill": [
        "Drill bit wear increasing torque demand",
        "Rock hardness variation at drill site",
        "Hydraulic fluid pressure drop",
        "Misalignment of drill mast",
    ],
    "Processing Plant": [
        "Sub-optimal ore blend increasing grinding load",
        "Equipment interlock inefficiencies",
        "Ventilation/cooling systems running continuously",
        "Scheduled maintenance overdue across plant line",
    ],
}

RECOMMENDATIONS = {
    "Crusher": [
        "Inspect motor windings and load current",
        "Schedule bearing maintenance immediately",
        "Reduce feed rate to recommended capacity",
        "Check and replenish lubrication system",
    ],
    "Conveyor": [
        "Realign belt and inspect idlers",
        "Reduce load to rated belt capacity",
        "Lubricate and inspect roller bearings",
        "Adjust belt tension to OEM specification",
    ],
    "Excavator": [
        "Inspect hydraulic pump and hoses for leaks",
        "Review dig-site material hardness with geology team",
        "Service engine air/fuel intake system",
        "Inspect undercarriage and track tension",
    ],
    "Pump": [
        "Inspect and replace worn impeller",
        "Clear pipeline blockages and inspect valves",
        "Check suction line for air ingress",
        "Replace worn seals/bearings",
    ],
    "Drill": [
        "Replace worn drill bit",
        "Adjust drilling parameters for rock hardness",
        "Inspect hydraulic system pressure",
        "Re-align drill mast",
    ],
    "Processing Plant": [
        "Review ore blend ratio with plant metallurgist",
        "Audit equipment interlocks and control logic",
        "Optimize ventilation/cooling run schedule",
        "Trigger overdue preventive maintenance checklist",
    ],
}


def generate_recommendation(machine_name, machine_type, percent_deviation, severity):
    """
    Build a full AI insight dictionary for a given anomalous machine.

    Returns:
        {
            "headline": str,
            "severity": str,
            "reasons": [str, ...],
            "recommendations": [str, ...]
        }
    """
    reasons = POSSIBLE_REASONS.get(machine_type, POSSIBLE_REASONS["Processing Plant"])
    actions = RECOMMENDATIONS.get(machine_type, RECOMMENDATIONS["Processing Plant"])

    direction = "more" if percent_deviation >= 0 else "less"
    headline = (
        f"{machine_name} consumed {abs(percent_deviation):.1f}% {direction} energy "
        f"than its historical average."
    )

    return {
        "headline": headline,
        "severity": severity,
        "reasons": reasons,
        "recommendations": actions,
    }
