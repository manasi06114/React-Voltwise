"""
Medium Task — Multi-Region Grid
Multiple cities, interconnected regions, energy transfer between cities.
Goal: optimise power distribution across regions.
"""

from grid_simulator import Region


def build_regions():
    return [
        Region(
            name="Region-A",
            base_demand=100.0,
            solar_capacity=70.0,
            wind_capacity=20.0,
            battery_capacity=60.0,
            battery_charge=0.5,
            has_backup_generator=True,
            generator_output=40.0,
        ),
        Region(
            name="Region-B",
            base_demand=80.0,
            solar_capacity=30.0,
            wind_capacity=50.0,
            battery_capacity=40.0,
            battery_charge=0.5,
            has_backup_generator=False,
            generator_output=0.0,
        ),
        Region(
            name="Region-C",
            base_demand=60.0,
            solar_capacity=20.0,
            wind_capacity=40.0,
            battery_capacity=30.0,
            battery_charge=0.5,
            has_backup_generator=True,
            generator_output=25.0,
        ),
    ]
