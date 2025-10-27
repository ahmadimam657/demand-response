#!/usr/bin/env python3
"""
Simple moving-horizon optimization example.

This example demonstrates a moving-horizon demand response optimization
without reserve-market participation. It generates simple multi-day price
and demand patterns, runs the moving-horizon optimizer and reports
spot-market cost savings and basic diagnostics.
"""


import numpy as np
import pandas as pd

from demand_response import moving_horizon


def generate_realistic_data(n_hours: int = 72) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate simple price and demand data for demonstration.

    The produced DataFrames use a DatetimeIndex and contain only the
    columns required by the moving-horizon example: ``price`` and
    ``demand``.
    """

    # Create time index
    dates = pd.date_range("2024-01-01", periods=n_hours, freq="h")

    # Daily price cycle with light noise (ct/kWh)
    hours = np.arange(n_hours)
    daily_pattern = 30 + 25 * np.sin(2 * np.pi * hours / 24 - np.pi / 2)
    noise = np.random.normal(0.0, 5.0, n_hours)
    prices = np.maximum(15.0, daily_pattern + noise)

    # Demand roughly inverse to price with small noise (kWh)
    demand_pattern = 12 + 3 * np.sin(2 * np.pi * hours / 24 + np.pi)
    demand_noise = np.random.normal(0.0, 1.0, n_hours)
    demand = np.maximum(5.0, demand_pattern + demand_noise)

    price_data = pd.DataFrame({"price": prices}, index=dates)
    demand_data = pd.DataFrame({"demand": demand}, index=dates)

    return price_data, demand_data


def main() -> tuple[dict, dict[str, float]]:
    """Run a simple moving-horizon optimization example.

    This example generates 3 days of synthetic price/demand data, runs the
    moving-horizon optimizer and reports spot-market savings and basic
    diagnostics.
    """

    print("*** Moving Horizon Optimization (simple example) ***")
    print("=" * 60)

    # Generate realistic test data
    print(">>> Generating realistic price and demand data...")
    price_data, demand_data = generate_realistic_data(n_hours=72)

    print(f"   Generated {len(price_data)} hours of data")
    print(f"   Price range: {price_data['price'].min():.1f} - {price_data['price'].max():.1f} ct/kWh")
    print(f"   Demand range: {demand_data['demand'].min():.1f} - {demand_data['demand'].max():.1f} kWh")

    # Configure moving horizon optimization
    config = {
        "daily_decision_hour": 6,
        "n_lookahead_hours": 24,
        "virtual_storage": {
            "max_demand_advance": 3,
            "max_demand_delay": 2,
            "max_hourly_purchase": 20.0,
            "max_rate": 10.0,
            "solver": "mip",
        },
    }

    print("\n>>> Optimization Configuration:")
    print(f"   Decision hour: {config['daily_decision_hour']}:00")
    print(f"   Lookahead horizon: {config['n_lookahead_hours']} hours")
    print(f"   Max demand advance: {config['virtual_storage']['max_demand_advance']} hours")
    print(f"   Max demand delay: {config['virtual_storage']['max_demand_delay']} hours")
    print(f"   Max transfer capacity: {config['virtual_storage']['max_hourly_purchase']} kWh/hour")

    # Run moving horizon optimization
    print("\n>>> Running moving horizon optimization...")
    result = moving_horizon(price_data, demand_data, config)

    # Extract results
    optimized_demand = result["results"]["demand"]
    demand_shifts = result["results"]["shift"]

    # Spot market costs
    print("\n>>> Calculating spot-market cost savings...")
    original_spot_cost = (price_data["price"] * demand_data["demand"]).sum()
    optimized_spot_cost = (price_data["price"] * optimized_demand).sum()
    total_savings = original_spot_cost - optimized_spot_cost
    savings_percentage = (total_savings / original_spot_cost) * 100 if original_spot_cost > 0 else 0.0

    # Display simple results
    print("\n>>> Spot Market Results:")
    print(f"   Original spot cost:  {original_spot_cost:.2f} ct")
    print(f"   Optimized spot cost: {optimized_spot_cost:.2f} ct")
    print(f"   Spot savings:        {total_savings:.2f} ct ({savings_percentage:.2f}%)")

    # Energy analysis
    print("\n>>> Energy Analysis:")
    print(f"   Total demand: {demand_data['demand'].sum():.2f} -> {optimized_demand.sum():.2f} kWh")
    print(f"   Total energy shifted: {abs(demand_shifts).sum():.2f} kWh")
    print(f"   Max positive shift: {demand_shifts.max():.2f} kWh")
    print(f"   Max negative shift: {demand_shifts.min():.2f} kWh")

    # Strategy analysis: correlation between price and shift
    price_shift_corr = np.corrcoef(price_data["price"], demand_shifts)[0, 1]
    print("\n>>> Optimization Strategy Analysis:")
    print(f"   Price-shift correlation: {price_shift_corr:.3f}")
    if price_shift_corr < -0.1:
        print("   [OK] Energy shifted away from expensive hours")
    elif price_shift_corr > 0.1:
        print("   [!] Energy shifted towards expensive hours (unexpected)")
    else:
        print("   [~] Weak correlation: mixed strategy")

    print("\n*** Moving horizon optimization completed successfully!")

    return result, {"total_savings": total_savings, "savings_percentage": savings_percentage}


if __name__ == "__main__":
    main()