"""
ai/efficiency_score.py
------------------------
Computes a 0-100 "Energy Efficiency Score" for a machine's daily
performance, combining:

    - Specific Energy Consumption (kWh per ton of ore processed) - lower is better
    - Utilization (working hours vs a 24h day) - higher is better, up to a point
    - Idle penalty (implied idle time = 24 - working_hours, when status is Active)

The formula is intentionally transparent (rule-based weighted score) so it
can be explained to plant engineers rather than being an opaque ML output.
"""


def calculate_efficiency_score(energy_kwh, working_hours, ore_processed_tons,
                                rated_power_kw=100.0):
    """
    Calculate an efficiency score between 0 and 100.

    Formula components (weights sum to 100):
        1. Specific Energy Index (50 pts): how much energy per ton of ore,
           benchmarked against an ideal specific consumption.
        2. Utilization Index (30 pts): working_hours / 24, rewarding higher
           utilization of the asset.
        3. Idle Penalty (20 pts): penalizes excessive idle time relative to
           working hours, since idling machinery wastes energy.

    Returns a float rounded to 1 decimal place, clamped to [0, 100].
    """
    if ore_processed_tons <= 0:
        ore_processed_tons = 0.01  # avoid division by zero for idle machines

    # 1) Specific energy consumption: kWh per ton processed
    specific_energy = energy_kwh / ore_processed_tons
    # Ideal benchmark specific energy per ton (illustrative industry figure)
    ideal_specific_energy = (rated_power_kw * 0.35)
    specific_energy_index = max(0, 1 - (specific_energy - ideal_specific_energy) /
                                 max(ideal_specific_energy, 1))
    specific_energy_index = min(1, max(0, specific_energy_index)) * 50

    # 2) Utilization index: reward working hours closer to a full productive shift (~20h)
    utilization_ratio = min(working_hours / 20.0, 1.0)
    utilization_index = utilization_ratio * 30

    # 3) Idle penalty: the more idle hours (24 - working_hours), the bigger the deduction
    idle_hours = max(0, 24 - working_hours)
    idle_penalty_ratio = min(idle_hours / 24.0, 1.0)
    idle_index = (1 - idle_penalty_ratio) * 20

    score = specific_energy_index + utilization_index + idle_index
    return round(min(100, max(0, score)), 1)


def score_to_status(score):
    """Map a numeric efficiency score to a color-coded status label."""
    if score >= 75:
        return {"label": "Excellent", "color": "green"}
    elif score >= 50:
        return {"label": "Average", "color": "yellow"}
    else:
        return {"label": "Poor", "color": "red"}
