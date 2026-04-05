"""
Easy Task — Single City Grid
One city, solar energy, limited battery storage.
Goal: maintain stable power supply.
"""

from grid_simulator import Region


def build_regions():
    return [
        Region(
            name="City-A",
            base_demand=80.0,
            solar_capacity=60.0,
            wind_capacity=0.0,
            battery_capacity=40.0,
            battery_charge=0.5,
            has_backup_generator=True,
            generator_output=30.0,
        )
    ]
